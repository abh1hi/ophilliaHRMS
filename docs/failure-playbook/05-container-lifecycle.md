# 05 — Container Lifecycle & Restart Policies

## Container Lifecycle Events

### What Happens When a Container Stops (Graceful)

```
docker stop <container>
  │
  ├─ T+0s:   Docker sends SIGTERM to PID 1
  │
  ├─ T+0-5s: FastAPI lifespan shutdown begins
  │           ├─ Logs "Shutting down — waiting for in-flight requests…"
  │           ├─ await asyncio.sleep(5)  ← 5-second grace period
  │           ├─ Scheduler shutdown (auth-service only)
  │           ├─ Redis connection closed
  │           └─ RabbitMQ consumer closed (audit, notification)
  │
  ├─ T+5s:   Gunicorn services (auth, employee):
  │           ├─ Gunicorn catches SIGTERM
  │           ├─ Stops accepting new connections
  │           ├─ Waits for workers to finish (graceful-timeout: 15s)
  │           └─ Worker completes current request, then exits
  │
  ├─ T+10s:  Docker default stop timeout (10 seconds)
  │           ├─ If PID 1 still running: Docker sends SIGKILL
  │           └─ Process forcefully terminated
  │
  └─ T+10s:  Container enters "Exited" state
```

**Critical Timing Issue:**
- FastAPI lifespan: 5s grace
- Gunicorn graceful-timeout: 15s
- Docker stop timeout: 10s (default)
- **Problem:** Gunicorn wants 15s but Docker kills at 10s. Workers may be killed mid-request.
- **Fix:** Set `docker stop --time 20 <container>` or add `stop_grace_period: 20s` in docker-compose

### What Happens When a Container Restarts

```
Container restart (docker restart or auto-restart)
  │
  ├─ Phase 1: Stop (same as above)
  │
  ├─ Phase 2: Start
  │   ├─ T+0s:   Docker creates new container from same image
  │   ├─ T+0s:   entrypoint.sh runs
  │   ├─ T+1-5s: alembic upgrade head (if in entrypoint)
  │   ├─ T+5s:   uvicorn/gunicorn starts
  │   ├─ T+5s:   FastAPI lifespan startup:
  │   │           ├─ Redis connection established
  │   │           ├─ RabbitMQ consumer connected
  │   │           ├─ Scheduler started (auth-service)
  │   │           └─ DB connectivity verified (audit-service)
  │   └─ T+5s:   Server begins accepting requests
  │
  ├─ Phase 3: Health Check
  │   ├─ T+5-15s:  start_period begins (15-30s depending on service)
  │   ├─ T+15-45s: First health check runs
  │   │             ├─ Checks DB: SELECT 1
  │   │             ├─ Checks Redis: PING
  │   │             └─ Checks RabbitMQ: connection.is_closed
  │   └─ T+45-60s: Container marked "healthy"
  │
  └─ Phase 4: Traffic Resumes
      └─ Nginx routes requests to container (DNS resolved)
```

### What Happens When a Container Crashes

```
Container crash (unhandled exception, segfault, OOM)
  │
  ├─ T+0s:   Process exits immediately
  │           ├─ No SIGTERM sent (crash, not stop)
  │           ├─ No lifespan shutdown hook runs
  │           ├─ No Redis cleanup
  │           ├─ No RabbitMQ consumer close
  │           ├─ No graceful worker drain
  │           └─ Active connections abandoned
  │
  ├─ T+0s:   Impact on active resources:
  │           ├─ DB connections: orphaned in pool (PG cleans up via tcp_keepalive)
  │           ├─ Redis connections: orphaned (Redis timeout cleans up)
  │           ├─ RabbitMQ: unacked messages requeued after consumer timeout
  │           ├─ In-flight HTTP requests: connection reset to client
  │           └─ Scheduled jobs: stopped (no compensation)
  │
  ├─ T+1s:   Docker detects exit, checks restart policy
  │
  └─ T+1s → T+60s: Same restart sequence as above
```

---

## Docker Restart Policy Behavior

### Current Policy: `unless-stopped`

All services in docker-compose.yml use `restart: unless-stopped`.

| Event | `no` | `always` | `on-failure` | `unless-stopped` (current) |
|-------|------|----------|--------------|---------------------------|
| Container exits (error) | Stays dead | Restarts | Restarts | Restarts |
| Container exits (success, code 0) | Stays dead | Restarts | Stays dead | Stays dead |
| Docker daemon restarts | Stays dead | Restarts | Stays dead | Restarts |
| Manual `docker stop` | N/A | Restarts on daemon restart | N/A | Stays stopped |
| OOMKilled | Stays dead | Restarts | Restarts | Restarts |
| Host reboot | Stays dead | Restarts | Stays dead | Restarts (if was running) |

