# 03 — Application & Database Failure Scenarios

## Application Level Failures

---

### Scenario A1: Service Crash (Bug / Unhandled Exception)

**Trigger:** Null pointer equivalent, unhandled async exception, invalid data causes panic

**Timeline:**
1. `T+0s` — Exception propagates to top-level, process exits
2. `T+0s` — Docker marks container as `Exited`
3. `T+0s` — Nginx: next request to this service gets no upstream response
4. `T+0-10s` — Nginx DNS cache (valid=10s): may try dead container IP
5. `T+0s` — Nginx returns `502 Bad Gateway` → JSON: `{"detail": "Service temporarily unavailable"}`
6. `T+1s` — Docker `unless-stopped` triggers restart
7. `T+5-15s` — Container runs entrypoint: `alembic upgrade head && uvicorn/gunicorn start`
8. `T+15s` — Health check start_period begins (15-30s depending on service)
9. `T+45-60s` — Container healthy, traffic resumes

**System Behavior:**
- Exception handlers catch most errors (`exception_handlers.py` covers HTTP, Validation, and unhandled)
- Only truly fatal errors (segfault, OS-level) cause process exit
- Structured JSON error logging includes path, request_id, and full stack trace
- Other services: completely unaffected (microservice isolation)

**User Impact:**
- Specific module unavailable for 30-60s
- Frontend shows error toast from API response
- User can navigate to other modules while affected one recovers

**Data Safety:** No risk. DB transactions are atomic; uncommitted work rolls back.

**Best Case:** Transient bug, single crash, auto-recovers in 30s.
**Worst Case:** Persistent bug, restart loop, requires code fix and redeploy.

---

### Scenario A2: API Gateway (Nginx) Failure

**Trigger:** Nginx misconfiguration, worker crash, OOM, manual stop

**Timeline:**
1. `T+0s` — Nginx process dies
2. `T+0s` — Port 80 stops accepting connections
3. `T+0s` — ALL external traffic blocked (gateway is sole entry point)
4. `T+0s` — Internal service-to-service calls unaffected (direct Docker DNS)
5. `T+0s` — RabbitMQ consumers continue processing events internally
6. `T+1s` — Docker restarts gateway container
7. `T+5s` — Nginx boots (near-instant startup)
8. `T+5s` — Health check: `wget -qO- http://127.0.0.1/health` (3s timeout)
9. `T+10s` — Gateway healthy, external traffic resumes

**System Behavior:**
- Gateway restart is fast (~5 seconds) because Nginx is lightweight
- DNS resolution via `resolver 127.0.0.11 valid=10s` — services discovered immediately
- Nginx upstream variables resolved at request time (not startup time)
- No connection draining during crash — active requests get connection reset

**User Impact:**
- Total external unavailability for ~10 seconds
- Frontend SPA already loaded in browser still works (client-side cached)
- API calls fail with network error
- Backend services continue operating normally (just unreachable from outside)

**Data Safety:** No risk. Gateway is stateless.

**Best Case:** 5-10 second outage, auto-restart.
**Worst Case:** Config error causes restart loop — requires manual fix.

---

### Scenario A3: Auth Service Down

**Trigger:** Crash, OOM, restart, deployment

**Timeline:**
1. `T+0s` — Auth service stops responding
2. `T+0s` — Login attempts: fail immediately (POST /auth/login → 502)
3. `T+0s` — Token refresh: fail (POST /auth/refresh → 502)
4. `T+0s` — Existing valid JWTs: CONTINUE WORKING (verified locally by each service using public key)
5. `T+15min` — Existing access tokens start expiring (15-minute TTL)
6. `T+15min` — Users with expired tokens and no refresh: forced to re-login (which fails)
7. `T+15min` — Gradual user lockout begins

**System Behavior:**
- JWT validation is LOCAL (each service has the public key — no auth-service call needed)
- Token blacklist check goes to Redis directly (not auth-service)
- Users with valid, non-expired tokens: FULLY FUNCTIONAL
- New logins, token refresh, password reset: ALL FAIL
- User creation, role changes, company management: ALL FAIL

**Cascade Impact:**
```
Auth Service Down
  ├── New logins: BLOCKED
  ├── Token refresh: BLOCKED (tokens expire in 15min)
  ├── Existing sessions (< 15min old): WORKING
  ├── Employee CRUD: WORKING (uses JWT locally)
  ├── Attendance: WORKING
  ├── Leave requests: WORKING
  ├── Payroll: WORKING
  └── Audit/Notifications: WORKING (event-driven, async)
```

