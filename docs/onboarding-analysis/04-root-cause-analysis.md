# 04 — Root Cause Analysis

For each problem identified in [03-problems-and-gaps.md](03-problems-and-gaps.md), this document explains **why** it exists, **which component** is responsible, and what **architectural decision** caused it.

---

## Technical Issues

### T1: No Cross-Service Event Propagation

| Aspect | Detail |
|--------|--------|
| **Why it happens** | The `register_company()` method in AuthService performs a simple database INSERT and returns. No event publishing code exists. |
| **Responsible component** | `auth-service/app/services/auth_service.py` |
| **Root cause** | Auth service was built as a standalone identity provider. Company management was added later (migration `0002_add_companies.py`) without integrating the existing RabbitMQ infrastructure. |
| **Evidence** | RabbitMQ is configured in docker-compose and `.env.docker` files, and other services have RabbitMQ consumer code (audit-service, notification-service), but auth-service has no publisher for company lifecycle events. |

### T2: No Default Data Seeding Per Tenant

| Aspect | Detail |
|--------|--------|
| **Why it happens** | Each service operates independently with no awareness of company creation events. There is no "on tenant created, seed defaults" handler. |
| **Responsible component** | All services — but primarily the missing orchestration layer |
| **Root cause** | The database-per-service pattern was implemented without an event-driven initialization pattern. Services were designed to serve API requests, not react to lifecycle events. Each service only creates records when explicitly asked via its REST API. |
| **Evidence** | No service has a `setup_defaults()` or `initialize_tenant()` function. No RabbitMQ consumer handles a `company.created` event. |

### T3: No Idempotent Initialization

| Aspect | Detail |
|--------|--------|
| **Why it happens** | `seed_user.py` uses `get_or_create` for the company (by name) but does INSERT for the user without checking existence first. API endpoints rely on database unique constraints for deduplication. |
| **Responsible component** | `auth-service/seed_user.py`, `auth-service/app/repositories/user_repository.py` |
| **Root cause** | The seed script was written as a one-time bootstrapper, not as a repeatable initialization tool. No idempotency keys or "upsert" patterns were considered. |

### T4: No First-Run Detection

| Aspect | Detail |
|--------|--------|
| **Why it happens** | The system was designed assuming an operator would always run `seed_user.py` before any user accesses the frontend. The frontend login page is a dead end without pre-existing credentials. |
| **Responsible component** | Both auth-service and frontend |
| **Root cause** | The system was built "inside out" — backend APIs first, then frontend consuming those APIs. The cold-start scenario (zero users, zero companies) was never designed as a user-facing flow. |

### T5: RabbitMQ Volatile Storage

| Aspect | Detail |
|--------|--------|
| **Why it happens** | `docker-compose.yml` mounts `tmpfs` for RabbitMQ data directory instead of a Docker volume. |
| **Responsible component** | `docker-compose.yml` |
| **Root cause** | Likely a development convenience to avoid stale queue buildup during rapid iteration. Was never updated for production readiness. |

### T6: Redis No Authentication

| Aspect | Detail |
|--------|--------|
| **Why it happens** | Redis is started with default configuration. No `requirepass` directive or `--requirepass` flag. |
| **Responsible component** | `docker-compose.yml` → redis service |
| **Root cause** | Development-oriented setup where security was deferred. Redis is on the internal Docker bridge network, so it's not directly exposed, but any compromised container can access it. |

### T7: Stale Token After Company Creation

| Aspect | Detail |
|--------|--------|
| **Why it happens** | The `/create-company` page calls `POST /auth/companies` to create the company, then redirects to the dashboard. But it doesn't call `/auth/select-company` to get a new token scoped to the newly created company. |
| **Responsible component** | `frontend-tailless-ophillia-hrms-vue/src/pages/CreateCompany.vue` |
| **Root cause** | The Create Company and Select Company flows were built as separate features. The create flow assumes the user's existing token is sufficient, but the token's `company_id` may be null or stale. |

---

## UX Issues

### U1: No Self-Service First User Registration

| Aspect | Detail |
|--------|--------|
| **Why it happens** | The public `POST /auth/register` endpoint forces `role=EMPLOYEE` and requires an existing `company_id` in SaaS mode. There is no "create account + create company" combined flow. |
| **Responsible component** | `auth-service/app/services/auth_service.py` → `register_user()` |
| **Root cause** | Registration was designed for employees joining an existing company, not for founders creating a new one. The SaaS self-signup scenario was added via `POST /auth/companies` but was never linked to user registration. |

### U2: Empty Dashboard After First Login

| Aspect | Detail |
|--------|--------|
| **Why it happens** | Dashboard component calls `fetchEmployees`, `fetchDepartments`, etc. on mount. These return empty arrays. The component renders KPI cards showing "0" with no conditional empty-state handling. |
| **Responsible component** | `frontend-tailless-ophillia-hrms-vue/src/pages/Dashboard.vue` |
| **Root cause** | Dashboard was designed for an already-running organization, not for a fresh setup. No distinction between "no data yet" and "data exists but is zero." |

### U3: No Onboarding Checklist

| Aspect | Detail |
|--------|--------|
| **Why it happens** | The `post-login-context` endpoint returns a single `next_action` enum — it's a single decision point, not a multi-step workflow. Once the user enters the dashboard, there's no further guidance. |
| **Responsible component** | Auth service + Frontend |
| **Root cause** | The post-login context was designed as a routing decision ("where to go next"), not as an onboarding state machine. The concept of multi-step onboarding was never part of the initial architecture. |

