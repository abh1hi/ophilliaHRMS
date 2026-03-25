# 02 — Infrastructure & Container Failure Scenarios

## Infrastructure Level Failures

---

### Scenario I1: VPS Goes Down Completely

**Trigger:** Hardware failure, hypervisor crash, provider outage, power loss

**Timeline of Events:**
1. `T+0s` — VPS loses power/connectivity
2. `T+0s` — All Docker containers stop instantly (SIGKILL equivalent — no graceful shutdown)
3. `T+0s` — All active HTTP requests fail with connection reset
4. `T+0s` — PostgreSQL performs emergency shutdown (no clean checkpoint)
5. `T+0s` — RabbitMQ queued events in tmpfs are permanently lost
6. `T+0s` — Redis AOF journal may have up to 1 second of unsynced writes
7. `T+?` — VPS provider restores hardware or migrates VM
8. `T+?` — VPS boots, Docker daemon starts
9. `T+?+30s` — Containers with `unless-stopped` begin restarting
10. `T+?+60s` — PostgreSQL runs crash recovery (WAL replay)
11. `T+?+90s` — Services pass health checks, system operational

**System Behavior:**
- Zero availability during outage
- PostgreSQL's WAL ensures committed transactions survive (ACID guarantee)
- Uncommitted transactions are rolled back during recovery
- RabbitMQ starts empty — all pending events permanently lost
- Redis restores from AOF — may lose last ~1s of blacklist entries

**User Impact:**
- All pages show connection errors or timeouts
- Mobile apps / API consumers get no response
- No degraded mode — complete blackout

**Data Safety:**
- Committed DB transactions: SAFE (WAL recovery)
- In-flight DB transactions: LOST (rolled back)
- RabbitMQ events: LOST (tmpfs)
- Redis blacklist: MOSTLY SAFE (AOF, ~1s loss window)

**Best Case:** Provider fixes issue in minutes. System auto-recovers. Only RabbitMQ events lost. No data corruption.

**Worst Case:** Extended outage (hours/days). No off-site backup exists. If disk is damaged, PostgreSQL volume is unrecoverable. Total data loss.

**Detection:** External uptime monitoring (e.g., UptimeRobot, Pingdom) checking `/health` endpoint.

---

### Scenario I2: Network Outage (Partial or Full)

**Trigger:** VPS network interface down, routing issue, DNS failure, firewall misconfiguration

**Timeline of Events:**
1. `T+0s` — External traffic cannot reach VPS port 80
2. `T+0s` — Internal Docker network (bridge) still functional
3. `T+0s` — Services continue processing existing requests normally
4. `T+0s` — New external requests timeout at client side
5. `T+30s` — Docker health checks still pass (internal network works)
6. `T+?` — Network restored, traffic resumes immediately

**System Behavior:**
- Internal service-to-service communication: UNAFFECTED
- RabbitMQ consumers: CONTINUE PROCESSING (internal)
- Scheduled jobs (token purge, audit retention): CONTINUE RUNNING
- PostgreSQL connections: UNAFFECTED
- External access: COMPLETELY BLOCKED

**User Impact:**
- Website/API unreachable from internet
- Users see DNS timeout or connection refused
- No data is at risk — system is operating normally internally

**Data Safety:** No risk. All data operations continue internally.

**Best Case:** Network restored quickly. Zero data impact. Users experience brief unreachability.

**Worst Case:** Extended network partition. If SMTP needs external access, notification emails queue up. No internal damage.

**Detection:** External synthetic monitoring. Internal health checks will NOT detect this.

---

### Scenario I3: Disk Failure or Disk Full

**Trigger:** Physical disk failure, Docker log accumulation, PostgreSQL WAL growth, uncontrolled data growth

**Timeline of Events (Disk Full):**
1. `T+0s` — Disk reaches 100% utilization
2. `T+0s` — PostgreSQL: `PANIC: could not write to WAL` — crashes
3. `T+0s` — All services: DB connection errors cascade
4. `T+0s` — Docker: cannot create new container layers, cannot write logs
5. `T+0s` — Redis AOF: cannot append — may crash or go read-only
6. `T+0s` — Nginx: cannot write access logs — may stop accepting requests
7. `T+1s` — All health checks fail (DB unreachable)
8. `T+30s` — Docker attempts container restarts — may fail (no disk space)

**System Behavior:**
- PostgreSQL enters crash state — refuses all connections
- Services report `degraded` health (DB check fails)
- Container restarts may fail if Docker needs disk space for overlay layers
- System enters a cascading failure loop

**User Impact:**
- All write operations fail immediately
- Read operations may work briefly from connection pool cache
- Login fails (auth needs DB)
- Complete system unavailability within seconds

**Data Safety:**
- Committed data: SAFE (on disk, just full)
- In-flight writes: LOST (PostgreSQL crash recovery rolls them back)
- Risk of data corruption: LOW (PostgreSQL WAL is designed for this)
- RabbitMQ: events lost (tmpfs — not even on disk)

