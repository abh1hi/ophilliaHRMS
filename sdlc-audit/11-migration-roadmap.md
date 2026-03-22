# Migration Roadmap: Current → Target Architecture

---

## Current State Summary

- 8 microservices + Nginx gateway
- Docker Compose orchestration
- Single PostgreSQL instance (8 databases)
- Single RabbitMQ (tmpfs — volatile)
- Single Redis
- No TLS, secrets in Git, minimal CI/CD
- Production Readiness Score: **58/100**

## Target State

- 14+ microservices with shared library
- Kubernetes orchestration
- Managed PostgreSQL (Multi-AZ, read replicas)
- RabbitMQ cluster (3 nodes) with persistence
- Redis cluster (3 nodes)
- Full TLS, vault-managed secrets, comprehensive CI/CD
- Full observability (logging, metrics, tracing)
- Production Readiness Score: **90+/100**

---

## Phase 0: Emergency Fixes (Week 1–2)

**Goal:** Eliminate critical security vulnerabilities

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 1 | Remove all secrets from Git history (git filter-branch or BFG) | 2h | Critical |
| 2 | Generate new JWT keys, DB passwords, encryption keys, service tokens | 1h | Critical |
| 3 | Move secrets to `.env` files NOT in Git (already in .gitignore but files are tracked) | 1h | Critical |
| 4 | Switch RabbitMQ from tmpfs to Docker volume | 15m | High |
| 5 | Add Redis AUTH password | 30m | High |
| 6 | Change RabbitMQ credentials from guest/guest | 30m | High |
| 7 | Add TLS termination at Nginx gateway (self-signed for now) | 2h | High |
| 8 | Add `git-secrets` pre-commit hook | 30m | Preventive |

**Deliverable:** Secure development environment
**Score Impact:** 58 → ~68

---

## Phase 1: CI/CD & Quality Foundation (Week 3–6)

**Goal:** Automated quality gates for all services

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 1 | Create shared CI pipeline (matrix strategy for all 8 services) | 1 week |  |
| 2 | Add linting: ruff + mypy to pipeline | 2 days | Code quality |
| 3 | Add security scanning: bandit + safety | 1 day | Vulnerability detection |
| 4 | Expand unit tests to 70% coverage (all services) | 2 weeks | Reliability |
| 5 | Add Docker image build + push to GitHub Container Registry | 2 days | Deployment readiness |
| 6 | Add pre-commit hooks (lint, format, secrets) | 1 day | Developer experience |
| 7 | Create `ophillia-commons` shared Python package | 1 week | Reduce duplication |
| 8 | Standardize pagination across all services | 2 days | API consistency |

**Deliverable:** All services with automated testing and quality gates
**Score Impact:** 68 → ~75

---

## Phase 2: Observability & Hardening (Week 7–10)

**Goal:** Production-grade monitoring and security

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 1 | Deploy Loki + Promtail for centralized logging | 3 days | Logging |
| 2 | Deploy Prometheus + scrape all services | 2 days | Metrics |
| 3 | Deploy Grafana with pre-built dashboards | 2 days | Visualization |
| 4 | Add Tempo for distributed tracing | 2 days | Tracing |
| 5 | Add OpenTelemetry SDK to all services | 1 week | Trace context |
| 6 | Implement circuit breakers on cross-service HTTP calls | 3 days | Resilience |
| 7 | Move rate limiting to Redis backend | 2 days | Scalability |
| 8 | Add Redis caching for hot data (policies, structures, types) | 3 days | Performance |
| 9 | Implement idempotency keys on critical POST endpoints | 3 days | Reliability |
| 10 | Add database backup automation (pg_dump to S3) | 2 days | Disaster recovery |

**Deliverable:** Observable, resilient services
**Score Impact:** 75 → ~82

---

## Phase 3: Missing Core Features (Week 11–18)

**Goal:** Complete core HRMS feature set

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 1 | **Build Organization Service** (hierarchy, org chart, locations) | 2 weeks | Core |
| 2 | **Build Reporting/Analytics Service** (dashboards, KPIs, exports) | 3 weeks | Core |
| 3 | **Add income tax + TDS to Payroll** | 2 weeks | Compliance |
| 4 | **Implement email delivery** (SendGrid/SES integration) | 3 days | Feature |
| 5 | **Implement leave accrual cron** | 2 days | Automation |
| 6 | **Add PDF payslip generation** | 3 days | Feature |
| 7 | **Implement department leave limits** (currently mocked) | 3 days | Fix |
| 8 | **Implement manager auto-assignment** for approvals | 3 days | Fix |
| 9 | **Add shift management** to attendance service | 1 week | Feature |
| 10 | **Unify students_events to hrms_events** exchange | 2h | Architecture |

