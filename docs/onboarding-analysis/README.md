# First-Time Deployment & Onboarding Flow — Analysis Report

> **Project:** OphilliaHRMS
> **Date:** 2026-03-24
> **Scope:** Multi-tenant SaaS onboarding, first deployment, company initialization

---

## Executive Summary

OphilliaHRMS has a functional but incomplete onboarding flow. The system supports company creation, post-login context routing, and basic tenant isolation — but lacks orchestration, default data provisioning, guided UX, and event-driven initialization across services.

**Key Findings:**
- Company creation is isolated to the auth-service with **zero cross-service propagation**
- No default data (departments, leave types, salary structures) is seeded on company creation
- RabbitMQ is configured but **not used** for onboarding events
- Frontend has route guards and post-login context but **no onboarding wizard or progress tracking**
- First super_admin must be created via CLI (`seed_user.py`) — no self-service bootstrap

**Risk Level:** Medium-High — the system works for demo purposes but will frustrate real users and fail at scale.

---

## Report Structure

| # | File | Contents |
|---|------|----------|
| 1 | [01-current-flow-analysis.md](01-current-flow-analysis.md) | Step-by-step sequence of current deployment & login flow, API calls, sequence diagram |
| 2 | [02-user-journey-mapping.md](02-user-journey-mapping.md) | Real user experience mapping, what users see, UX gaps |
| 3 | [03-problems-and-gaps.md](03-problems-and-gaps.md) | Technical, UX, system design, and DevOps issues |
| 4 | [04-root-cause-analysis.md](04-root-cause-analysis.md) | Why each problem exists, which component is responsible |
| 5 | [05-ideal-flow-design.md](05-ideal-flow-design.md) | Industry-standard onboarding flow (To-Be), state machine, sequence diagram |
| 6 | [06-architecture-improvements.md](06-architecture-improvements.md) | Backend, frontend, and database architecture recommendations |
| 7 | [07-implementation-plan.md](07-implementation-plan.md) | Phased roadmap from stabilization to optimization |
| 8 | [08-industry-best-practices.md](08-industry-best-practices.md) | SaaS onboarding patterns, anti-patterns, comparison table |

---

## Problems → Solutions Quick Reference

| Problem | Impact | Solution | Phase |
|---------|--------|----------|-------|
| No cross-service initialization on company creation | Other services unaware of new tenant | Publish `CompanyCreated` event via RabbitMQ | Phase 1 |
| No default data (leave types, departments, etc.) | Empty dashboard, manual setup | Seed templates per service on `CompanyCreated` | Phase 1 |
| First admin requires CLI access | Can't self-deploy | Add bootstrap endpoint or first-run wizard | Phase 1 |
| No onboarding wizard | Users lost after company creation | Multi-step setup wizard in frontend | Phase 2 |
| No onboarding state tracking | Can't resume, no progress visibility | `onboarding_status` table + state machine | Phase 2 |
| No event-driven orchestration | Tight coupling, fragile initialization | Onboarding Service with saga pattern | Phase 3 |
| No observability on onboarding | Can't measure drop-off or failures | Structured logging + analytics events | Phase 4 |
| RabbitMQ on tmpfs | Messages lost on restart | Switch to persistent volume | Phase 1 |
| No HTTPS on gateway | Insecure in production | Add TLS termination to Nginx | Phase 1 |
| Redis has no AUTH | Security vulnerability | Add `requirepass` configuration | Phase 1 |

---

## Current Architecture Snapshot

```
┌─────────────┐     ┌──────────┐     ┌────────────────┐
│   Frontend   │────▶│  Nginx   │────▶│  Auth Service   │──▶ auth_db
│  (Vue 3)     │     │ Gateway  │     │  (FastAPI:8000) │
└─────────────┘     └──────────┘     └────────────────┘
                         │
                         ├──────────▶ Employee Service ──▶ employee_db
                         ├──────────▶ Attendance Service ──▶ attendance_db
                         ├──────────▶ Leave Service ──▶ leave_db
                         ├──────────▶ Payroll Service ──▶ payroll_db
                         ├──────────▶ Students Service ──▶ students_db
                         ├──────────▶ Audit Service ──▶ audit_db
                         └──────────▶ Notification Service ──▶ notification_db

Infrastructure: PostgreSQL 16 | RabbitMQ 3.12 | Redis 7
Tenant Isolation: company_id in JWT + row-level filtering (app-enforced)
```

---

## How to Use This Report

1. **Start with** [03-problems-and-gaps.md](03-problems-and-gaps.md) if you want to see what's broken
2. **Start with** [01-current-flow-analysis.md](01-current-flow-analysis.md) if you want to understand the system first
3. **Start with** [07-implementation-plan.md](07-implementation-plan.md) if you want to jump straight to action items