**Best Case:** Admin frees disk space (prune Docker, delete old logs). PostgreSQL recovers via WAL replay. No data loss.

**Worst Case:** Physical disk failure. Volume unreadable. Without off-site backup: total data loss.

**Detection:** Disk usage monitoring with alerts at 80% and 90% thresholds.

**Recovery Steps:**
```bash
# 1. Free space immediately
docker system prune -f                    # Remove stopped containers, unused images
truncate -s 0 /var/lib/docker/containers/*/*-json.log  # Clear container logs

# 2. Check PostgreSQL
docker logs hrms-db --tail 50            # Check for PANIC messages
docker restart hrms-db                    # Restart — WAL recovery runs automatically

# 3. Verify
docker exec hrms-db pg_isready           # Should return "accepting connections"
```

---

### Scenario I4: CPU / RAM Exhaustion

**Trigger:** Traffic spike, slow query cascade, memory leak, bulk import operation

**Timeline of Events (RAM Exhaustion):**
1. `T+0s` — VPS RAM usage hits limit
2. `T+0s` — Linux OOM killer activates
3. `T+0s` — OOM killer targets process with highest memory (likely PostgreSQL or a service)
4. `T+0s` — Targeted container receives SIGKILL (no graceful shutdown)
5. `T+1s` — Docker detects container exit with code 137 (OOMKilled)
6. `T+1s` — Docker `unless-stopped` policy triggers restart
7. `T+30s` — Container health check period begins
8. `T+60s` — Container healthy, service restored

**System Behavior:**
- Docker resource limits (768MB per service) provide partial protection via cgroup limits
- If a service exceeds its limit, Docker OOMKills that specific container
- If the VPS itself runs out, the Linux kernel OOM killer picks globally
- PostgreSQL OOMKill = all services lose DB access simultaneously

**User Impact:**
- If a single service OOMKilled: that module unavailable for ~60s (restart + health check)
- If PostgreSQL OOMKilled: total system failure for ~60-90s (crash recovery)
- Active requests to killed service: connection reset / 502 from gateway

**Data Safety:**
- OOMKilled service: in-flight requests lost, but DB transactions roll back safely
- OOMKilled PostgreSQL: WAL recovery preserves committed data
- No data corruption risk from OOM alone

**Best Case:** Single service OOMKilled, restarts in 30s, brief module outage.

**Worst Case:** PostgreSQL OOMKilled during heavy write load. WAL recovery takes minutes. Users see extended outage.

**Detection:** Container exit code 137 in `docker inspect`. Host `dmesg | grep oom`.

---

## Container Level Failures

---

### Scenario C1: Container Crash (Application Error)

**Trigger:** Unhandled exception, segfault in native library, assertion failure

**Timeline of Events:**
1. `T+0s` — Application process exits with non-zero code
2. `T+0s` — Container enters `Exited` state
3. `T+0s` — Active requests to this container: 502 Bad Gateway from Nginx
4. `T+0s` — Nginx DNS cache (10s TTL): may still route to dead container briefly
5. `T+1s` — Docker `unless-stopped` policy triggers restart
6. `T+5s` — Container starts, runs entrypoint (alembic migrate + uvicorn/gunicorn start)
7. `T+15-30s` — Health check start_period begins
8. `T+45-60s` — Health check passes, container marked `healthy`

**System Behavior:**
- Nginx returns 502/503 for requests to the crashed service
- Other services: UNAFFECTED (microservice isolation)
- Nginx custom error page: `{"detail": "Service temporarily unavailable"}`
- Gateway proxy timeout: 3s connect, 10s read — failed requests return quickly

**User Impact:**
- Module-specific outage (e.g., attendance-service crash = attendance features unavailable)
- Login/auth crash = system-wide impact (all authenticated requests fail)
- Frontend SPA remains loaded — API calls fail with error messages
- Typical downtime: 30-60 seconds

**Data Safety:** No risk. In-flight transactions roll back. DB state consistent.

**Best Case:** Transient error, container restarts cleanly, 30s outage.

**Worst Case:** Persistent bug causes restart loop (see C2).

---

### Scenario C2: Container Restart Loop (CrashLoopBackOff equivalent)

**Trigger:** Configuration error, missing env var, DB migration failure, incompatible dependency

**Timeline of Events:**
1. `T+0s` — Container starts, immediately fails
2. `T+1s` — Docker restarts container
3. `T+2s` — Container starts, immediately fails again
4. `T+3s` — Docker restarts, exponential backoff begins
5. `T+3s → T+∞` — Container cycles: start → crash → restart → crash...

**System Behavior:**
- Docker Compose does NOT have native backoff for `unless-stopped` (unlike Kubernetes CrashLoopBackOff)
- Container restarts repeatedly at Docker daemon's restart rate
- Health check status oscillates between `starting` and `unhealthy`
- High CPU usage from rapid process start/stop

**User Impact:**
- Persistent module unavailability
- Brief windows during restart where container may serve partial requests before crashing
- No auto-healing — requires manual intervention

**Data Safety:** Generally safe, unless the crash is caused by a bad migration that partially executed.

