# 03 — Current Problems & Gaps

## Technical Issues

### T1: No Cross-Service Event Propagation on Company Creation
- **What:** When `POST /auth/companies` creates a company, only the `auth_db.companies` table is updated. No event is published to RabbitMQ. No other service is notified.
- **Impact:** Employee, Leave, Payroll, Attendance, and Notification services have zero awareness of new tenants. Each service only discovers the company when the first scoped API request arrives.
- **Where:** `services/auth-service/app/services/auth_service.py` → `register_company()` method

### T2: No Default Data Seeding Per Tenant
- **What:** When a company is created, no default data is provisioned in any service:
  - No default departments
  - No default leave types (Sick, Casual, Earned, etc.)
  - No default salary structure templates
  - No default attendance policies
  - No default holidays
- **Impact:** Every tenant starts with a completely blank slate. Users must manually create all foundational data before the system is usable.
- **Where:** Missing entirely — no seed logic exists outside `seed_user.py`

### T3: No Idempotent Initialization
- **What:** If the `seed_user.py` script is run twice with the same parameters, behavior is undefined. Company creation via API has domain uniqueness checks but no idempotency keys.
- **Impact:** Retries or network failures during onboarding can leave the system in a partial state with no clean recovery path.
- **Where:** `services/auth-service/seed_user.py`, `services/auth-service/app/services/auth_service.py`

### T4: No First-Run Detection
- **What:** The system has no mechanism to detect whether this is a first-ever deployment. There's no flag, table, or configuration that says "this instance has never been set up."
- **Impact:** Cannot automatically trigger a bootstrap wizard or redirect to a setup page on first deployment.
- **Where:** Missing entirely

### T5: RabbitMQ Configured with tmpfs (Volatile Storage)
- **What:** In `docker-compose.yml`, RabbitMQ uses `tmpfs` mounts, meaning all queues and messages are lost on container restart.
- **Impact:** Any event-driven initialization that depends on RabbitMQ will lose messages on restart. This makes event-driven onboarding unreliable.
- **Where:** `docker-compose.yml` → rabbitmq service → `tmpfs: - /var/lib/rabbitmq`

### T6: Redis Has No Authentication
- **What:** Redis is deployed without a password (`requirepass` not set).
- **Impact:** Any service or attacker on the Docker network can read/write the JWT blacklist, potentially un-revoking tokens.
- **Where:** `docker-compose.yml` → redis service

### T7: JWT Token Contains company_id But No Token Refresh on Company Switch
- **What:** When a super_admin creates a company via the Create Company page, the frontend redirects to the dashboard but the existing JWT still has the old (or null) `company_id`. The `/select-company` endpoint handles re-issuance, but `/create-company` flow doesn't.
- **Impact:** After creating a company, the first few API calls may use a stale token without the new `company_id`.
- **Where:** `frontend-tailless-ophillia-hrms-vue/src/pages/CreateCompany.vue`

---

## UX Issues

### U1: No Self-Service First User Registration
- **What:** There is no `/signup` or `/register` route. The first user must be created via CLI.
- **Impact:** Non-technical users cannot deploy and start using the system without developer assistance.
- **Where:** Missing entirely from frontend routes and auth-service endpoints (public registration creates EMPLOYEE role only)

### U2: Empty Dashboard After First Login
- **What:** The dashboard shows KPI cards with all zeros (0 Employees, 0 Departments, etc.) and no contextual guidance.
- **Impact:** Users feel the product is broken or incomplete. No clear next steps.
- **Where:** `frontend-tailless-ophillia-hrms-vue/src/pages/Dashboard.vue`

### U3: No Onboarding Checklist or Progress Tracking
- **What:** After company creation, there is no wizard, checklist, or guided flow to help users set up their organization.
- **Impact:** Users must discover the setup order (Departments → Employees → Leave Types → etc.) by themselves.
- **Where:** Missing entirely

### U4: Minimal Company Creation Form
- **What:** The Create Company form only collects `name` and `domain`. No industry, timezone, country, logo, or customization.
- **Impact:** Missed opportunity to personalize the experience and pre-configure defaults based on company type.
- **Where:** `frontend-tailless-ophillia-hrms-vue/src/pages/CreateCompany.vue`

### U5: No User Invitation System
- **What:** There is no invite-by-email, invite link, or bulk import mechanism. Admins must create users one by one.
- **Impact:** Onboarding a team of 50+ people requires 50+ manual form submissions.
- **Where:** `services/auth-service/app/api/v1/endpoints/auth_routes.py` → `POST /users` (admin-only, single user)

### U6: No Empty State Guidance
- **What:** When lists are empty (Employees, Departments, etc.), they show empty tables with no illustrations, tips, or CTAs.
- **Impact:** Users don't know what to do or why the page is empty.
- **Where:** All list views in the frontend

