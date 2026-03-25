# 09 — High Availability Improvements & Risk Matrix

## Current vs Target Architecture

### Current: Single VPS, Single Everything

```
Internet → [VPS] → Nginx → Services → PostgreSQL (1) → Disk
                                      → Redis (1)
                                      → RabbitMQ (1, tmpfs)
```

**Availability estimate:** ~99.0% (approximately 87 hours downtime/year)

### Target: Redundant, Multi-Node

```
Internet → [Load Balancer] → VPS-1 → Services ──┐
                            → VPS-2 → Services ──┤
                                                   ├──→ Managed PostgreSQL (Primary + Replica)
                                                   ├──→ Redis Sentinel (3 nodes)
                                                   └──→ RabbitMQ Cluster (3 nodes)
```

**Availability target:** ~99.9% (approximately 8.7 hours downtime/year)

---

## Improvement Roadmap

### Phase 1: Quick Wins (No Architecture Change)

| Improvement | Effort | Impact | Details |
|-------------|--------|--------|---------|
| Fix RabbitMQ persistence | 5 min | HIGH | Replace tmpfs with Docker volume |
| Add Redis authentication | 15 min | HIGH | Add `--requirepass` to Redis command |
| Fix PostgreSQL max_connections | 5 min | HIGH | Set to 500 to match pool budget |
| Standardize entrypoints to Gunicorn | 2 hrs | MEDIUM | All services use Gunicorn with graceful-timeout |
| Add stop_grace_period to compose | 5 min | MEDIUM | `stop_grace_period: 20s` for all services |
| Implement automated pg_dump backup | 1 hr | CRITICAL | Daily cron job (see 07-backup-dr.md) |
| Add external uptime monitoring | 30 min | HIGH | UptimeRobot/Pingdom on /health |
| Fix health checks to return 503 when degraded | 1 hr | MEDIUM | Return non-200 when DB/Redis down |

### Phase 2: Observability

| Improvement | Effort | Impact | Details |
|-------------|--------|--------|---------|
| Deploy Prometheus + Grafana | 2 hrs | HIGH | Docker Compose monitoring profile |
| Add Node Exporter + cAdvisor | 30 min | HIGH | Host and container metrics |
| Add PostgreSQL Exporter | 30 min | HIGH | DB connection, query, and lock metrics |
| Deploy Loki + Promtail | 1 hr | MEDIUM | Centralized log aggregation |
| Configure alerting rules | 2 hrs | HIGH | Slack/email alerts for critical conditions |
| Add application /metrics endpoints | 4 hrs | MEDIUM | Request count, latency histograms per service |

### Phase 3: Resilience Patterns

| Improvement | Effort | Impact | Details |
|-------------|--------|--------|---------|
| Add circuit breakers | 4 hrs | HIGH | pybreaker or tenacity for inter-service calls |
| Add idempotency keys | 8 hrs | HIGH | Prevent duplicate writes on retry |
| Implement outbox pattern | 16 hrs | HIGH | Fix dual-write problem (DB + RabbitMQ) |
| Add statement_timeout to PostgreSQL | 5 min | MEDIUM | `SET statement_timeout = '30s'` |
| Add query timeouts in application | 2 hrs | MEDIUM | Per-query timeout in SQLAlchemy |
| Implement connection pool monitoring | 2 hrs | MEDIUM | Log pool checkout times, overflow events |

### Phase 4: Multi-Node (Infrastructure Change)

| Improvement | Effort | Impact | Details |
|-------------|--------|--------|---------|
| Add load balancer (HAProxy/Traefik) | 4 hrs | HIGH | Remove Nginx SPOF |
| PostgreSQL replication (streaming) | 8 hrs | CRITICAL | Primary + read replica |
| OR: Migrate to managed DB | 2 hrs | CRITICAL | AWS RDS, DigitalOcean Managed PG |
| Redis Sentinel or managed Redis | 4 hrs | HIGH | Auto-failover for cache |
| RabbitMQ clustering (3-node) | 8 hrs | MEDIUM | Message broker redundancy |
| Multi-VPS service deployment | 16 hrs | HIGH | Services distributed across nodes |
| Blue-green deployment pipeline | 8 hrs | MEDIUM | Zero-downtime deployments |

### Phase 5: Container Orchestration

| Improvement | Effort | Impact | Details |
|-------------|--------|--------|---------|
| Migrate to Kubernetes | 40 hrs | HIGH | Full orchestration, auto-scaling, self-healing |
| OR: Docker Swarm mode | 16 hrs | MEDIUM | Simpler multi-node Docker |
| Horizontal Pod Autoscaling | 4 hrs | MEDIUM | Scale services based on CPU/memory |
| Rolling update strategy | 2 hrs | MEDIUM | Zero-downtime deploys via K8s |
| Pod Disruption Budgets | 1 hr | MEDIUM | Ensure minimum replicas during maintenance |