**Detection:** `docker ps` shows frequent restart count. `docker inspect` shows increasing `RestartCount`.

**Recovery:**
```bash
# 1. Stop the restart loop
docker stop hrms-auth              # (or whichever service)

# 2. Check logs
docker logs hrms-auth --tail 100   # Identify root cause

# 3. Fix the issue (env var, config, code)
# 4. Restart
docker start hrms-auth
```

---

### Scenario C3: Container OOMKilled

**Trigger:** Memory leak, large query result, bulk file processing, too many connections

**Timeline of Events:**
1. `T+0s` — Container memory exceeds cgroup limit (768MB for services)
2. `T+0s` — Kernel sends SIGKILL to container's main process (no graceful shutdown possible)
3. `T+0s` — Container exits with code 137
4. `T+0s` — All in-flight requests terminated immediately
5. `T+1s` — Docker restarts container (unless-stopped)
6. `T+30-60s` — Container passes health check

**System Behavior:**
- SIGKILL = no lifespan shutdown hook runs
- No 5-second grace period
- No Redis cleanup, no scheduler shutdown, no RabbitMQ disconnection
- FastAPI lifespan `yield` never returns to shutdown code
- SQLAlchemy connections abandoned (pool_pre_ping will detect on next use)

**User Impact:** Same as C1 but potentially more abrupt. Connections may linger as TIME_WAIT.

**Data Safety:**
- Database: SAFE (uncommitted transactions roll back, connections cleaned by PG)
- Redis: connection orphaned but Redis timeout will clean it
- RabbitMQ: unacked messages requeued (if using manual ack) or lost (if auto-ack)

---

### Scenario C4: Docker Daemon Crash

**Trigger:** Docker bug, kernel update, dockerd segfault, `systemctl restart docker`

**Timeline of Events:**
1. `T+0s` — Docker daemon process dies
2. `T+0s` — All containers lose management (but processes may keep running briefly)
3. `T+1-5s` — Container processes receive SIGTERM from init system cleanup
4. `T+5-10s` — Containers with Gunicorn: graceful shutdown within 15s timeout
5. `T+5-10s` — Containers with raw Uvicorn: immediate termination
6. `T+?` — systemd restarts dockerd (if configured)
7. `T+?+10s` — Docker inventories existing containers
8. `T+?+15s` — `unless-stopped` containers begin restarting
9. `T+?+45-90s` — Health checks pass, system restored

**System Behavior:**
- Brief total outage (all containers stop)
- PostgreSQL: clean shutdown if SIGTERM received before SIGKILL
- Services with Gunicorn: graceful drain within 15s
- Services with raw Uvicorn: immediate stop, in-flight requests lost

**User Impact:** Total system outage for duration of daemon restart (~30-90s).

**Data Safety:**
- PostgreSQL: SAFE (clean shutdown + WAL)
- Redis: SAFE (AOF)
- RabbitMQ: EVENTS LOST (tmpfs cleared on container stop)

---

### Scenario C5: Manual Container Stop/Start

**Trigger:** Administrator runs `docker stop <service>` or `docker-compose stop <service>`

**Timeline of Events:**
1. `T+0s` — Docker sends SIGTERM to container PID 1
2. `T+0-5s` — FastAPI lifespan shutdown begins (5-second grace period)
3. `T+5s` — Gunicorn (if used): begins graceful worker shutdown (15s timeout)
4. `T+10s` — Docker's stop timeout (default 10s): sends SIGKILL if still running
5. `T+10s` — Container enters `Exited` state
6. `T+10s` — If `unless-stopped`: Docker will NOT restart (manual stop respected)

**Graceful Shutdown Behavior by Service:**

| Service | Entrypoint | SIGTERM Handling | Grace Period |
|---------|------------|-----------------|--------------|
| Auth | Gunicorn | Gunicorn catches SIGTERM, drains workers | 15s graceful-timeout |
| Employee | Gunicorn | Gunicorn catches SIGTERM, drains workers | 15s graceful-timeout |
| Attendance | Uvicorn (raw) | Uvicorn catches SIGTERM, stops event loop | ~0s (no configured timeout) |
| Students | Uvicorn (raw) | Uvicorn catches SIGTERM, stops event loop | ~0s |
| Payroll | Uvicorn (raw) | Uvicorn catches SIGTERM, stops event loop | ~0s |
| Leave | Uvicorn (raw) | Uvicorn catches SIGTERM, stops event loop | ~0s |
| Audit | Uvicorn (raw) | Uvicorn catches SIGTERM, stops event loop | ~0s |
| Notification | Uvicorn (raw) | Uvicorn catches SIGTERM, stops event loop | ~0s |

**Key Risk:** 6 of 8 services use raw Uvicorn with no `--timeout-graceful-shutdown` flag. In-flight requests are terminated immediately on SIGTERM.

**User Impact:** Targeted service unavailable. Does not auto-restart (manual stop).

**Data Safety:** Safe for Gunicorn services (drain period). Risky for raw Uvicorn services (in-flight request data may be lost if write was in progress).
