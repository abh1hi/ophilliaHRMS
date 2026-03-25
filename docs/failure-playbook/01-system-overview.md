# 01 — System Overview & Single Points of Failure

## Current Architecture

```
                              ┌─── Single VPS ────────────────────────────────────┐
                              │                                                    │
 Users ──── Internet ────────▶│  ┌─────────┐    ┌──────────────────────────────┐  │
                              │  │  Nginx   │───▶│  Microservices (8 FastAPI)   │  │
                              │  │ Gateway  │    │                              │  │
                              │  │  :80     │    │  Auth      :8000  ─┐        │  │
                              │  └─────────┘    │  Employee  :8001   │        │  │
                              │       │          │  Attendance:8002   ├──┐     │  │
                              │       │          │  Students  :8003   │  │     │  │
                              │       ▼          │  Payroll   :8004   │  │     │  │
                              │  ┌─────────┐    │  Leave     :8005   │  │     │  │
                              │  │Frontend │    │  Audit     :8006   │  │     │  │
                              │  │ Vue:3000│    │  Notify    :8007  ─┘  │     │  │
                              │  └─────────┘    └──────────────────────┼─────┘  │
                              │                                         │         │
                              │  ┌──────────────────────────────────────┘         │
                              │  │                                                │
                              │  ▼                                                │
                              │  ┌──────────┐  ┌───────────┐  ┌───────────┐     │
                              │  │PostgreSQL│  │ RabbitMQ  │  │   Redis   │     │
                              │  │  :5432   │  │  :5672    │  │   :6379   │     │
                              │  │ 8 DBs    │  │  tmpfs!   │  │  100MB    │     │
                              │  │ 1024MB   │  │  768MB    │  │  200MB    │     │
                              │  └──────────┘  └───────────┘  └───────────┘     │
                              │                                                    │
                              └────────────────────────────────────────────────────┘
```

## Service Inventory

| Service | Port | Database | Profile | Workers | Entrypoint | Resource Limit |
|---------|------|----------|---------|---------|------------|----------------|
| Auth | 8000 | auth_db | core | Gunicorn 1W | graceful-timeout 15s | 1 CPU, 768MB |
| Employee | 8001 | employee_db | hr | Gunicorn 1W | graceful-timeout 15s | 1 CPU, 768MB |
| Attendance | 8002 | attendance_db | hr | Uvicorn (raw) | no timeout config | 1 CPU, 768MB |
| Students | 8003 | students_db | student | Uvicorn (raw) | no timeout config | 1 CPU, 768MB |
| Payroll | 8004 | payroll_db | hr | Uvicorn (raw) | no timeout config | 1 CPU, 768MB |
| Leave | 8005 | leave_db | hr | Uvicorn (raw) | no timeout config | 1 CPU, 768MB |
| Audit | 8006 | audit_db | core | Uvicorn (raw) | no timeout config | 1 CPU, 768MB |
| Notification | 8007 | notification_db | core | Uvicorn (raw) | no timeout config | 1 CPU, 768MB |
| Gateway | 80 | — | core | Nginx | — | 0.5 CPU, 512MB |
| Frontend | 3000 | — | core | Nginx | — | 0.5 CPU, 512MB |
| PostgreSQL | 5432 | 8 databases | always | — | — | 1 CPU, 1024MB |
| RabbitMQ | 5672 | — | always | — | tmpfs mount | 1 CPU, 768MB |
| Redis | 6379 | — | always | — | AOF persistence | 0.25 CPU, 200MB |

**Total resource allocation:** 10.5 CPU cores, 8,380 MB RAM

---

## Service Dependency Map

```
                    ┌─────────────┐
                    │  PostgreSQL  │
                    │  (8 databases)│
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌────▼────┐  ┌──────▼──────┐
     │ Auth Service │ │ All 7   │  │   Alembic   │
     │ (identity)   │ │ other   │  │ (migrations)│
     │              │ │services │  └─────────────┘
     └──────┬──────┘ └────┬────┘
            │              │
     ┌──────▼──────┐      │
     │    Redis     │◀─────┘  (token blacklist validation)
     │  (blacklist) │
     └─────────────┘

     ┌──────────────────────────────────┐
     │           RabbitMQ               │
     │  (hrms_events topic exchange)    │
     └──────┬───────────────┬───────────┘
            │               │
     ┌──────▼──────┐ ┌─────▼──────┐
     │ Audit Svc   │ │ Notify Svc │
     │ (consumer)  │ │ (consumer) │
     │ wildcard #  │ │ leave.*    │
     └─────────────┘ │ employee.* │
                      └────────────┘

     ┌──────────────┐
     │    Nginx     │──▶ All services via Docker DNS
     │   Gateway    │    (resolver 127.0.0.11 valid=10s)
     └──────────────┘
```