### U7: No Contextual Help or Tooltips
- **What:** Forms don't explain what fields mean, what's required, or provide examples.
- **Impact:** Especially problematic for the Employee form (52 fields) and Payroll setup.
- **Where:** All form components

---

## System Design Issues

### S1: No Onboarding Orchestration Service
- **What:** There is no dedicated service or workflow engine that coordinates the multi-step onboarding process across services.
- **Impact:** Each service is independently unaware of onboarding state. No saga pattern, no compensation logic, no centralized status tracking.
- **Where:** Missing entirely

### S2: No Onboarding State Machine
- **What:** There is no state tracking for onboarding progress. The `post-login-context` endpoint provides a single `next_action` but doesn't track multi-step progress.
- **Impact:** Users can't resume onboarding if they close the browser. No way to show "3 of 7 steps complete."
- **Where:** `services/auth-service/app/services/auth_service.py` → `get_post_login_context()`

### S3: Tight Coupling Between Auth Service and Company Lifecycle
- **What:** The auth-service owns both authentication AND company management. Company creation, listing, updating, and deletion are all in auth routes.
- **Impact:** As company lifecycle grows more complex (billing, subscriptions, feature flags), the auth-service becomes a monolith.
- **Where:** `services/auth-service/app/api/v1/endpoints/auth_routes.py`

### S4: No Feature Flags Per Tenant
- **What:** There is no mechanism to enable/disable features per company (e.g., "this company uses payroll but not students").
- **Impact:** All tenants get all features, even if irrelevant. Cannot do gradual rollouts or A/B testing.
- **Where:** Missing entirely

### S5: No Tenant-Aware Configuration
- **What:** There is no per-tenant configuration table (timezone, date format, currency, working hours, etc.).
- **Impact:** All tenants share the same global configuration. An Indian company and a US company would have the same defaults.
- **Where:** Missing entirely — `companies` table only has `name`, `domain`, `is_active`

---

## DevOps Issues

### D1: Manual Seed Step Required for First Deployment
- **What:** `seed_user.py` must be run manually inside the auth container after deployment.
- **Impact:** Automated deployments (CI/CD, Kubernetes) can't fully bootstrap the system without a post-deploy hook.
- **Where:** `services/auth-service/seed_user.py`

### D2: No Environment-Aware Initialization
- **What:** The same initialization process runs regardless of environment (development, staging, production).
- **Impact:** Can't auto-seed demo data in dev, skip seeds in prod, or configure differently per environment.
- **Where:** No environment detection in any initialization code

### D3: No Health Check for "Ready to Use" State
- **What:** Service health checks only verify the process is running, not whether the system is fully initialized and ready for users.
- **Impact:** Monitoring tools report "healthy" even when no admin user or company exists.
- **Where:** All service health check endpoints

### D4: No Database Backup or Recovery Strategy
- **What:** No backup scripts, no pg_dump automation, no point-in-time recovery configuration.
- **Impact:** Data loss on infrastructure failure.
- **Where:** Missing from `infra/` directory

### D5: No HTTPS/TLS
- **What:** Nginx gateway listens on HTTP port 80 only. No SSL certificates configured.
- **Impact:** Credentials and tokens transmitted in plaintext. Unacceptable for production.
- **Where:** `services/gateway/nginx/nginx.conf`

---

## Summary Table

| ID | Category | Severity | Problem |
|----|----------|----------|---------|
| T1 | Technical | Critical | No cross-service event propagation |
| T2 | Technical | Critical | No default data seeding |
| T3 | Technical | Medium | No idempotent initialization |
| T4 | Technical | Medium | No first-run detection |
| T5 | Technical | High | RabbitMQ volatile storage |
| T6 | Technical | High | Redis no authentication |
| T7 | Technical | Medium | Stale token after company creation |
| U1 | UX | High | No self-service first user |
| U2 | UX | High | Empty dashboard, no guidance |
| U3 | UX | Critical | No onboarding checklist |
| U4 | UX | Medium | Minimal company creation form |
| U5 | UX | High | No user invitation system |
| U6 | UX | Medium | No empty state guidance |
| U7 | UX | Low | No contextual help |
| S1 | Design | Critical | No onboarding orchestration |
| S2 | Design | High | No onboarding state machine |
| S3 | Design | Medium | Auth-company tight coupling |
| S4 | Design | Medium | No feature flags |
| S5 | Design | Medium | No tenant configuration |
| D1 | DevOps | High | Manual seed step |
| D2 | DevOps | Medium | No environment-aware init |
| D3 | DevOps | Low | No "ready to use" health check |
| D4 | DevOps | High | No backup strategy |
| D5 | DevOps | Critical | No HTTPS |
