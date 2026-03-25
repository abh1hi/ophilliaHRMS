# 10 — Best Practices & Architecture Diagrams

## Best Practice Assessment

### 1. Graceful Shutdown

**Current State:**
| Service | Graceful Shutdown? | Method | Grade |
|---------|-------------------|--------|-------|
| Auth | Yes | Gunicorn graceful-timeout 15s + FastAPI lifespan 5s | B+ |
| Employee | Yes | Gunicorn graceful-timeout 15s + FastAPI lifespan 5s | B+ |
| Attendance | Partial | FastAPI lifespan 5s, but raw Uvicorn (no drain) | C |
| Students | Partial | FastAPI lifespan, raw Uvicorn, runs as root | D |
| Payroll | Partial | FastAPI lifespan 5s, raw Uvicorn | C |
| Leave | Partial | FastAPI lifespan 5s, raw Uvicorn | C |
| Audit | Partial | FastAPI lifespan 5s, raw Uvicorn, RabbitMQ consumer close | C+ |
| Notification | Partial | FastAPI lifespan 5s, raw Uvicorn, consumer close | C+ |

**Industry Standard:**
```python
# Recommended: All services should use Gunicorn with proper timeouts
# entrypoint.sh (standardized):
exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 2 \
  --bind 0.0.0.0:${PORT} \
  --timeout 60 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --log-level warning

# docker-compose.yml (per service):
stop_grace_period: 35s  # Must exceed gunicorn graceful-timeout
```

**Key Principle:** `stop_grace_period` > `graceful-timeout` > `lifespan sleep`. Otherwise Docker sends SIGKILL before the application finishes draining.

---

### 2. Health Checks

**Current State:**
- All services implement `/health` endpoint checking DB + Redis/RabbitMQ
- Returns `{"status": "healthy"}` or `{"status": "degraded"}`
- Docker health checks configured in docker-compose.yml
- **Problem:** Returns HTTP 200 even when `degraded` — Docker considers it healthy

**Industry Standard:**
```python
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    checks = {}
    # ... check DB, Redis, RabbitMQ ...

    all_ok = all(v == "ok" for v in checks.values())

    if all_ok:
        return JSONResponse(
            status_code=200,
            content={"status": "healthy", "checks": checks}
        )
    else:
        return JSONResponse(
            status_code=503,  # ← Docker will mark as unhealthy
            content={"status": "degraded", "checks": checks}
        )
```

**Three-tier health check pattern:**
```
/health/live    → Am I running? (always 200 if process alive)
/health/ready   → Can I serve traffic? (503 if DB/Redis down)
/health/startup → Have I finished initialization? (503 during migration)
```

---

### 3. Circuit Breakers

**Current State:** Not implemented. Services call each other directly with no failure isolation.

**Risk:** If auth-service is slow, all services that validate tokens against it accumulate waiting threads, exhausting their own resources (cascading failure).

**Industry Standard:**
```python
# Using tenacity with circuit breaker pattern:
from tenacity import retry, stop_after_attempt, wait_exponential, CircuitBreaker

circuit_breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=30,      # Try again after 30s
    expected_exception=Exception,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    before_sleep=circuit_breaker,
)
async def call_auth_service(token: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            "http://auth-service:8000/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()
```

**Where needed:**
- Employee service → Auth service (user validation)
- Attendance service → Employee service (employee lookup)
- Leave service → Employee service (employee verification)
- Payroll service → Employee service (salary data)

---

### 4. Retry Strategies

**Current State:**
| Component | Retry? | Strategy |
|-----------|--------|----------|
| RabbitMQ publisher | Yes | 3 retries, exponential backoff (2^n seconds) |
| HTTP inter-service calls | No | Single attempt, timeout at 10s |
| Database connections | Partial | pool_pre_ping (reconnect), but no query retry |
| Redis operations | No | Single attempt, fallback to default |

**Industry Standard:**
```python
# Retry with jitter to prevent thundering herd:
import random

async def retry_with_jitter(func, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return await func()
        except TransientError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)
```

---

### 5. Idempotency

**Current State:**
| Operation | Idempotent? | Protection |
|-----------|-------------|------------|
| Employee creation | No | Email unique constraint only |
| Attendance clock-in | Yes | UniqueConstraint(employee_id, date) |
| Leave request | No | No dedup mechanism |
| Payroll run | Yes | UniqueConstraint(company_id, period_start, period_end) |
| Audit event | Yes | UniqueConstraint(event_id) |
| Notification | No | No dedup |

