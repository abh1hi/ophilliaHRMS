# 08 — Monitoring & Detection Strategy

## Current Monitoring State

| What | Current Method | Sufficient? |
|------|---------------|-------------|
| Service health | Docker health checks (every 30s) | Partial — checks DB+Redis but returns 200 even when degraded |
| Container status | Docker daemon (`docker ps`) | Manual only — no alerting |
| Application errors | Structured JSON logs (stdout) | Logs exist but no aggregation or alerting |
| API latency | Nginx access log (JSON with request_time) | Logged but not aggregated or alerted on |
| Database performance | None | NO MONITORING |
| Disk usage | None | NO MONITORING |
| CPU / RAM | Docker resource limits only | Limits exist but no visibility into usage |
| Request tracing | X-Request-ID header propagated | Good — but no centralized trace viewer |
| RabbitMQ | Management UI (:15672) | Available but not monitored |
| Audit trail | Audit service (all events) | Good for business events, not for infrastructure |

---

## Recommended Monitoring Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Monitoring Stack                       │
│                                                           │
│  ┌───────────┐   ┌──────────┐   ┌────────────────────┐ │
│  │ Prometheus │──▶│ Grafana  │──▶│ Alert Manager      │ │
│  │ (metrics)  │   │ (viz)    │   │ (Slack/Email/PD)   │ │
│  └─────┬─────┘   └──────────┘   └────────────────────┘ │
│        │                                                  │
│  ┌─────▼──────────────────────────────────────────────┐ │
│  │ Scrape targets:                                     │ │
│  │  - Node Exporter (host CPU/RAM/disk)               │ │
│  │  - cAdvisor (container metrics)                     │ │
│  │  - PostgreSQL Exporter (DB performance)             │ │
│  │  - Redis Exporter (cache metrics)                   │ │
│  │  - RabbitMQ built-in Prometheus endpoint            │ │
│  │  - Application /metrics endpoints                   │ │
│  │  - Nginx stub_status                               │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌───────────┐   ┌──────────┐                           │
│  │   Loki    │──▶│ Grafana  │  (log aggregation)       │
│  │ (logs)    │   │ (search) │                           │
│  └─────┬─────┘   └──────────┘                           │
│        │                                                  │
│  ┌─────▼──────────────────────────────────────────────┐ │
│  │ Log sources: Docker JSON log driver → Promtail     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Uptime Monitor (external):                         │  │
│  │  UptimeRobot / Pingdom → checks /health from      │  │
│  │  outside the VPS every 60s                         │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## What to Monitor

### Host Level (Node Exporter)

| Metric | Warning Threshold | Critical Threshold | Alert |
|--------|------------------|-------------------|-------|
| CPU utilization | > 70% for 5min | > 90% for 2min | Slack + Email |
| RAM utilization | > 80% | > 95% | Slack + Email |
| Disk usage | > 80% | > 90% | Slack + Email |
| Disk I/O wait | > 30% for 5min | > 50% for 2min | Slack |
| Network errors | > 0 for 5min | > 100/min | Slack |
| Load average | > 2× CPU cores | > 4× CPU cores | Slack |

### Container Level (cAdvisor)

| Metric | Warning | Critical | Alert |
|--------|---------|----------|-------|
| Container restart count | > 2 in 10min | > 5 in 10min | Slack + Email |
| Container CPU vs limit | > 80% limit | > 95% limit | Slack |
| Container memory vs limit | > 80% of 768MB | > 95% of 768MB | Slack + Email |
| Container health status | `unhealthy` for > 2min | `unhealthy` for > 5min | Slack + Email |
| Container exit code 137 | Any occurrence | — | Slack (OOMKilled) |

### Application Level (Custom /metrics)

| Metric | Warning | Critical | Alert |
|--------|---------|----------|-------|
| Request latency P95 | > 1s | > 5s | Slack |
| Request latency P99 | > 3s | > 10s | Slack + Email |
| HTTP 5xx rate | > 1% of requests | > 5% of requests | Slack + Email |
| HTTP 429 rate | > 10/min | > 100/min | Slack |
| Active DB connections | > 40 (67% of pool) | > 55 (92% of pool) | Slack + Email |

