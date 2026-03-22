# OphilliaHRMS — Infrastructure & Deployment Recommendation

**Date:** 2026-03-22
**Target Load:** ~50 Daily Active Users (low-traffic SaaS)
**Current State:** 8 microservices + gateway + frontend, Docker Compose orchestration

---

## 1. System Understanding

### Service Inventory & Classification

```
TIER 1 — CRITICAL (must be running 24/7)
├── Gateway (Nginx)          — single entry point, rate limiting, routing
├── Auth Service (8000)      — JWT issuance, login, refresh, RBAC
└── PostgreSQL               — all persistent data (8 databases)

TIER 2 — MEDIUM LOAD (active during business hours)
├── Employee Service (8001)  — profile CRUD, department management
├── Attendance Service (8002)— clock-in/out, geofence validation
├── Leave Service (8005)     — requests, multi-level approval, balances
└── Payroll Service (8004)   — salary calc, payroll runs (monthly burst)

TIER 3 — LOW LOAD (background / event-driven)
├── Notification Service (8007) — RabbitMQ consumer, email queue
├── Audit Service (8006)        — event consumer, append-only logs
├── Students Service (8003)     — optional module, separate tenant use-case
├── RabbitMQ                    — event broker (~100–300 events/day)
└── Redis                       — token blacklist, rate limit counters
```

### Request Patterns

| Pattern | Timing | Description |
|---------|--------|-------------|
| **Morning spike** | 8:30–9:30 AM | 40–50 clock-in requests in ~30 min |
| **Steady trickle** | 9 AM–6 PM | Leave requests, profile views, department queries |
| **Evening spike** | 5:30–6:30 PM | 40–50 clock-out requests |
| **Monthly burst** | End of month | 1 payroll run processing all 50 employees |
| **Idle** | 6 PM–8 AM | Near-zero traffic (health checks only) |

### DB Usage Patterns

| Database | Read/Write | Rows (estimated @50 users) | Growth |
|----------|-----------|---------------------------|--------|
| auth_db | 90/10 | ~100 users, ~200 tokens | Slow |
| employee_db | 85/15 | ~60 employees, ~10 departments | Slow |
| attendance_db | 40/60 | ~1,500 records/month (50 users × 30 days) | Steady |
| leave_db | 70/30 | ~200 requests/month | Slow |
| payroll_db | 30/70 | ~50 payslips/month (monthly batch) | Steady |
| notification_db | 20/80 | ~300 logs/month | Steady |
| audit_db | 5/95 | ~500–1,000 events/month | Steady |
| students_db | 80/20 | Varies by institution | Varies |

---

## 2. Load & Usage Modeling

### Assumptions

| Metric | Value | Reasoning |
|--------|-------|-----------|
| Daily Active Users | 50 | Given constraint |
| Requests per user per day | 40–60 | Login(1) + clock-in(1) + clock-out(1) + profile views(5) + leave(2) + misc(30) |
| Total requests/day | ~2,500 | 50 × 50 avg |
| Active window | 8 hours | 8:30 AM – 6:30 PM |
| Average RPS | **0.09** | 2,500 / (8 × 3600) |
| Peak concurrent users | 15–20 | Morning clock-in rush |
| Peak RPS | **2–3** | 20 users × 3 rapid requests in clock-in flow |
| Absolute max RPS (burst) | **10** | Bulk import or payroll run |
| DB connections active | 8–16 | 1–2 per service (pool_size=20 per service, but idle) |

### Reality Check

```
Your peak load of 3 RPS is what a SINGLE uvicorn worker
handles comfortably at ~50% capacity.

A Raspberry Pi 4 could serve this traffic.

Your current docker-compose allocates 7.25 vCPU and 6.5GB RAM.
Your actual usage will be ~0.3 vCPU and ~1.8GB RAM.
```

---

## 3. VPS Recommendation

### A. Architecture Decision: Single VPS

For 50 DAU, a **single VPS** is the only sensible choice.

| Option | Verdict | Why |
|--------|---------|-----|
| Single VPS | **YES** | Traffic is trivial; multi-node adds latency, cost, and ops burden |
| Multi-node | NO | Zero benefit at this scale; adds network hops and failure modes |
| Hybrid (VPS + managed DB) | NO (for now) | Managed PostgreSQL costs $15–50/mo alone — more than your entire VPS |

