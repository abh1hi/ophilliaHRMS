# API Gateway Contract (v3)

The API Gateway (nginx) acts as the single entry point for all client traffic, routing requests to backend microservices and enforcing cross-cutting concerns.

## Base URL
- **External**: `http://localhost:80` (Docker) or `https://your-domain.com` (production)
- **Internal services are NOT exposed directly** — all traffic must pass through the gateway.

---

## Responsibilities

| Concern | Implementation |
| :--- | :--- |
| Routing | Path-based routing to backend services |
| Rate Limiting | nginx `limit_req` zones (per-IP) |
| Security Headers | X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy |
| API Versioning | `API-Version: v1` response header on all requests |
| Request ID | `X-Request-ID` propagated to all upstream services |
| CORS | Preflight OPTIONS handling per service block |
| Error Pages | Standardized JSON error responses for 429, 502, 503, 504 |
| Health Aggregation | Individual `/health` endpoints exposed per service |

---

## API Version Policy

- **Current version**: `v1` (all endpoints under `/api/v1/`)
- **Version header**: Every response includes `API-Version: v1`
- **Freeze policy**: The v1 API surface is frozen as of contract v3. Breaking changes require a new version prefix (`/api/v2/`).
- **Deprecation**: When v2 is introduced, v1 endpoints will include `Deprecation: true` and `Sunset: <date>` response headers for a minimum of 90 days before removal.

---

## Route Map

| Gateway Path | Upstream Service | Port |
| :--- | :--- | :--- |
| `/api/v1/auth/*` | auth-service | 8000 |
| `/api/v1/employees/*` | employee-service | 8001 |
| `/api/v1/departments/*` | employee-service | 8001 |
| `/api/v1/attendance/*` | attendance-service | 8002 |
| `/api/v1/students/*` | students-service | 8003 |
| `/api/v1/classes/*` | students-service | 8003 |
| `/api/v1/guardians/*` | students-service | 8003 |
| `/api/v1/payroll/*` | payroll-service | 8004 |
| `/api/v1/salary/*` | payroll-service | 8004 |
| `/api/v1/leave/*` | leave-service | 8005 |
| `/api/v1/audit/*` | audit-service | 8006 |
| `/api/v1/notifications/*` | notification-service | 8007 |
| `/` | frontend (Vue SPA) | 3000 |

---

## Rate Limiting

| Zone | Rate | Burst | Applied To |
| :--- | :--- | :--- | :--- |
| `auth_login` | 5 req/s | 10 | `POST /api/v1/auth/login` |
| `api_general` | 30 req/s | 20 | All other `/api/v1/*` routes |

---

## Health Endpoints

Each service exposes a health check through the gateway:

| Endpoint | Upstream |
| :--- | :--- |
| `/health` | Gateway itself (static JSON) |
| `/api/v1/auth/health` | auth-service `/health` |
| `/api/v1/employees/health` | employee-service `/health` |
| `/api/v1/attendance/health` | attendance-service `/health` |
| `/api/v1/students/health` | students-service `/health` |
| `/api/v1/payroll/health` | payroll-service `/health` |
| `/api/v1/leave/health` | leave-service `/health` |
| `/api/v1/notifications/health` | notification-service `/health` |
| `/api/v1/audit/health` | audit-service `/health` |

**Health Response Format** (all services):
```json
{
  "status": "healthy" | "degraded",
  "service": "<service-name>",
  "version": "1.0.0",
  "checks": {
    "database": "ok" | "error",
    "redis": "ok" | "error",
    "rabbitmq": "ok" | "error"
  }
}
```

---

## Timeouts

| Setting | Value |
| :--- | :--- |
| `proxy_connect_timeout` | 3s |
| `proxy_send_timeout` | 10s |
| `proxy_read_timeout` | 10s |

---

## Error Responses

| HTTP Status | Response |
| :--- | :--- |
| 429 | `{"detail": "Too many requests. Please slow down."}` |
| 502, 503, 504 | `{"detail": "Service temporarily unavailable. Please retry."}` |

---

## DNS Resolution

The gateway uses Docker's internal DNS resolver (`127.0.0.11`) with `valid=10s` to resolve service hostnames at request time. This allows the gateway to survive service restarts without requiring its own restart.

---

## Internal Endpoints Blocked

| Path | Action |
| :--- | :--- |
| `/metrics` | Blocked (returns 403) — Prometheus scrapes directly |
| `/employees/internal/*` | Not routed — service-to-service only |