### Why `unless-stopped` Is Appropriate

- Auto-restarts after crashes (high availability)
- Respects manual `docker stop` (operational control)
- Survives Docker daemon restart / host reboot
- Only drawback: no exponential backoff on rapid crash loops

### Missing: Restart Backoff

Docker Compose does NOT have native backoff like Kubernetes. If a container crash-loops:
- `unless-stopped`: restarts immediately, every time, forever
- CPU waste from rapid start/crash cycles
- Log flooding from repeated startup messages

**Kubernetes equivalent:** CrashLoopBackOff (5s → 10s → 20s → 40s → ... → 5min cap)

---

## Impact on Active Requests

### Graceful Stop (SIGTERM)

| Service Type | Entrypoint | In-Flight Request Fate |
|-------------|------------|----------------------|
| Auth (Gunicorn) | graceful-timeout: 15s | Completes if finishes within 10s (Docker kills at 10s) |
| Employee (Gunicorn) | graceful-timeout: 15s | Same — completes within Docker timeout |
| Attendance (Uvicorn raw) | no graceful config | TERMINATED immediately on SIGTERM |
| Students (Uvicorn raw) | no graceful config | TERMINATED immediately |
| Payroll (Uvicorn raw) | no graceful config | TERMINATED immediately |
| Leave (Uvicorn raw) | no graceful config | TERMINATED immediately |
| Audit (Uvicorn raw) | no graceful config | TERMINATED immediately |
| Notification (Uvicorn raw) | no graceful config | TERMINATED immediately |

### Crash (SIGKILL / OOM / Exception Exit)

All services: in-flight requests TERMINATED. No graceful handling possible.

### Impact on In-Flight Transactions

```
Request lifecycle during shutdown:

  1. HTTP request received by Uvicorn
  2. FastAPI routes to handler
  3. Handler begins DB transaction (implicit via session)
  4. SQL INSERT/UPDATE executed
                               ← SIGTERM arrives here
  5. await db.commit()         ← This line may or may not execute
  6. Return HTTP response

  If SIGTERM before commit:
    → Transaction never committed
    → PostgreSQL connection drops
    → PG detects orphaned connection via tcp_keepalive
    → PG rolls back uncommitted transaction
    → Data: SAFE (no partial write)

  If SIGTERM after commit, before response:
    → Data committed to DB (permanent)
    → HTTP response not sent to client
    → Client sees "connection reset"
    → Client may retry → duplicate write risk (no idempotency)
    → Data: COMMITTED but client unaware
```

### Impact on Background Jobs

| Job | Service | Frequency | Stop Behavior |
|-----|---------|-----------|---------------|
| Token purge | Auth | 1 hour | APScheduler: `shutdown(wait=False)` — current job may be interrupted |
| Magic token purge | Auth | 6 hours | Same as above |
| Health ping | Auth | 15 minutes | Same as above |
| Audit retention | Audit | Once at startup | asyncio.Task: cancelled on shutdown |
| RabbitMQ consumer | Audit | Continuous | Consumer closed — unacked messages requeued by RabbitMQ |
| RabbitMQ consumer | Notification | Continuous | Consumer closed — unacked messages requeued |
| RabbitMQ consumer | Payroll | Continuous | Consumer closed — unacked messages requeued |

**Token purge interruption risk:** If purge is mid-DELETE when killed, the transaction rolls back. Expired tokens remain until next purge run. No data corruption.

---

## Health Check Timing Analysis

```
Service startup timeline:

T+0s    Container created
T+1s    entrypoint.sh starts
T+2s    alembic upgrade head (if needed — usually no-op)
T+3s    uvicorn/gunicorn starts
T+4s    FastAPI lifespan: Redis/RabbitMQ connections
T+5s    Server accepting requests
        │
        │  start_period (15-30s): health checks ignored
        │
T+20s   First health check attempt
T+20s   GET /health → checks DB + Redis
        │
        │  If healthy: Container marked "healthy"
        │  If unhealthy: retries (3 retries at 30s interval)
        │
T+50s   Worst case: 3 retries at 30s = 90s before unhealthy
T+80s   If still unhealthy: Container restarted
```

**Gap:** Between T+5s (server up) and T+20s (first health check), the service may receive traffic from Nginx but is not yet verified as healthy. Nginx doesn't check Docker health status — it just tries the upstream and returns 502 if it fails.