### B. Recommended Configuration

| Component | Minimum (works) | Recommended (comfortable) | Overkill (your spec) |
|-----------|-----------------|--------------------------|---------------------|
| **vCPU** | 2 shared | 2 dedicated | 4 dedicated |
| **RAM** | 4 GB | 8 GB | 16 GB |
| **Disk** | 40 GB NVMe | 80 GB NVMe | 100 GB NVMe |
| **Bandwidth** | 4 TB | 8 TB | Unlimited |
| **Monthly cost** | ~$4–6 | ~$7–15 | ~$20–35 |

**Verdict:** Your target spec (2 vCPU / 8 GB / 100 GB NVMe / 8 TB) is the **recommended sweet spot**. It gives breathing room for development, docker builds, and log storage without over-spending.

### C. Provider Comparison

#### Budget Tier (India-friendly, best ₹/performance)

| Provider | Plan | Spec | Price/mo | Notes |
|----------|------|------|----------|-------|
| **Hetzner CX22** | Cloud | 2 vCPU / 4 GB / 40 GB | **€3.99 (~₹370)** | Best value globally; Falkenstein/Helsinki DC |
| **Hetzner CPX21** | Cloud | 3 AMD vCPU / 4 GB / 80 GB | **€7.49 (~₹695)** | Dedicated AMD EPYC cores |
| **Hetzner CPX31** | Cloud | 4 AMD vCPU / 8 GB / 160 GB | **€14.49 (~₹1,345)** | Your exact target spec, room to grow |
| **Contabo VPS S** | VPS | 4 vCPU / 8 GB / 200 GB | **€6.99 (~₹650)** | Cheapest 8GB; slower disk I/O; India DC available |

#### Balanced Tier

| Provider | Plan | Spec | Price/mo | Notes |
|----------|------|------|----------|-------|
| **DigitalOcean** | Basic Droplet | 2 vCPU / 4 GB / 80 GB | **$24 (~₹2,000)** | Bangalore DC; good API/tooling |
| **Linode (Akamai)** | Shared 4GB | 2 vCPU / 4 GB / 80 GB | **$24 (~₹2,000)** | Mumbai DC; free backups |
| **Vultr** | Cloud Compute | 2 vCPU / 4 GB / 80 GB | **$24 (~₹2,000)** | Mumbai/Bangalore DC |

#### Premium Tier

| Provider | Plan | Spec | Price/mo | Notes |
|----------|------|------|----------|-------|
| **AWS Lightsail** | 2 vCPU / 8 GB | Fixed | **$40 (~₹3,350)** | Mumbai region; managed backups |
| **GCP e2-standard-2** | Compute | 2 vCPU / 8 GB | **~$50 (~₹4,200)** | Mumbai; free tier credits help initially |

### Final Provider Recommendation

```
PRIMARY:   Hetzner CPX31 — €14.49/mo (~₹1,345/mo)
           4 AMD vCPU / 8 GB / 160 GB NVMe / 20 TB traffic
           Location: Helsinki (lowest latency to India from EU)

RUNNER-UP: Contabo VPS S — €6.99/mo (~₹650/mo)
           4 vCPU / 8 GB / 200 GB NVMe / unlimited traffic
           Location: Bangalore, India (lowest latency)
           ⚠ Slower I/O, mixed reviews on support

IF INDIA DC REQUIRED: DigitalOcean Basic $24/mo
           Bangalore DC, great API, managed backups
```

---

## 4. Deployment Architecture

### Production Layout on Single VPS