**User Impact:**
- Users already logged in: unaffected for up to 15 minutes
- New users / returning users: cannot access system
- After 15 min: progressive lockout as tokens expire

**Data Safety:** No data risk. Auth service doesn't own business data.

**Best Case:** Auth restarts in 30s. Only users actively logging in during those 30s are affected.
**Worst Case:** Extended auth outage (>15min). All users gradually locked out.

---

### Scenario A4: Database Connection Failure

**Trigger:** PostgreSQL overloaded, connection limit hit, network partition between containers

**Timeline:**
1. `T+0s` — Service attempts DB query, connection fails
2. `T+0s` — `pool_pre_ping=True` detects stale connection, tries to reconnect
3. `T+10s` — Connection timeout (`connect_args={"timeout": 10}`) expires
4. `T+10s` — Request returns HTTP 500 with `{"error": {"code": "INTERNAL_SERVER_ERROR"}}`
5. `T+30s` — Health check polls: `SELECT 1` fails → service reports `degraded`
6. `T+30s` — Docker health check: considers degraded as still running (HTTP 200 returned)
7. `T+?` — If PostgreSQL recovers: `pool_pre_ping` auto-reconnects on next request

**System Behavior:**
- `pool_pre_ping=True` means SQLAlchemy validates connections before use
- Stale connections in pool are replaced automatically
- Connection pool overflow (40 extra): handles burst after recovery
- `pool_recycle=3600`: prevents stale connections from lingering >1 hour

**Critical Issue:** Health endpoints return HTTP 200 even when `status: "degraded"`. Docker health check interprets any 200 as healthy. Degraded services are NOT restarted.

**User Impact:**
- All database-dependent operations fail with 500 errors
- Static pages (frontend SPA shell) still load
- API calls return error JSON

**Data Safety:** Safe. Failed connections = no writes attempted. No partial state.

---

### Scenario A5: Redis Failure

**Trigger:** Redis container crash, OOM (100MB limit), connection timeout

**Timeline:**
1. `T+0s` — Redis stops responding
2. `T+0s` — Token blacklist check: `is_blacklisted()` returns `False` (fallback behavior)
3. `T+0s` — Revoked tokens are now ACCEPTED (security degradation)
4. `T+0s` — Health checks report `degraded` (Redis check fails)
5. `T+1s` — Docker restarts Redis container (unless-stopped)
6. `T+5s` — Redis loads AOF from disk (~1-2s for 100MB)
7. `T+10s` — Redis healthy, blacklist operational again

**System Behavior:**
- **Graceful degradation by design**: Redis failure does NOT crash services
- Code pattern: `if _redis is None: return False` — treats unavailable Redis as "not blacklisted"
- This is a conscious trade-off: availability over strict security during Redis outage
- All other service functions (DB reads/writes, API responses) continue normally

**Security Impact:**
- Window of vulnerability: any token that was revoked (logout, password change) can be reused
- Duration: until Redis recovers + loads AOF
- Scope: only affects tokens that were actively blacklisted

**User Impact:** Users likely unaware. System continues operating. Logged-out sessions may appear to still work.

**Data Safety:** No data risk. Redis is a cache, not a data store.

**Best Case:** Redis restarts in 5-10s, AOF restores blacklist, brief security window.
**Worst Case:** Redis data lost (AOF corrupt), blacklist empty. All previously revoked tokens temporarily valid until they naturally expire (15min for access, 7 days for refresh).

---

## Database Level Failures

---

### Scenario D1: PostgreSQL Crash

**Trigger:** OOMKill, bug, disk error, manual kill

**Timeline:**
1. `T+0s` — PostgreSQL process terminates
2. `T+0s` — All 8 services lose DB connectivity simultaneously
3. `T+0s` — All API requests that need DB return 500
4. `T+0s` — In-flight transactions: automatically rolled back by PG on recovery
5. `T+1s` — Docker restarts PostgreSQL container
6. `T+5s` — PostgreSQL enters recovery mode
7. `T+5-30s` — WAL replay: replays committed transactions since last checkpoint
8. `T+30s` — PostgreSQL accepts connections
9. `T+30s` — Services reconnect via `pool_pre_ping` on next request
10. `T+45-60s` — Health checks pass, system fully operational