### U4: Minimal Company Creation Form

| Aspect | Detail |
|--------|--------|
| **Why it happens** | The `Company` model only has `name`, `domain`, `is_active`, and `created_at`. There's no schema for additional metadata. |
| **Responsible component** | `auth-service/app/models/user.py` → `Company` class |
| **Root cause** | Company was modeled as an authentication/isolation boundary, not as a rich organizational entity. The multi-tenant isolation needed `company_id` as a foreign key — so the company table was kept minimal. |

### U5: No User Invitation System

| Aspect | Detail |
|--------|--------|
| **Why it happens** | The `POST /auth/users` endpoint creates a single user with a password. There's no email notification, no invite token, no bulk endpoint. |
| **Responsible component** | `auth-service/app/services/auth_service.py` → `create_user()` |
| **Root cause** | User creation was designed as an admin CRUD operation, not as an invitation workflow. The magic-link infrastructure exists and could be repurposed for invites, but the connection was never made. |

### U6–U7: No Empty States or Contextual Help

| Aspect | Detail |
|--------|--------|
| **Why it happens** | Frontend components render data tables directly from API responses. No conditional rendering for empty states. No tooltip or help components exist. |
| **Responsible component** | All frontend list/form components |
| **Root cause** | Frontend was built feature-by-feature as a data management UI, not as a product with a user experience layer. Standard CRUD patterns were followed without progressive disclosure or contextual guidance. |

---

## System Design Issues

### S1: No Onboarding Orchestration

| Aspect | Detail |
|--------|--------|
| **Why it happens** | Each microservice was built as an independent CRUD API. There is no service that coordinates cross-service workflows. |
| **Responsible component** | Architecture-level gap |
| **Root cause** | The microservices were designed for **runtime request handling**, not for **lifecycle orchestration**. The architecture follows a request-response pattern exclusively. The existing RabbitMQ infrastructure was intended for async events (audit logging, notifications) but was never extended to lifecycle workflows. |

### S2: No Onboarding State Machine

| Aspect | Detail |
|--------|--------|
| **Why it happens** | No `onboarding_status` or `setup_progress` table exists in any database. The `post-login-context` calculates state in real-time based on company count. |
| **Responsible component** | Auth service |
| **Root cause** | The onboarding "state" is computed, not stored. This works for the simple 3-way decision (create/select/dashboard) but cannot support multi-step progress tracking. |

### S3: Auth-Company Tight Coupling

| Aspect | Detail |
|--------|--------|
| **Why it happens** | Company CRUD endpoints are in `auth_routes.py`. The Company model is in `auth-service/app/models/user.py` alongside User, RefreshToken, and MagicToken. |
| **Responsible component** | Auth service |
| **Root cause** | The company table was added to the auth service because it was the first place `company_id` was needed (as a FK on users). This grew organically — company management was "close enough" to auth to not warrant a separate service initially. |

### S4–S5: No Feature Flags or Tenant Config

| Aspect | Detail |
|--------|--------|
| **Why it happens** | The `Company` model is a thin identity record. No `company_settings`, `company_features`, or `tenant_config` tables exist. |
| **Responsible component** | Architecture-level gap |
| **Root cause** | Multi-tenancy was implemented at the data isolation level (company_id filtering) but not at the configuration level. All tenants are treated identically. |

---

## DevOps Issues

### D1: Manual Seed Step

| Aspect | Detail |
|--------|--------|
| **Why it happens** | `seed_user.py` is a standalone Python script that must be exec'd into the container. It's not integrated into the service startup or docker-compose lifecycle. |
| **Responsible component** | `auth-service/seed_user.py` |
| **Root cause** | Security decision — the first admin creation requires shell access to prevent unauthorized admin creation. However, this trades security for usability. A better approach would be a time-limited setup token or first-run API. |

### D2: No Environment-Aware Initialization

| Aspect | Detail |
|--------|--------|
| **Why it happens** | All `.env.docker` files have `DEBUG=false`. There's no `ENVIRONMENT=dev|staging|prod` variable that changes initialization behavior. |
| **Responsible component** | All service configuration files |
| **Root cause** | Single-environment mindset. The system was developed and tested in one configuration without environment differentiation. |

### D5: No HTTPS

| Aspect | Detail |
|--------|--------|
| **Why it happens** | Nginx config has `listen 80;` only. No `listen 443 ssl;` block. No certificate paths configured. |
| **Responsible component** | `services/gateway/nginx/nginx.conf` |
| **Root cause** | Development setup. HTTPS is typically handled by a reverse proxy or load balancer in production, but no documentation or configuration exists for that deployment pattern. |

---

## Dependency Graph of Root Causes

```
"Built as CRUD APIs, not as a product"
    ├── No onboarding orchestration (S1)
    ├── No onboarding state machine (S2)
    ├── No default data seeding (T2)
    └── No empty state guidance (U6)

"Company added as afterthought to auth"
    ├── Auth-company tight coupling (S3)
    ├── Minimal company model (U4)
    ├── No tenant config (S5)
    └── No feature flags (S4)

"Development-first, production-deferred"
    ├── RabbitMQ tmpfs (T5)
    ├── Redis no auth (T6)
    ├── No HTTPS (D5)
    ├── No backups (D4)
    └── No environment awareness (D2)

"No self-service bootstrap designed"
    ├── Manual seed step (D1)
    ├── No first-run detection (T4)
    ├── No self-registration (U1)
    └── No invite system (U5)
```