### Critical Dependency Chains

| If This Fails | These Are Affected | Severity |
|---------------|-------------------|----------|
| PostgreSQL | ALL services (8/8) — total system failure | CRITICAL |
| Redis | Auth token validation degrades (blacklist check returns false) | HIGH |
| RabbitMQ | Audit logging stops, notifications stop, events lost | HIGH |
| Auth Service | No login, no token refresh, no user management | CRITICAL |
| Nginx Gateway | No traffic reaches any service | CRITICAL |
| Employee Service | Employee CRUD fails, but other modules still work | MEDIUM |
| Any other service | Only that module affected; rest of system operates | LOW-MEDIUM |

---

## Single Points of Failure (SPOFs)

### SPOF 1: The VPS Itself
- **What:** Entire system runs on one machine
- **Failure mode:** Hardware failure, provider outage, network partition
- **Impact:** 100% system outage, zero redundancy
- **Current mitigation:** None
- **Required mitigation:** Multi-node deployment, VPS snapshots, off-site backups

### SPOF 2: PostgreSQL (Single Instance, No Replication)
- **What:** One PostgreSQL container serving 8 databases for all services
- **Failure mode:** Container crash, data corruption, disk failure
- **Impact:** Total data unavailability — all services return errors
- **Current mitigation:** Docker volume persistence, `unless-stopped` restart policy
- **Required mitigation:** Streaming replication, automated backups, WAL archiving

### SPOF 3: Nginx Gateway (Single Entry Point)
- **What:** All HTTP traffic flows through one Nginx container
- **Failure mode:** Container crash, misconfiguration
- **Impact:** Complete frontend and API unavailability
- **Current mitigation:** `unless-stopped` restart, health check
- **Required mitigation:** Load balancer in front, or dual gateway with failover

### SPOF 4: Redis (Single Instance)
- **What:** One Redis container (100MB, no auth) for JWT blacklist
- **Failure mode:** Container crash, memory exhaustion, eviction
- **Impact:** Revoked tokens may be re-accepted (security degradation)
- **Current mitigation:** AOF persistence, `unless-stopped` restart
- **Required mitigation:** Redis Sentinel or cluster, authentication, larger memory allocation

### SPOF 5: RabbitMQ (Volatile Storage)
- **What:** One RabbitMQ container with tmpfs (in-memory only)
- **Failure mode:** Container restart, broker crash
- **Impact:** All queued events permanently lost (audit gaps, missed notifications)
- **Current mitigation:** Durable queue declarations (but moot with tmpfs)
- **Required mitigation:** Replace tmpfs with persistent volume, consider clustering

### SPOF 6: Docker Daemon
- **What:** All containers managed by single Docker daemon
- **Failure mode:** Daemon crash, upgrade, kernel panic
- **Impact:** All containers stop simultaneously
- **Current mitigation:** `unless-stopped` restart policy (auto-restart after daemon recovery)
- **Required mitigation:** Container orchestration (Kubernetes, Docker Swarm)

---

## Database Connection Budget

Each service configures: `pool_size=20, max_overflow=40` = **60 connections max per service**

| Component | Max Connections |
|-----------|----------------|
| Auth Service | 60 |
| Employee Service | 60 |
| Attendance Service | 60 |
| Students Service | 60 |
| Payroll Service | 60 |
| Leave Service | 60 |
| Audit Service | 60 |
| Notification Service | 60 |
| **Total Possible** | **480** |
| **PostgreSQL Default max_connections** | **~100** |

**Risk:** If multiple services hit max_overflow simultaneously, PostgreSQL will reject connections (`FATAL: too many connections`). This is a ticking time bomb under load.

---

## Network Topology

```
Internet → VPS Public IP → Docker Bridge Network (hrms-network)
                            │
                            ├── 172.x.x.2  gateway (nginx:80)
                            ├── 172.x.x.3  frontend (nginx:3000)
                            ├── 172.x.x.4  auth-service:8000
                            ├── 172.x.x.5  employee-service:8001
                            ├── 172.x.x.6  attendance-service:8002
                            ├── 172.x.x.7  students-service:8003
                            ├── 172.x.x.8  payroll-service:8004
                            ├── 172.x.x.9  leave-service:8005
                            ├── 172.x.x.10 audit-service:8006
                            ├── 172.x.x.11 notification-service:8007
                            ├── 172.x.x.12 hrms-db (postgres:5432)
                            ├── 172.x.x.13 rabbitmq:5672
                            └── 172.x.x.14 hrms-redis:6379
```

All services communicate over Docker's internal bridge network using container names as DNS hostnames. The DNS resolver is `127.0.0.11` with a 10-second TTL (configured in Nginx).