**Industry Standard:**
```
Client sends: POST /employees
Headers: Idempotency-Key: abc-123

Server:
  1. Check if abc-123 exists in idempotency_keys table
  2. If exists: return cached response (no re-execution)
  3. If not: execute, store result with key, return response

Table: idempotency_keys
  - key (VARCHAR UNIQUE)
  - response_status (INT)
  - response_body (JSONB)
  - created_at (TIMESTAMP)
  - expires_at (TIMESTAMP)  -- Auto-cleanup after 24h
```

---

### 6. Logging & Tracing

**Current State:**
- Structured JSON logging in all services (good)
- X-Request-ID propagation via middleware (good)
- Correlation ID in RabbitMQ events (good)
- Log output to stdout (12-factor compliant, good)
- No centralized log aggregation (gap)
- No distributed tracing (gap)

**Industry Standard:**
```
Current:   Service → stdout → Docker JSON log driver → disk
                              (no aggregation, no search)

Recommended: Service → stdout → Promtail → Loki → Grafana
                                (centralized, searchable, alertable)

Future:    Service → OpenTelemetry → Jaeger/Tempo
                     (distributed traces, latency analysis)
```

---

## Architecture Diagrams

### Current System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         SINGLE VPS                                    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     Docker Engine                                │ │
│  │                                                                   │ │
│  │  ┌─────────┐                                                     │ │
│  │  │  Nginx  │◀── Port 80 (HTTP only, no TLS)                    │ │
│  │  │ Gateway │                                                     │ │
│  │  └────┬────┘                                                     │ │
│  │       │                                                           │ │
│  │       ├───────────┬───────────┬───────────┬──────────────────┐  │ │
│  │       │           │           │           │                  │  │ │
│  │  ┌────▼───┐ ┌─────▼──┐ ┌─────▼──┐ ┌─────▼──┐  ... (8 svc) │  │ │
│  │  │  Auth  │ │Employee│ │Attend. │ │Payroll │               │  │ │
│  │  │ :8000  │ │ :8001  │ │ :8002  │ │ :8004  │               │  │ │
│  │  │Gunicorn│ │Gunicorn│ │Uvicorn │ │Uvicorn │               │  │ │
│  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘               │  │ │
│  │      │          │          │          │                     │  │ │
│  │      └──────────┴──────────┴──────────┘                     │  │ │
│  │                        │                                      │  │ │
│  │              ┌─────────┴─────────┐                           │  │ │
│  │              │                   │                            │  │ │
│  │         ┌────▼────┐        ┌────▼────┐     ┌──────────┐    │  │ │
│  │         │Postgres │        │  Redis  │     │ RabbitMQ │    │  │ │
│  │         │ :5432   │        │  :6379  │     │  :5672   │    │  │ │
│  │         │ 1024MB  │        │  200MB  │     │  768MB   │    │  │ │
│  │         │ 8 DBs   │        │ no auth │     │  tmpfs!  │    │  │ │
│  │         │ vol:✓   │        │ vol:✓   │     │  vol:✗   │    │  │ │
│  │         └─────────┘        └─────────┘     └──────────┘    │  │ │
│  │                                                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  SPOFs: VPS, Postgres, Nginx, Redis, RabbitMQ, Docker daemon          │
└──────────────────────────────────────────────────────────────────────┘
```

### Failure Flow: PostgreSQL Crash

```
           PostgreSQL crashes (OOM / disk / bug)
                        │
           ┌────────────┼────────────┐
           │            │            │
     ┌─────▼─────┐ ┌───▼────┐ ┌────▼────┐
     │Auth Service│ │Employee│ │All other│
     │health check│ │ health │ │services │
     │DB: error   │ │DB: error│ │DB: error│
     └─────┬─────┘ └───┬────┘ └────┬────┘
           │            │            │
     Returns "degraded" (HTTP 200)  │
           │            │            │
     ┌─────▼────────────▼────────────▼─────┐
     │  All API requests return 500         │
     │  "INTERNAL_SERVER_ERROR"             │
     │  Health checks: "degraded" (200)     │
     │  Docker: considers "healthy" ← BUG  │
     └─────────────────────────────────────┘
                        │
                   Docker restarts
                   PostgreSQL (30-60s)
                        │
     ┌──────────────────▼──────────────────┐
     │  PostgreSQL recovery:                │
     │  1. WAL replay (committed data safe)│
     │  2. Rollback uncommitted txns       │
     │  3. Accept connections              │
     └──────────────────┬──────────────────┘
                        │
     ┌──────────────────▼──────────────────┐
     │  Services auto-reconnect:            │
     │  pool_pre_ping detects recovery     │
     │  Next request gets fresh connection  │
     │  System operational                  │
     └─────────────────────────────────────┘