### Database Level (PostgreSQL Exporter)

| Metric | Warning | Critical | Alert |
|--------|---------|----------|-------|
| Active connections | > 60 | > 90 (of 100 default max) | Slack + Email |
| Deadlocks | Any occurrence | > 5/hour | Slack |
| Slow queries (> 1s) | > 10/hour | > 50/hour | Slack |
| Replication lag | > 1s (if replicated) | > 10s | Slack + Email |
| Database size growth | > 10% per day | > 25% per day | Slack |
| Transaction rollback rate | > 5% | > 20% | Slack |
| Cache hit ratio | < 95% | < 80% | Slack |

### Redis Level (Redis Exporter)

| Metric | Warning | Critical | Alert |
|--------|---------|----------|-------|
| Memory usage | > 70MB (of 100MB) | > 90MB | Slack + Email |
| Evicted keys | > 0 | > 100/hour | Slack + Email |
| Connected clients | > 50 | > 100 | Slack |
| Keys count | > 50K | > 100K | Slack |

### RabbitMQ Level (Built-in Prometheus)

| Metric | Warning | Critical | Alert |
|--------|---------|----------|-------|
| Queue depth (audit_queue) | > 1000 | > 10000 | Slack + Email |
| Queue depth (notification_queue) | > 500 | > 5000 | Slack + Email |
| DLQ depth (any) | > 0 | > 100 | Slack + Email |
| Consumer count | < expected (3) | 0 | Slack + Email |
| Message publish rate drop | > 50% decline | > 90% decline | Slack |

---

## Docker Compose Addition for Monitoring

```yaml
# Add to docker-compose.yml

  prometheus:
    image: prom/prometheus:latest
    container_name: hrms-prometheus
    profiles: ["monitoring"]
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - hrms-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: hrms-grafana
    profiles: ["monitoring"]
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    networks:
      - hrms-network
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: hrms-node-exporter
    profiles: ["monitoring"]
    pid: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
    networks:
      - hrms-network
    restart: unless-stopped

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: hrms-cadvisor
    profiles: ["monitoring"]
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    networks:
      - hrms-network
    restart: unless-stopped

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: hrms-pg-exporter
    profiles: ["monitoring"]
    environment:
      DATA_SOURCE_NAME: "postgresql://postgres:${POSTGRES_PASSWORD}@hrms-db:5432/postgres?sslmode=disable"
    networks:
      - hrms-network
    restart: unless-stopped

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: hrms-redis-exporter
    profiles: ["monitoring"]
    environment:
      REDIS_ADDR: "redis://hrms-redis:6379"
    networks:
      - hrms-network
    restart: unless-stopped

  loki:
    image: grafana/loki:latest
    container_name: hrms-loki
    profiles: ["monitoring"]
    volumes:
      - loki-data:/loki
    ports:
      - "3100:3100"
    networks:
      - hrms-network
    restart: unless-stopped

  promtail:
    image: grafana/promtail:latest
    container_name: hrms-promtail
    profiles: ["monitoring"]
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./infra/promtail/config.yml:/etc/promtail/config.yml
    networks:
      - hrms-network
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
  loki-data:
```

**Usage:** `docker compose --profile core --profile hr --profile monitoring up -d`

---

## Alerting Rules (Prometheus)

```yaml
# infra/prometheus/alerts.yml
groups:
  - name: hrms_critical
    rules:
      - alert: ServiceDown
        expr: up{job=~"hrms-.*"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate > 5% on {{ $labels.service }}"

      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL connections at {{ $value }}/100"

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 20
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Disk space below 20%"

      - alert: ContainerOOMKilled
        expr: increase(container_oom_events_total[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Container {{ $labels.name }} OOMKilled"

      - alert: RabbitMQDLQNotEmpty
        expr: rabbitmq_queue_messages{queue=~".*dlq.*"} > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Dead letter queue has {{ $value }} messages"

      - alert: RedisEviction
        expr: increase(redis_evicted_keys_total[1h]) > 0
        labels:
          severity: warning
        annotations:
          summary: "Redis evicting keys — blacklist may be compromised"
```
