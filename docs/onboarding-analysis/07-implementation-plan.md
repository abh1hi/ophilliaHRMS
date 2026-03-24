# 07 — Implementation Plan

## Phase Overview

| Phase | Focus | Duration Estimate | Dependencies |
|-------|-------|-------------------|--------------|
| **Phase 1** | Stabilization & Security | — | None |
| **Phase 2** | UX Onboarding | — | Phase 1 |
| **Phase 3** | Backend Orchestration | — | Phase 1 |
| **Phase 4** | Optimization & Analytics | — | Phase 2 + 3 |

---

## Phase 1: Stabilization & Security

**Goal:** Fix critical infrastructure issues and make the current flow reliable.

### 1.1 Fix RabbitMQ Persistence
- **File:** `docker-compose.yml`
- **Change:** Replace `tmpfs` mount with named Docker volume
- **Risk:** Low — additive change, no data migration needed
```yaml
# Before:
tmpfs:
  - /var/lib/rabbitmq
# After:
volumes:
  - rabbitmq-data:/var/lib/rabbitmq
```

### 1.2 Add Redis Authentication
- **Files:** `docker-compose.yml`, all service `.env.docker` files
- **Change:** Add `--requirepass` to Redis, update connection strings
- **Risk:** Medium — all services must be updated simultaneously