**Deliverable:** Feature-complete core HRMS
**Score Impact:** 82 → ~88

---

## Phase 4: Enterprise Features (Week 19–30)

**Goal:** Enterprise-grade platform

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 1 | **Build Workflow/Approval Engine** (extract from leave/payroll) | 3 weeks | Architecture |
| 2 | **Build Recruitment/ATS Service** | 4 weeks | Feature |
| 3 | **Build Performance Management Service** | 3 weeks | Feature |
| 4 | **Build Document Management Service** (S3 integration) | 2 weeks | Feature |
| 5 | **Add 2FA/MFA** to auth service | 1 week | Security |
| 6 | **Add OAuth/OIDC social login** | 2 weeks | Feature |
| 7 | **Add contract tests** (Pact) for all service boundaries | 1 week | Quality |
| 8 | **Add performance/load tests** (k6/Locust) | 1 week | Quality |

**Deliverable:** Enterprise HRMS platform
**Score Impact:** 88 → ~93

---

## Phase 5: Scale & Optimize (Week 31+)

**Goal:** Production-grade deployment infrastructure

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 1 | Create Kubernetes manifests (Kustomize) | 2 weeks | Orchestration |
| 2 | Set up managed PostgreSQL (RDS Multi-AZ) | 1 week | HA |
| 3 | Set up RabbitMQ cluster (Amazon MQ or 3-node) | 1 week | HA |
| 4 | Set up Redis cluster (ElastiCache) | 3 days | HA |
| 5 | Deploy HashiCorp Vault for secrets | 1 week | Security |
| 6 | Set up horizontal pod autoscaler | 2 days | Scalability |
| 7 | Implement blue-green deployments | 3 days | Zero-downtime |
| 8 | Set up staging environment | 3 days | Quality |
| 9 | Implement CDN for frontend (CloudFront/CloudFlare) | 2 days | Performance |
| 10 | SOC 2 / GDPR compliance audit | 4 weeks | Compliance |

**Deliverable:** Production-deployed, scalable platform
**Score Impact:** 93 → ~98

---

## Timeline Summary

```
Week  1-2:   ████ Phase 0 — Emergency Security Fixes
Week  3-6:   ████████ Phase 1 — CI/CD & Quality
Week  7-10:  ████████ Phase 2 — Observability
Week 11-18:  ████████████████ Phase 3 — Core Features
Week 19-30:  ████████████████████████ Phase 4 — Enterprise
Week 31+:    ████████████████ Phase 5 — Scale
```

---

## Resource Requirements

| Phase | Engineers | Duration | Focus |
|-------|-----------|----------|-------|
| Phase 0 | 1 DevOps | 2 weeks | Security |
| Phase 1 | 1 DevOps + 2 Backend | 4 weeks | CI/CD + Testing |
| Phase 2 | 1 DevOps + 1 Backend | 4 weeks | Observability |
| Phase 3 | 3 Backend + 1 Frontend | 8 weeks | Features |
| Phase 4 | 4 Backend + 2 Frontend | 12 weeks | Features |
| Phase 5 | 2 DevOps + 1 Backend | 8+ weeks | Infrastructure |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Secrets already leaked from Git | HIGH | CRITICAL | Rotate ALL keys immediately |
| Breaking changes during shared library extraction | MEDIUM | HIGH | Gradual migration with backward compatibility |
| Income tax calculation complexity | HIGH | HIGH | Start with new tax regime (simpler); add old regime later |
| Kubernetes migration breaks Docker Compose workflow | MEDIUM | MEDIUM | Maintain Compose for local dev |
| Performance regression with observability overhead | LOW | MEDIUM | Profile before/after; use sampling |
| Team bandwidth for enterprise features | HIGH | HIGH | Prioritize by customer demand |

---

## Success Metrics

| Metric | Current | Phase 1 | Phase 3 | Phase 5 |
|--------|---------|---------|---------|---------|
| Production Readiness Score | 58 | 75 | 88 | 98 |
| Test Coverage (unit) | ~40% | 70% | 80% | 90% |
| CI/CD Services Covered | 1/8 | 8/8 | 10/14 | 14/14 |
| Mean Time to Deploy | Manual | 30 min | 15 min | 5 min |
| MTTR (Mean Time to Recovery) | Unknown | 1 hour | 30 min | 5 min |
| P95 Response Time | Unknown | < 500ms | < 300ms | < 200ms |
| Uptime SLA | None | 99% | 99.5% | 99.9% |