---

## Deployment Strategies

### Current: Recreate (Big Bang)
```
docker-compose up --build -d
→ Stops old containers
→ Builds new images
→ Starts new containers
→ Brief outage during transition
```

### Recommended: Rolling Update (Per-Service)
```bash
# Update one service at a time
docker-compose up --build -d --no-deps auth-service
# Wait for health check
sleep 60
# Verify
curl -s http://localhost:8000/health | jq .
# Continue with next service
docker-compose up --build -d --no-deps employee-service
```

### Future: Blue-Green
```
Active:  VPS-1 (blue)  → Load Balancer → Users
Standby: VPS-2 (green) → (idle)

Deploy to green:
  1. Deploy new code to VPS-2
  2. Run migrations on VPS-2
  3. Health check VPS-2
  4. Switch Load Balancer: Users → VPS-2 (green)
  5. VPS-1 (blue) becomes standby
  6. Rollback: Switch LB back to VPS-1
```

---

## Risk Matrix

| # | Scenario | Probability | Impact | Severity | Current Mitigation | Required Mitigation |
|---|----------|------------|--------|----------|-------------------|-------------------|
| 1 | VPS hardware failure | Low | Critical | **CRITICAL** | None | Off-site backups, multi-node |
| 2 | PostgreSQL crash | Low | Critical | **CRITICAL** | Auto-restart, WAL | Replication, automated backup |
| 3 | Disk full | Medium | Critical | **CRITICAL** | None | Disk monitoring, log rotation |
| 4 | RabbitMQ restart (event loss) | High | High | **CRITICAL** | None (tmpfs!) | Persistent volume |
| 5 | Bad deployment | Medium | High | **HIGH** | Manual rollback | Blue-green, health gates |
| 6 | Redis OOM / eviction | Medium | High | **HIGH** | LRU eviction | Larger memory, noeviction for blacklist |
| 7 | Auth service crash | Low | High | **HIGH** | Auto-restart (30-60s) | Multiple replicas |
| 8 | DB connection exhaustion | Medium | High | **HIGH** | Pool limits | Fix max_connections, reduce pool |
| 9 | Container OOMKilled | Medium | Medium | **HIGH** | Auto-restart | Memory monitoring, leak detection |
| 10 | Nginx gateway crash | Low | Critical | **HIGH** | Auto-restart (5-10s) | Dual gateway, LB |
| 11 | Network outage | Low | High | **MEDIUM** | None | External monitoring |
| 12 | Schema migration failure | Low | High | **MEDIUM** | Alembic versioning | Pre-deploy backup, migration testing |
| 13 | Partial deployment | Medium | Medium | **MEDIUM** | None | Atomic deploy script |
| 14 | Redis crash | Low | Medium | **MEDIUM** | Auto-restart, AOF | Sentinel |
| 15 | CPU exhaustion | Low | Medium | **MEDIUM** | Docker cgroup limits | Monitoring + alerting |
| 16 | Docker daemon crash | Very Low | Critical | **MEDIUM** | unless-stopped | Orchestration (K8s) |
| 17 | Slow query cascade | Medium | Medium | **MEDIUM** | Nginx 10s timeout | statement_timeout, query monitoring |
| 18 | Data corruption | Very Low | Critical | **MEDIUM** | WAL checksums | Automated backup verification |
| 19 | Accidental data deletion | Low | High | **MEDIUM** | Soft-delete (companies) | Automated backups, audit trail |
| 20 | Single service crash | Medium | Low | **LOW** | Auto-restart | Monitoring |

### Severity Calculation

```
Severity = Probability × Impact

            │ Low Impact  │ Medium Impact │ High Impact  │ Critical Impact │
────────────┼─────────────┼───────────────┼──────────────┼─────────────────┤
Very Low    │ LOW         │ LOW           │ MEDIUM       │ MEDIUM          │
Low         │ LOW         │ MEDIUM        │ HIGH         │ CRITICAL        │
Medium      │ LOW         │ MEDIUM/HIGH   │ HIGH         │ CRITICAL        │
High        │ MEDIUM      │ HIGH          │ CRITICAL     │ CRITICAL        │
```

---

## Priority Action Items

### Do This Week (Critical)
1. Replace RabbitMQ tmpfs with persistent volume
2. Implement daily PostgreSQL backup script
3. Set up external uptime monitoring
4. Set PostgreSQL `max_connections = 500`

### Do This Month (High)
5. Add Redis authentication
6. Standardize all entrypoints to Gunicorn
7. Deploy Prometheus + Grafana monitoring stack
8. Add disk usage alerting
9. Fix health checks to return 503 when degraded

### Do This Quarter (Medium)
10. Add circuit breakers for inter-service calls
11. Implement idempotency keys
12. Add statement_timeout to PostgreSQL
13. Evaluate managed database service
14. Plan multi-node deployment