**System Behavior:**
- PostgreSQL WAL (Write-Ahead Log) ensures durability
- All committed transactions survive the crash
- All uncommitted transactions are rolled back
- Checkpoint interval (default 5 min) determines WAL replay volume
- Connection pool (`pool_pre_ping=True`) auto-detects recovered connections

**User Impact:**
- Total system outage for 30-60 seconds
- All modules affected simultaneously
- Frontend shows error states on all data-dependent components

**Data Safety:**
- Committed data: GUARANTEED SAFE (WAL durability)
- Uncommitted data: LOST (rolled back by design)
- Database integrity: PRESERVED (ACID compliance)

**Best Case:** Clean restart, minimal WAL replay, 30s outage.
**Worst Case:** Disk corruption during crash — requires manual recovery or backup restore.

---

### Scenario D2: Data Corruption

**Trigger:** Disk sector failure, incomplete write, storage hardware issue

**Timeline:**
1. `T+0s` — PostgreSQL detects checksum mismatch or corrupted page
2. `T+0s` — Affected queries fail with `ERROR: invalid page in block` or similar
3. `T+0s` — PostgreSQL may continue serving uncorrupted data
4. `T+?` — Administrator detects via error logs
5. `T+?` — Manual intervention required

**System Behavior:**
- PostgreSQL 16 has data checksums (if enabled during initdb — not explicitly configured here)
- Corruption may be limited to specific tables/pages
- Unaffected tables continue operating normally
- No automatic recovery — requires manual `pg_resetwal`, backup restore, or table-level recovery

**User Impact:** Depends on which table is corrupted. Could range from one module's data inaccessible to complete data loss.

**Data Safety:** HIGH RISK. Without backups, corrupted data may be unrecoverable.

**Best Case:** Corruption limited to a single page, detectable, recoverable via REINDEX or pg_dump of uncorrupted tables.
**Worst Case:** System catalog corruption. Database unreadable. Without backup: permanent data loss.

---

### Scenario D3: Slow Queries / Deadlocks

**Trigger:** Missing index, large table scan, concurrent bulk operations, N+1 queries

**Timeline:**
1. `T+0s` — Slow query holds DB connections for extended period
2. `T+0s` — Connection pool drains (20 base connections consumed)
3. `T+10s` — Pool overflow begins (up to 40 additional connections)
4. `T+?` — All 60 connections consumed → new requests wait in queue
5. `T+10s` — `connect_args={"timeout": 10}` expires → requests fail with timeout
6. `T+?` — Slow query completes, connections released, pool recovers

**System Behavior:**
- No `statement_timeout` configured in PostgreSQL (queries run indefinitely)
- No query timeout in application code
- Only protection: Nginx proxy_read_timeout of 10s (kills request at gateway level)
- Database connections remain held even after Nginx timeout (query still running in PG)
- Connection leak risk: if application doesn't properly close sessions after timeout

**User Impact:**
- Progressive degradation: first slow, then timeouts, then errors
- Specific service affected (each has own DB, own pool)
- Other services using other databases: unaffected

**Data Safety:** No corruption risk. Deadlocks are auto-resolved by PostgreSQL (one transaction rolled back).

---

### Scenario D4: Connection Pool Exhaustion

**Trigger:** Traffic spike, slow queries holding connections, connection leak

**Timeline:**
1. `T+0s` — All pool connections (20 base + 40 overflow = 60) in use
2. `T+0s` — New DB requests queue, waiting for connection
3. `T+10s` — Connection checkout timeout (10s) expires
4. `T+10s` — SQLAlchemy raises `TimeoutError: QueuePool limit`
5. `T+10s` — Application returns HTTP 500
6. `T+10s` — If traffic subsides: connections return to pool, service recovers

**Aggregate Risk:**
- 8 services × 60 max connections = 480 possible connections
- PostgreSQL default `max_connections` = 100
- **If >2 services hit peak simultaneously, PostgreSQL will reject connections**
- Error: `FATAL: too many connections for role "postgres"`

**System Behavior:**
- SQLAlchemy `pool_pre_ping` won't help (PG rejecting at connection level)
- All services competing for same 100 connection slots
- Services with fewer connections may be starved by services with more active connections

**User Impact:** Random 500 errors across multiple modules. Hard to diagnose because it appears as intermittent failures.

**Mitigation Required:**
```sql
-- In PostgreSQL configuration:
ALTER SYSTEM SET max_connections = 500;
-- Or reduce per-service pool:
-- pool_size=10, max_overflow=15 = 25/service × 8 = 200 total
```