```
┌─────────────────────────────────────────────────────────────────┐
│                    VPS: 2–4 vCPU / 8 GB RAM                     │
│                    Ubuntu 24.04 LTS                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  HOST-LEVEL NGINX (not containerized)                     │   │
│  │  • TLS termination (Let's Encrypt / Certbot)             │   │
│  │  • Static frontend files served directly                  │   │
│  │  • Reverse proxy → Docker containers                      │   │
│  │  • Rate limiting, security headers, gzip                  │   │
│  │  • RAM: ~20 MB                                            │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│  ┌────────────────────▼─────────────────────────────────────┐   │
│  │  DOCKER COMPOSE (internal network only — no exposed ports)│   │
│  │                                                           │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │   │
│  │  │ auth-service │ │ employee-svc│ │ attend-svc  │        │   │
│  │  │ :8000       │ │ :8001       │ │ :8002       │        │   │
│  │  │ ~80 MB      │ │ ~80 MB      │ │ ~80 MB      │        │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │   │
│  │                                                           │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │   │
│  │  │ leave-svc   │ │ payroll-svc │ │ students-svc│        │   │
│  │  │ :8005       │ │ :8004       │ │ :8003       │        │   │
│  │  │ ~80 MB      │ │ ~80 MB      │ │ ~80 MB      │        │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │   │
│  │                                                           │   │
│  │  ┌─────────────┐ ┌─────────────┐                         │   │
│  │  │ notif-svc   │ │ audit-svc   │                         │   │
│  │  │ :8007       │ │ :8006       │                         │   │
│  │  │ ~60 MB      │ │ ~60 MB      │                         │   │
│  │  └─────────────┘ └─────────────┘                         │   │
│  │                                                           │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │ PostgreSQL 16     │ RabbitMQ 3.12 │ Redis 7      │    │   │
│  │  │ 8 databases       │ Event broker  │ Token cache  │    │   │
│  │  │ ~300 MB           │ ~150 MB       │ ~30 MB       │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Estimated total RAM usage: ~1.5–2.0 GB (of 8 GB available)     │
│  Estimated CPU usage: ~0.2–0.5 vCPU avg, ~1.5 vCPU peak         │
│  Free headroom: ~6 GB RAM, ~2 vCPU                               │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architecture Decisions

#### 1. Host-Level Nginx (not the containerized gateway)

**Why:** Your current setup has a containerized Nginx gateway. For production on a single VPS, move Nginx to the host level:

| Aspect | Containerized Gateway | Host-Level Nginx |
|--------|----------------------|------------------|
| TLS termination | Needs cert volume mounts, renewal hacks | Native Certbot integration |
| Static files | Separate frontend container (~512 MB limit) | Serve `/dist` directly (~5 MB) |
| Restart | Docker must be running | Survives Docker restarts |
| Resource | 768 MB container limit | ~20 MB native |
| Port binding | Container port mapping | Direct bind to 80/443 |

This **eliminates 2 containers** (gateway + frontend) and saves ~1 GB of allocated memory.

#### 2. Optimized docker-compose.yml Resource Limits

Your current limits are 5–10x over-provisioned. Here are realistic limits for 50 users:

```yaml
# ACTUAL resource needs for 50 DAU
x-resource-limits-api: &api-limits
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 256M      # was 768M — a FastAPI worker idles at ~60-80 MB
      reservations:
        cpus: '0.1'
        memory: 128M

x-resource-limits-db: &db-limits
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 512M      # was 1024M — 8 small DBs with <10K rows each
      reservations:
        cpus: '0.1'
        memory: 256M

x-resource-limits-broker: &broker-limits
  deploy:
    resources:
      limits:
        cpus: '0.25'
        memory: 256M      # was 768M — <300 events/day doesn't need more
      reservations:
        cpus: '0.05'
        memory: 128M

x-resource-limits-cache: &cache-limits
  deploy:
    resources:
      limits:
        cpus: '0.1'
        memory: 64M       # was 200M — maxmemory already set to 100MB, actual ~30MB
      reservations:
        cpus: '0.05'
        memory: 32M
```

#### 3. Port Mapping — Internal Only

Stop exposing service ports to the host. Only the host Nginx needs to reach them via Docker network:

```yaml
services:
  auth-service:
    # REMOVE: ports: ["8000:8000"]
    # Services communicate via Docker DNS on hrms-network
    expose:
      - "8000"    # accessible only within Docker network
    networks:
      - hrms-network
```

**Ports to expose on the host:**

| Port | Service | Exposed To |
|------|---------|-----------|
| 80 | Host Nginx | Internet (redirects to 443) |
| 443 | Host Nginx | Internet (TLS termination) |
| 5432 | — | **BLOCKED** (no external DB access) |
| 5672/15672 | — | **BLOCKED** (no external RabbitMQ) |
| 6379 | — | **BLOCKED** (no external Redis) |

#### 4. Host Nginx Configuration

```nginx
# /etc/nginx/sites-available/ophillia-hrms

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;