### 1.3 Add HTTPS to Gateway
- **File:** `services/gateway/nginx/nginx.conf`
- **Change:** Add SSL listener on port 443, HTTP→HTTPS redirect, certificate configuration
- **Risk:** Medium — requires certificate provisioning (Let's Encrypt or self-signed for dev)

### 1.4 Fix Token Refresh After Company Creation
- **File:** `frontend-tailless-ophillia-hrms-vue/src/pages/CreateCompany.vue`
- **Change:** After `POST /auth/companies` succeeds, call `POST /auth/select-company` to get company-scoped tokens before redirecting to dashboard
- **Risk:** Low

### 1.5 Add Event Publishing to Auth Service
- **Files:** New file `services/auth-service/app/events/publisher.py`, modify `auth_service.py`
- **Change:** Add RabbitMQ publisher, publish `company.created` event after company creation
- **Risk:** Medium — new dependency, needs error handling for MQ connection failures
- **Key Principle:** Company creation must succeed even if event publishing fails (fire-and-forget with retry queue)

### 1.6 Add System Status Endpoint
- **File:** `services/auth-service/app/api/v1/endpoints/auth_routes.py`
- **Change:** Add `GET /auth/system-status` (public, returns `{initialized: bool}`)
- **Risk:** Low

### 1.7 Add Bootstrap Endpoint
- **File:** `services/auth-service/app/api/v1/endpoints/auth_routes.py`
- **Change:** Add `POST /auth/bootstrap` (creates first user + company, only when 0 users exist)
- **Risk:** Medium — security-sensitive, must be self-disabling
- **Validation:** Must verify 0 users in a transaction to prevent race conditions

### Phase 1 Checklist
- [ ] RabbitMQ persistent volume
- [ ] Redis password configured
- [ ] HTTPS on gateway (at minimum, documented for production)
- [ ] Token refresh after company creation
- [ ] RabbitMQ publisher in auth-service
- [ ] `GET /auth/system-status` endpoint
- [ ] `POST /auth/bootstrap` endpoint
- [ ] Company model enriched (country, timezone, industry, settings)
- [ ] `company_features` table created
- [ ] All existing tests still pass

---

## Phase 2: UX Onboarding

**Goal:** Build the frontend onboarding wizard and improve the first-time user experience.

### 2.1 First-Run Setup Page
- **File:** New `frontend-tailless-ophillia-hrms-vue/src/pages/Setup.vue`
- **Change:** Combined account + company creation form, shown only when system not initialized
- **Route:** `/setup` (public, guarded by system-status check)

### 2.2 Router Guard Enhancement
- **File:** `frontend-tailless-ophillia-hrms-vue/src/router/index.ts`
- **Change:** Add system initialization check before auth check. If not initialized → `/setup`. If initialized but not logged in → `/login`. If logged in but onboarding incomplete → `/onboarding`.

### 2.3 Onboarding Wizard Pages
- **New files:**
  - `src/pages/onboarding/OnboardingLayout.vue` — wizard shell with stepper
  - `src/pages/onboarding/StepDepartments.vue` — review/edit seeded departments
  - `src/pages/onboarding/StepLeavePolicy.vue` — review/edit leave types
  - `src/pages/onboarding/StepInviteTeam.vue` — batch invite by email
  - `src/pages/onboarding/StepReview.vue` — summary + launch button

### 2.4 Onboarding Store
- **New file:** `src/store/onboarding.store.ts`
- **State:** `{ status, steps, currentStep, dismissed }`
- **Actions:** `fetchStatus()`, `completeStep()`, `skipStep()`, `completeWizard()`
- **API calls:** `GET /onboarding/status`, `POST /onboarding/complete-step`, `POST /onboarding/complete-wizard`

### 2.5 Dashboard Onboarding Widget
- **File:** Modify `src/pages/Dashboard.vue`
- **Change:** Add `OnboardingChecklist` component that shows when onboarding is not `FULLY_ONBOARDED`
- **Behavior:** Dismissable, shows progress percentage, links to incomplete steps

### 2.6 Empty State Components
- **New file:** `src/components/common/EmptyState.vue`
- **Change:** Replace empty table states in Employees, Departments, Leave, Payroll pages with contextual empty states that include an illustration, explanation, and CTA button

### 2.7 Invite Acceptance Page
- **New file:** `src/pages/AcceptInvite.vue`
- **Route:** `/accept-invite?token=...`
- **Flow:** Verify invite token → show "Set your password" form → create account → redirect to dashboard

### Phase 2 Checklist
- [ ] `/setup` page (combined registration + company creation)
- [ ] Router guards for initialization and onboarding state
- [ ] Onboarding wizard (4-5 steps)
- [ ] Onboarding Pinia store
- [ ] Dashboard onboarding checklist widget
- [ ] Empty state components for all list pages
- [ ] Invite acceptance page
- [ ] Mobile-responsive wizard layout

---

## Phase 3: Backend Orchestration

**Goal:** Build the onboarding service and event-driven initialization.

### 3.1 Create Onboarding Service
- **New directory:** `services/onboarding-service/`
- **Structure:** Same as other services (FastAPI, SQLAlchemy, Alembic)
- **Database:** `onboarding_db`
- **Tables:** `onboarding_status`, `onboarding_steps`, `onboarding_templates`

### 3.2 Onboarding Service API
```
GET  /api/v1/onboarding/status           → State + steps for current company
POST /api/v1/onboarding/complete-step    → Mark step completed/skipped
POST /api/v1/onboarding/complete-wizard  → Advance to WIZARD_COMPLETE
GET  /api/v1/onboarding/templates        → Available seed templates
```

### 3.3 Onboarding Service Event Consumers
- Listen on `company.created` → initialize onboarding state
- Listen on `departments.seeded`, `leave_types.seeded`, `salary_structure.seeded`, `attendance_policy.seeded` → mark steps complete
- Listen on `employee.created` → check if first employee, update progress
- Publish `onboarding.defaults_ready` when all services confirm seeding
- Publish `onboarding.complete` when fully onboarded

### 3.4 Service Seed Handlers
Add `company.created` consumer to each service:

| Service | Seeds | Confirmation Event |
|---------|-------|--------------------|
| Employee | Default departments (4) | `departments.seeded` |
| Leave | Default leave types (3-5) + holidays | `leave_types.seeded` |
| Payroll | Default salary structure template | `salary_structure.seeded` |
| Attendance | Default attendance policy (manual, 8hrs) | `attendance_policy.seeded` |
| Notification | Default notification preferences | `notification_preferences.seeded` |

### 3.5 Seed Templates
Create JSON templates for different countries/industries:

```
services/onboarding-service/templates/
  leave_types/
    IN.json    → Indian leave types (CL, SL, EL, Maternity, Paternity)
    US.json    → US leave types (PTO, Sick, FMLA)
    default.json
  departments/
    tech.json  → Engineering, Product, QA, DevOps
    general.json → HR, Finance, Operations, Admin
  holidays/
    IN_2026.json → Indian national holidays
    US_2026.json → US federal holidays
  salary_structures/
    IN.json    → Indian payroll (Basic, HRA, PF, ESI)
    default.json
```

### 3.6 Auth Service: Invite Endpoints
- `POST /auth/invite` — single user invite
- `POST /auth/invite-batch` — batch invite (up to 50)
- Reuse magic-link infrastructure with `purpose='invite'`

### 3.7 Infrastructure Updates
- Add `onboarding_db` to `infra/init-databases.sh`
- Add `onboarding-service` to `docker-compose.yml`
- Add Nginx route: `/api/v1/onboarding/*` → `onboarding-service:8008`

### Phase 3 Checklist
- [ ] Onboarding service created (FastAPI + SQLAlchemy + Alembic)
- [ ] Onboarding database and migrations
- [ ] Onboarding API endpoints
- [ ] Event consumers in onboarding service
- [ ] Seed handlers in employee, leave, payroll, attendance, notification services
- [ ] Seed templates (JSON) for India + default
- [ ] Invite endpoints in auth service
- [ ] Docker Compose updated
- [ ] Nginx routing updated
- [ ] Init script updated
- [ ] Integration tests for full onboarding flow

---

## Phase 4: Optimization & Analytics

**Goal:** Make the onboarding flow observable, reliable, and measurable.

### 4.1 Structured Logging for Onboarding
- Add structured log entries at every state transition
- Include `company_id`, `step_key`, `duration_ms` in log context
- Use correlation IDs for cross-service tracing

### 4.2 Retry & Compensation Logic
- If a service fails to seed defaults, implement retry with exponential backoff
- Dead letter queue for failed seed events
- Manual retry endpoint: `POST /onboarding/retry-step/{step_key}`
- Alert on seed failures (via notification service)

### 4.3 Onboarding Analytics
- Track time-to-complete per step
- Track drop-off rates (which steps users skip or abandon)
- Track total onboarding time (signup → fully onboarded)
- Store in audit log with event_type `onboarding.*`

### 4.4 A/B Testing Framework
- Feature flag support for different onboarding flows
- Ability to add/remove/reorder wizard steps via configuration
- Track which variant leads to higher completion rates

### 4.5 Onboarding Email Sequence
- Welcome email after account creation
- Reminder email if onboarding stalls for 24h
- Completion celebration email
- Integrate with notification service

### 4.6 Health Check Enhancement
- Add "system readiness" health check that verifies:
  - All services healthy
  - Database migrations applied
  - At least one admin user exists (if expected)
- Expose via `/health/ready` (Kubernetes readiness probe compatible)

### Phase 4 Checklist
- [ ] Structured logging with correlation IDs
- [ ] Retry logic with dead letter queues
- [ ] Manual retry endpoint
- [ ] Onboarding analytics events
- [ ] Drop-off tracking
- [ ] Onboarding email sequence (3 emails)
- [ ] System readiness health check
- [ ] Load testing onboarding flow

---

## Implementation Priority Matrix

```
                    High Impact
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        │  PHASE 1:     │  PHASE 3:     │
        │  Fix infra    │  Onboarding   │
        │  Bootstrap EP │  service      │
        │  Event pub    │  Seed handlers│
Low ────┼───────────────┼───────────────┼──── High
Effort  │               │               │  Effort
        │  PHASE 2:     │  PHASE 4:     │
        │  Setup page   │  Analytics    │
        │  Empty states │  Email seq    │
        │  Wizard UI    │  A/B testing  │
        │               │               │
        └───────────────┼───────────────┘
                        │
                    Low Impact
```

**Recommended order:** Phase 1 → Phase 2 + Phase 3 (parallel) → Phase 4

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Bootstrap endpoint exploited to create rogue admin | Low | Critical | Self-disabling (check user count in transaction), rate limit, log all calls |
| Event publishing fails silently | Medium | High | Dead letter queue, health monitoring, manual retry endpoint |
| Seed data conflicts with user-created data | Medium | Medium | Idempotent seeds (check existence before insert), use unique constraints |
| Wizard interruption leaves partial state | Medium | Low | State machine persists progress, all steps resumable |
| Cross-service event ordering issues | Low | Medium | Each service handles events independently, onboarding service aggregates confirmations |