```

### Failure Flow: Complete VPS Loss

```
     VPS loses power / hardware failure
                    │
     ┌──────────────┼──────────────┐
     │              │              │
  ┌──▼──┐      ┌───▼───┐     ┌───▼───┐
  │All  │      │Postgres│     │RabbitMQ│
  │svcs │      │  WAL   │     │ tmpfs  │
  │KILL │      │on disk │     │ LOST   │
  └──┬──┘      └───┬───┘     └───┬───┘
     │              │              │
     │   ┌──────────┘              │
     │   │                         │
     ▼   ▼                         ▼
  ┌─────────────┐         ┌──────────────┐
  │Docker volume│         │Events in     │
  │survives if  │         │flight are    │
  │disk intact  │         │permanently   │
  └──────┬──────┘         │lost (tmpfs)  │
         │                └──────────────┘
         │
    VPS restored / new VPS provisioned
         │
  ┌──────▼──────────────────────────────┐
  │ Recovery path:                       │
  │ 1. Docker daemon starts              │
  │ 2. Containers restart (unless-stopped)│
  │ 3. PostgreSQL: WAL recovery          │
  │ 4. Redis: AOF replay                 │
  │ 5. RabbitMQ: starts empty            │
  │ 6. Services: reconnect to all deps   │
  │ 7. System operational (30-90s)       │
  │                                      │
  │ IF disk destroyed:                   │
  │ → No backup = TOTAL DATA LOSS       │
  │ → With backup = restore from remote  │
  └─────────────────────────────────────┘
```

### Recovery Flow: Full Restore from Backup

```
  New VPS provisioned
         │
  ┌──────▼──────┐
  │ Install     │
  │ Docker +    │
  │ Compose     │
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │ Clone repo  │
  │ git clone   │
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │ Start infra │    docker compose up -d hrms-db redis rabbitmq
  │ only        │    Wait for health checks
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │ Download    │    aws s3 cp s3://backups/latest.tar.gz /tmp/
  │ backup      │
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │ Restore DBs │    pg_restore for each of 8 databases
  │ (8 DBs)     │    ~5-30 min depending on size
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │ Run         │    alembic upgrade head per service
  │ migrations  │    (apply any migrations newer than backup)
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │ Start all   │    docker compose up -d
  │ services    │    Wait for all health checks
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │ Verify      │    curl each /health endpoint
  │ & DNS       │    Update DNS to new VPS IP
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │ OPERATIONAL  │   Estimated total: 1-4 hours
  └─────────────┘
```

### Data Flow During Failure (Request Lifecycle)

```
Normal request:
  Client → Nginx → Service → DB → Service → Nginx → Client

DB failure during request:
  Client → Nginx → Service → DB ✗ → Service catches error
                                      → Returns JSON error
                                      → Nginx → Client (500)

Service crash during request:
  Client → Nginx → Service ✗ → Nginx detects upstream gone
                                → Returns 502 JSON → Client

Nginx crash:
  Client → Nginx ✗ → Connection refused → Client timeout

VPS crash:
  Client → VPS ✗ → No response → Client timeout (30-60s)
```

---

## Summary of Best Practice Compliance

| Practice | Current | Required | Gap |
|----------|---------|----------|-----|
| Graceful shutdown | 2/8 services (Gunicorn) | All services | HIGH |
| Health checks | All services (but 200 on degraded) | 503 on degraded | MEDIUM |
| Circuit breakers | None | All inter-service calls | HIGH |
| Retry strategies | RabbitMQ publisher only | All external calls | HIGH |
| Idempotency | 2/6 write operations | All write operations | HIGH |
| Structured logging | All services | All services | DONE |
| Request tracing | X-Request-ID propagation | Full distributed tracing | MEDIUM |
| Centralized logging | None | Loki/ELK | HIGH |
| Metrics collection | Audit service only | All services + infra | HIGH |
| Automated backups | None | Daily + WAL archiving | CRITICAL |
| Secret management | .env files in repo | Vault/Docker secrets | HIGH |
| TLS/HTTPS | None | Gateway + inter-service | CRITICAL |
| Connection pooling | Configured (oversized) | Right-sized, monitored | MEDIUM |
| Rate limiting | Nginx (IP-based) | + per-tenant, per-user | MEDIUM |