# Upstream definitions (Docker containers)
upstream auth_service     { server 127.0.0.1:8000; }
upstream employee_service { server 127.0.0.1:8001; }
upstream attendance_svc   { server 127.0.0.1:8002; }
upstream students_service { server 127.0.0.1:8003; }
upstream payroll_service  { server 127.0.0.1:8004; }
upstream leave_service    { server 127.0.0.1:8005; }
upstream audit_service    { server 127.0.0.1:8006; }
upstream notif_service    { server 127.0.0.1:8007; }

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=63072000" always;

    client_max_body_size 10M;
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    # ─── FRONTEND (static files served directly) ───
    root /var/www/ophillia/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;    # SPA fallback
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # Cache static assets aggressively
    location ~* \.(js|css|png|jpg|svg|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # ─── API ROUTES ───
    location /api/v1/auth {
        limit_req zone=auth_limit burst=10 nodelay;
        proxy_pass http://auth_service;
        include proxy_params;
    }

    location /api/v1/employees { proxy_pass http://employee_service; include proxy_params; }
    location /api/v1/departments { proxy_pass http://employee_service; include proxy_params; }
    location /api/v1/attendance { proxy_pass http://attendance_svc; include proxy_params; }
    location /api/v1/students { proxy_pass http://students_service; include proxy_params; }
    location /api/v1/classes { proxy_pass http://students_service; include proxy_params; }
    location /api/v1/payroll { proxy_pass http://payroll_service; include proxy_params; }
    location /api/v1/salary { proxy_pass http://payroll_service; include proxy_params; }
    location /api/v1/leave { proxy_pass http://leave_service; include proxy_params; }
    location /api/v1/audit { proxy_pass http://audit_service; include proxy_params; }
    location /api/v1/notifications { proxy_pass http://notif_service; include proxy_params; }

    # Health check endpoint
    location /health {
        return 200 '{"status":"ok"}';
        add_header Content-Type application/json;
    }
}
```

---

## 5. Cost Optimization Strategy

### What You're Over-Spending On (Current vs Optimized)

| Item | Current (docker-compose limits) | Optimized | Savings |
|------|-------------------------------|-----------|---------|
| API services (8×) | 8 × 768 MB = **6,144 MB** | 8 × 256 MB = **2,048 MB** | **67% RAM** |
| PostgreSQL | 1,024 MB | 512 MB | **50% RAM** |
| RabbitMQ | 768 MB | 256 MB | **67% RAM** |
| Redis | 200 MB | 64 MB | **68% RAM** |
| Frontend container | 512 MB | **0 MB** (static files) | **100%** |
| Gateway container | 768 MB | **0 MB** (host nginx) | **100%** |
| **Total allocated** | **~9.4 GB** | **~2.9 GB** | **69% reduction** |

### 7 Specific Cost Optimizations

#### 1. Serve frontend as static files — Save ~$0 but free 1 container + 512 MB

The frontend is already built to `/dist` as static HTML/JS/CSS. Serving it from a container running nginx inside Docker is pointless.

```bash
# Build once, deploy static files
cd frontend-tailless-ophillia-hrms-vue
npm run build
cp -r dist/ /var/www/ophillia/dist/
```

#### 2. Keep database-per-service but use a single PostgreSQL instance (already done)

You already share one PostgreSQL instance with 8 logical databases. This is correct for 50 users. Do NOT split into 8 PostgreSQL containers.

#### 3. Switch RabbitMQ from tmpfs to volume (free fix, prevents data loss)

```yaml
rabbitmq:
  volumes:
    - rabbitmq-data:/var/lib/rabbitmq    # REPLACE tmpfs
```

#### 4. Consider dropping RabbitMQ entirely (most aggressive cost saving)

At 50 users generating ~300 events/day, you could replace RabbitMQ with a simple PostgreSQL-based event table + polling:

| Approach | RAM | Complexity | Verdict |
|----------|-----|-----------|---------|
| Keep RabbitMQ | +256 MB | Already built | **Keep it** — the 256 MB is worth avoiding a rewrite |
| PostgreSQL event table | +0 MB | Requires rewriting all publishers/consumers | Not worth it |

#### 5. Use Alpine-based Python images (already doing this — good)

Your Dockerfiles already use `python:3.11-slim` with multi-stage builds. The resulting images are ~150–200 MB each.

#### 6. Reduce uvicorn workers to 1 (already done)

All services run with 1 worker. Correct for this load. Adding workers costs ~60 MB each for zero benefit.

#### 7. Use swap for safety (free insurance)

```bash
# Add 2 GB swap on VPS — catches OOM situations
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### What NOT to Do at 50 Users

| Anti-Pattern | Why It's Wrong | Cost |
|-------------|---------------|------|
| Managed PostgreSQL (RDS/Cloud SQL) | $15–50/mo for what a $5 VPS handles | 3–10x overspend |
| Kubernetes / K3s | Orchestrator overhead exceeds your workload | ~500 MB RAM wasted |
| Multiple VPS nodes | Network latency > compute savings | 2x cost minimum |
| CDN for API | Your API serves JSON at 3 RPS peak | $0 but adds complexity |
| Redis Cluster | You store <1,000 keys | Pointless |
| Read replicas | Your DB handles <1 query/second | Adds lag, zero benefit |
| CI/CD runners on separate machines | GitHub Actions free tier is sufficient | $0 if you use GH Actions |
| Monitoring stack (Prometheus+Grafana+Loki) | 3 services consuming more RAM than your app | +1–2 GB overhead |

---

## 6. Performance Optimization

### 6.1 Caching Strategy

```
LAYER 1: Browser Cache (free, already available)
─────────────────────────────────────────────────
• Static assets (JS/CSS/images): Cache-Control: max-age=2592000, immutable
• API responses: Cache-Control: private, max-age=0 (no browser cache for API)

LAYER 2: Nginx Proxy Cache (free, add to host nginx)
─────────────────────────────────────────────────────
• Cache GET /api/v1/employees (list) — 30s TTL
• Cache GET /api/v1/departments — 60s TTL
• Cache GET /api/v1/leave-types — 300s TTL (rarely changes)
• Cache GET /api/v1/attendance-policies — 300s TTL
• Cache GET /api/v1/salary/structures — 300s TTL
• Do NOT cache: POST, PATCH, DELETE, /auth/*, /attendance/clock-*

LAYER 3: Redis (already deployed, underutilized)
─────────────────────────────────────────────────
Currently used for: token blacklist only
Add these:
• Employee lookup cache (2 min TTL) — used by attendance, leave, payroll
• Leave type list (10 min TTL) — queried on every leave request
• Attendance policy resolution (5 min TTL) — queried on every clock-in
• Holiday list (1 hour TTL) — queried for business day calculation
```

**Nginx proxy cache config:**

```nginx
# Add to http {} block
proxy_cache_path /var/cache/nginx/api levels=1:2 keys_zone=api_cache:10m
                 max_size=100m inactive=5m;

# Add to cacheable locations
location /api/v1/departments {
    proxy_cache api_cache;
    proxy_cache_valid 200 60s;
    proxy_cache_key "$scheme$request_method$host$request_uri$http_authorization";
    add_header X-Cache-Status $upstream_cache_status;
    proxy_pass http://employee_service;
    include proxy_params;
}
```

### 6.2 Database Indexing Strategy

Your tables are tiny at 50 users, but these indexes prevent problems as you grow:

```sql
-- attendance_db: most-queried table
CREATE INDEX IF NOT EXISTS idx_attendance_employee_date
    ON attendance_records (employee_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_attendance_company_date
    ON attendance_records (company_id, date DESC);

-- leave_db
CREATE INDEX IF NOT EXISTS idx_leave_requests_employee_status
    ON leave_requests (employee_id, status);
CREATE INDEX IF NOT EXISTS idx_leave_requests_company_status
    ON leave_requests (company_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leave_balances_employee_year
    ON leave_balances (employee_id, year);

-- payroll_db
CREATE INDEX IF NOT EXISTS idx_payslips_employee_period
    ON payslips (employee_id, period_start DESC);
CREATE INDEX IF NOT EXISTS idx_payroll_runs_company_period
    ON payroll_runs (company_id, period_start, period_end);

-- audit_db (grows fastest — will have tens of thousands of rows)
CREATE INDEX IF NOT EXISTS idx_audit_logs_company_created
    ON audit_logs (company_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type
    ON audit_logs (event_type, created_at DESC);

-- auth_db
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_company ON users (company_id);
```

### 6.3 API Response Optimization

| Optimization | Where | Impact |
|-------------|-------|--------|
| Pagination (already exists) | All list endpoints | Prevents full-table scans |
| Field selection | `GET /employees?fields=id,name,email` | Reduce payload 80% for dropdowns |
| Compression | Nginx `gzip on` | Reduce JSON payloads ~70% |
| Connection pooling | Already configured (pool_size=20) | Over-provisioned — reduce to pool_size=5 |

**Reduce connection pool (saves ~15 idle connections to PostgreSQL):**

```python
# Each service currently: pool_size=20, max_overflow=40
# At 50 users with 1 worker per service: pool_size=5 is sufficient
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,         # was 20
    max_overflow=10,     # was 40
    pool_recycle=3600,
    pool_pre_ping=True,
)
```

### 6.4 Rate Limiting (already configured — no changes needed)

Current limits are appropriate:
- Auth login: 5 req/s per IP (good)
- General API: 30 req/s per IP (generous for 50 users, fine)

---

## 7. Scaling Strategy

### Stage 1: 0–100 Users (Current → 6 months)

**Architecture:** Single VPS, everything on one machine.

```
Cost: €7–15/mo
Infra: 1 VPS (2–4 vCPU, 4–8 GB RAM)
DB: Single PostgreSQL instance (8 databases)
Queue: Single RabbitMQ
Cache: Single Redis
Monitoring: Docker logs + simple uptime check (UptimeRobot free tier)
Backups: Daily pg_dump → compressed file → offsite (S3/Backblaze B2)
```

**Actions:**
1. Deploy on Hetzner CPX21 or CPX31
2. Set up host-level Nginx with TLS (Let's Encrypt)
3. Lower Docker resource limits to optimized values
4. Set up daily automated backups
5. Add 2 GB swap
6. Set up UFW firewall (allow only 80, 443, 22)

**Backup script (run daily via cron):**

```bash
#!/bin/bash
# /opt/hrms/backup.sh
BACKUP_DIR="/opt/hrms/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Dump all databases
docker exec hrms-db pg_dumpall -U postgres | gzip > "$BACKUP_DIR/hrms_full_$DATE.sql.gz"

# Keep only last 7 days locally
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

# Upload to Backblaze B2 ($0.005/GB — ~$0.01/mo for your data)
# b2 upload-file your-bucket "$BACKUP_DIR/hrms_full_$DATE.sql.gz" "backups/hrms_full_$DATE.sql.gz"
```

**Upgrade trigger:** Move to Stage 2 when ANY of these hit:
- Average RAM usage > 70% sustained (>5.6 GB on 8 GB VPS)
- CPU usage > 60% sustained during peak hours
- Database size > 10 GB
- P95 API latency > 500 ms during peak

---

### Stage 2: 100–1,000 Users (6–18 months)

**Architecture:** Single VPS + managed database OR second VPS for DB.

```
WHAT BREAKS FIRST AT 100–1K USERS:
1. PostgreSQL — connection count, I/O, backup window
2. Payroll runs — processing 1,000 payslips takes real CPU time
3. Audit log table — grows to millions of rows
4. Disk space — audit logs + attendance records accumulate
```

**Step-by-step scaling path:**

```
Step 1 (at ~150 users): Upgrade VPS
  └── Hetzner CPX41: 8 vCPU / 16 GB / 240 GB — €27.49/mo

Step 2 (at ~300 users): Externalize PostgreSQL
  └── Option A: Second VPS for PostgreSQL only (~€7/mo)
  └── Option B: Managed DB (Hetzner: ~€15/mo, DO: ~$15/mo)
  └── Add read replica for reporting queries

Step 3 (at ~500 users): Add monitoring
  └── Grafana Cloud free tier (10K metrics, 50 GB logs)
  └── Or lightweight: VictoriaMetrics + Grafana (uses 200 MB vs Prometheus 1 GB+)

Step 4 (at ~700 users): Increase workers
  └── gunicorn -w 2 for auth, employee, attendance services
  └── Leave others at 1 worker

Step 5 (at ~1K users): Consider service separation
  └── Audit service → separate VPS (heavy writes, growing data)
  └── Payroll → separate VPS (monthly CPU burst)
```

**Cost at 1K users: ~€35–55/mo ($40–60/mo)**

---

### Stage 3: 1,000+ Users (18+ months)

**Architecture:** Multi-node with load balancer.

```
┌──────────────────────────────────────────────────┐
│                LOAD BALANCER                      │
│        (Hetzner LB: €5.49/mo or Nginx)           │
└────────┬──────────────────────┬──────────────────┘
         │                      │
┌────────▼────────┐   ┌────────▼────────┐
│  APP SERVER 1    │   │  APP SERVER 2    │
│  Gateway + Auth  │   │  Gateway + Auth  │
│  Employee        │   │  Employee        │
│  Attendance      │   │  Attendance      │
│  Leave           │   │  Leave           │
└────────┬────────┘   └────────┬────────┘
         │                      │
         └──────────┬───────────┘
                    │
    ┌───────────────▼───────────────┐
    │  DATA TIER (separate VPS)      │
    │  PostgreSQL (primary + replica)│
    │  RabbitMQ (2-node cluster)    │
    │  Redis (single, replicated)   │
    └───────────────────────────────┘
    │
    │  BACKGROUND TIER (separate VPS)
    │  Audit Service (heavy writes)
    │  Payroll Service (monthly burst)
    │  Notification Service
    └───────────────────────────────
```

**Cost at 5K users: ~€80–120/mo**

**When to consider Kubernetes:** Only at 5,000+ users with multiple tenants, where you need auto-scaling, rolling deployments, and multi-region. Until then, Docker Compose + manual scaling is cheaper and simpler.

---

## 8. Risks & Bottlenecks

### Single Points of Failure

| Component | SPOF? | Impact | Mitigation |
|-----------|-------|--------|-----------|
| **VPS itself** | YES | Total outage | Daily backups; documented 30-min recovery procedure |
| **PostgreSQL** | YES | All data inaccessible | Daily pg_dump to offsite storage |
| **RabbitMQ (tmpfs!)** | YES | Events lost on restart | **FIX NOW:** Switch to Docker volume |
| **Redis** | YES (fail-open) | Revoked tokens temporarily valid | Acceptable risk at 50 users; add persistence |
| **Host Nginx** | YES | All traffic blocked | `systemctl enable nginx`; auto-restart |
| **Docker daemon** | YES | All services down | `systemctl enable docker`; auto-restart |

### CPU Bottlenecks

| Risk | When | Severity |
|------|------|----------|
| Argon2id password hashing | Multiple concurrent logins | LOW — 1 login at a time at 50 users |
| Payroll run (50 employees) | Monthly | LOW — <5 seconds for 50 payslips |
| AES-256-GCM encryption | Employee bulk import | LOW — only during bulk operations |
| Docker image builds | Deployment | MEDIUM — builds consume all CPU for 2–3 min; schedule deploys off-peak |

### Memory Bottlenecks

| Risk | When | Severity |
|------|------|----------|
| All 8 services starting simultaneously | Server reboot | MEDIUM — stagger with `depends_on` + `start_period` |
| PostgreSQL shared_buffers | Under load | LOW — default 128 MB is fine for <10K rows |
| RabbitMQ queue buildup | If consumers crash | LOW — <300 events/day; DLQ catches failures |
| Docker image layers in cache | After many builds | LOW — periodic `docker system prune` |

### DB Contention Risks

| Risk | When | Severity |
|------|------|----------|
| 8 services × pool_size=20 = 160 potential connections | Never (at 50 users) | ZERO — reduce pool_size to 5 |
| Audit log table growth | Over months | LOW — partition by month at 1M+ rows |
| Lock contention on payroll_runs | Concurrent payroll runs | LOW — idempotent design prevents duplicates |

---

## 9. Final Recommendation

### Exact Plan to Start With

```
┌───────────────────────────────────────────────┐
│  RECOMMENDED: Hetzner CPX31                    │
│                                                │
│  Spec:  4 AMD vCPU / 8 GB RAM / 160 GB NVMe   │
│  OS:    Ubuntu 24.04 LTS                       │
│  Cost:  €14.49/mo (~₹1,345/mo or ~$16/mo)     │
│  DC:    Helsinki or Falkenstein                 │
│  Traffic: 20 TB/mo (more than enough)          │
└───────────────────────────────────────────────┘
```

### Monthly Cost Breakdown

| Item | Cost | Notes |
|------|------|-------|
| VPS (Hetzner CPX31) | **€14.49** | 4 vCPU / 8 GB / 160 GB |
| Domain name | ~€1/mo | amortized annual cost |
| TLS certificate | **€0** | Let's Encrypt (free, auto-renewal) |
| Offsite backup (Backblaze B2) | **~€0.05** | 1 GB of compressed backups |
| Uptime monitoring | **€0** | UptimeRobot free tier (50 monitors) |
| Email sending (future) | **€0** | SendGrid free tier (100 emails/day) |
| **TOTAL** | **~€16/mo (~₹1,500/mo)** | |

### Budget Alternative

```
┌───────────────────────────────────────────────┐
│  BUDGET: Hetzner CX22                          │
│                                                │
│  Spec:  2 shared vCPU / 4 GB RAM / 40 GB       │
│  Cost:  €3.99/mo (~₹370/mo or ~$4.50/mo)       │
│  Note:  Tight but works for 50 users            │
│         Upgrade when RAM hits 3 GB usage         │
└───────────────────────────────────────────────┘
```

### Upgrade Trigger Conditions

| Trigger | Metric | Action |
|---------|--------|--------|
| RAM > 70% sustained | `free -h` shows <2.4 GB free on 8 GB | Upgrade to CPX41 (16 GB) |
| CPU > 60% during peak | `top` shows >60% for >30 min | Upgrade to CPX41 (8 vCPU) |
| Disk > 75% | `df -h` shows >120 GB used | Upgrade to larger disk or add volume |
| DB size > 10 GB | `SELECT pg_database_size()` | Externalize PostgreSQL |
| P95 latency > 500 ms | Application monitoring | Add workers (gunicorn -w 2) |
| Users > 200 | Business metric | Start Stage 2 planning |

### Day-1 Deployment Checklist

```
INFRASTRUCTURE
[ ] Provision Hetzner CPX31
[ ] Set hostname, timezone, locale
[ ] Create non-root user with SSH key
[ ] Disable password SSH login
[ ] Install Docker + Docker Compose v2
[ ] Install Nginx + Certbot on host
[ ] Configure UFW: allow 22, 80, 443 only
[ ] Add 2 GB swap
[ ] Set up unattended-upgrades for security patches

SECURITY (from audit Phase 0)
[ ] Generate new JWT RSA keys
[ ] Generate strong PostgreSQL password
[ ] Generate strong RabbitMQ credentials (replace guest/guest)
[ ] Add Redis AUTH password
[ ] Put all secrets in /opt/hrms/.env (not in Git)
[ ] Set up TLS with Let's Encrypt

DEPLOYMENT
[ ] Clone repo to /opt/hrms/
[ ] Build frontend: npm run build → /var/www/ophillia/dist/
[ ] Configure host Nginx (TLS + static + reverse proxy)
[ ] Update docker-compose.yml with optimized resource limits
[ ] Remove port exposures (use expose: instead of ports:)
[ ] Switch RabbitMQ from tmpfs to volume
[ ] docker compose --profile core --profile hr up -d
[ ] Verify all health checks pass

OPERATIONS
[ ] Set up daily backup cron (pg_dump → Backblaze B2)
[ ] Set up UptimeRobot monitoring (HTTPS + /health endpoint)
[ ] Set up Docker auto-restart (restart: unless-stopped — already done)
[ ] Test full recovery from backup (restore to fresh VPS)
[ ] Document recovery procedure
```

---

## Summary

| Question | Answer |
|----------|--------|
| **Best VPS?** | Hetzner CPX31 — 4 vCPU / 8 GB / 160 GB — €14.49/mo |
| **Single or multi-node?** | Single VPS until 200+ users |
| **What to optimize first?** | Lower Docker limits, host-level Nginx, TLS, backups |
| **Biggest risk?** | RabbitMQ tmpfs (data loss) and secrets in Git |
| **When to scale?** | RAM >70% or users >200 |
| **Total monthly cost?** | **~₹1,500/mo (~$16/mo)** |
