# 06 — Proposed Architecture Improvements

## Backend Improvements

### 1. New Onboarding Service

Create a new microservice: `onboarding-service` (FastAPI, port 8008)

**Responsibilities:**
- Track onboarding state per company
- Coordinate multi-service initialization
- Expose onboarding status and progress APIs
- React to events from other services to update progress

**Database:** `onboarding_db` (add to `init-databases.sh`)

**Key Tables:**
```sql
-- Tracks overall onboarding state per company
CREATE TABLE onboarding_status (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL UNIQUE,
    state VARCHAR NOT NULL DEFAULT 'NOT_STARTED',
    -- State: NOT_STARTED | ACCOUNT_CREATED | DEFAULTS_SEEDED |
    --        WIZARD_COMPLETE | FULLY_ONBOARDED
    wizard_completed_at TIMESTAMP,
    fully_onboarded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tracks individual onboarding steps
CREATE TABLE onboarding_steps (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    step_key VARCHAR NOT NULL,
    -- e.g., 'departments_configured', 'leave_types_set', 'first_employee_added'
    status VARCHAR NOT NULL DEFAULT 'pending',
    -- Status: pending | completed | skipped
    completed_at TIMESTAMP,
    skipped_at TIMESTAMP,
    metadata JSONB,
    UNIQUE(company_id, step_key)
);

-- Templates for default data per industry/country
CREATE TABLE onboarding_templates (
    id UUID PRIMARY KEY,
    template_type VARCHAR NOT NULL,
    -- e.g., 'leave_types', 'departments', 'salary_structure'
    country VARCHAR,
    industry VARCHAR,
    data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
```

**API Endpoints:**
```
GET  /api/v1/onboarding/status          → Current onboarding state + steps
POST /api/v1/onboarding/complete-step   → Mark a step as completed/skipped
POST /api/v1/onboarding/complete-wizard → Mark wizard as done
GET  /api/v1/onboarding/templates       → Get available templates
```

**RabbitMQ Consumers:**
```python
# Listens for service-seeded confirmations
@consumer("departments.seeded")
async def on_departments_seeded(event):
    await mark_step_completed(event.company_id, "departments_configured")
    await check_all_defaults_seeded(event.company_id)

@consumer("leave_types.seeded")
async def on_leave_types_seeded(event):
    await mark_step_completed(event.company_id, "leave_types_configured")
    await check_all_defaults_seeded(event.company_id)

# ... similar for payroll, attendance, notification

async def check_all_defaults_seeded(company_id):
    """If all services have confirmed seeding, advance state."""
    steps = await get_steps(company_id, ["departments_configured",
                                          "leave_types_configured",
                                          "salary_structure_configured",
                                          "attendance_policy_configured"])
    if all(s.status == "completed" for s in steps):
        await update_state(company_id, "DEFAULTS_SEEDED")
        await publish("onboarding.defaults_ready", { "company_id": company_id })
```

---

### 2. Auth Service: Bootstrap Endpoint

Add a new endpoint to auth-service for first-run setup:

```python
@router.post("/bootstrap", response_model=BootstrapResponse)
async def bootstrap_system(data: BootstrapRequest, db: AsyncSession):
    """
    Create the first admin + company. Only available when 0 users exist.
    Self-disabling: returns 403 if any user already exists.
    """
    user_count = await user_repo.count_all(db)
    if user_count > 0:
        raise HTTPException(403, "System already initialized")

    company = await auth_service.register_company(db, data.company)
    user = await auth_service.create_user(db, data.user, role="super_admin",
                                           company_id=company.id)
    tokens = await auth_service.generate_tokens(user)

    # Publish event with full company metadata
    await publish_event("company.created", {
        "company_id": str(company.id),
        "name": data.company.name,
        "country": data.company.country,
        "industry": data.company.industry,
        "timezone": data.company.timezone,
        "employee_count_range": data.company.employee_count_range,
        "created_by": str(user.id)
    })

    return BootstrapResponse(tokens=tokens, user=user, company=company)
```

Add a system status endpoint:
```python
@router.get("/system-status", response_model=SystemStatus)
async def get_system_status(db: AsyncSession):
    """Public endpoint: returns whether the system has been initialized."""
    user_count = await user_repo.count_all(db)
    return SystemStatus(
        initialized=user_count > 0,
        version="1.0.0"
    )
```

---

### 3. Auth Service: Invite System

```python
@router.post("/invite", response_model=InviteResponse)
async def invite_user(data: InviteRequest, current_user: TokenPayload):
    """Send an invitation email to join the company."""
    magic_token = await auth_service.create_magic_token(
        email=data.email,
        purpose="invite",
        company_id=current_user.company_id,
        role=data.role
    )
    await publish_event("user.invited", {
        "email": data.email,
        "company_id": current_user.company_id,
        "invited_by": current_user.sub,
        "role": data.role,
        "invite_url": f"{FRONTEND_URL}/accept-invite?token={magic_token}"
    })
    return InviteResponse(email=data.email, status="sent")

@router.post("/invite-batch", response_model=BatchInviteResponse)
async def invite_users_batch(data: BatchInviteRequest, current_user: TokenPayload):
    """Send invitations to multiple users."""
    results = []
    for invite in data.invites:
        result = await invite_user(invite, current_user)
        results.append(result)
    return BatchInviteResponse(results=results)
```

---

### 4. Event Publishing in Auth Service

Add RabbitMQ publisher to auth-service (currently missing):

```python
# services/auth-service/app/events/publisher.py
import aio_pika
from app.core.config import settings

async def publish_event(event_type: str, payload: dict):
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "hrms_events", aio_pika.ExchangeType.TOPIC, durable=True
        )
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps({
                    "event_type": event_type,
                    "payload": payload,
                    "timestamp": datetime.utcnow().isoformat(),
                    "correlation_id": str(uuid4())
                }).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=event_type
        )
```

---

### 5. Service Seed Handlers

Each service needs a `company.created` consumer that seeds defaults:

**Employee Service:**
```python
@consumer("company.created")
async def seed_defaults(event):
    company_id = event["company_id"]
    industry = event.get("industry", "general")

    templates = get_department_templates(industry)
    # e.g., ["Human Resources", "Engineering", "Finance", "Operations"]

    for dept in templates:
        await department_repo.create(DepartmentCreate(
            company_id=company_id,
            name=dept["name"],
            description=dept["description"]
        ))

    await publish("departments.seeded", {"company_id": company_id})
```

**Leave Service:**
```python
@consumer("company.created")
async def seed_defaults(event):
    company_id = event["company_id"]
    country = event.get("country", "IN")

    # Seed leave types
    leave_templates = get_leave_templates(country)
    for lt in leave_templates:
        await leave_type_repo.create(LeaveTypeCreate(
            company_id=company_id, **lt
        ))

    # Seed holidays
    holiday_templates = get_holiday_templates(country, datetime.now().year)
    for h in holiday_templates:
        await holiday_repo.create(HolidayCreate(
            company_id=company_id, **h
        ))

    await publish("leave_types.seeded", {"company_id": company_id})
```

---

## Frontend Improvements

### 1. Bootstrap/Setup Page

New route: `/setup` (public, only shown when system not initialized)

```typescript
// router guard
router.beforeEach(async (to, from, next) => {
  // Check system initialization status
  if (!systemStore.initChecked) {
    const status = await api.get('/auth/system-status')
    systemStore.setInitialized(status.initialized)
  }

  // If system not initialized and not on setup page, redirect
  if (!systemStore.initialized && to.path !== '/setup') {
    return next('/setup')
  }

  // If system initialized and on setup page, redirect to login
  if (systemStore.initialized && to.path === '/setup') {
    return next('/login')
  }

  // ... existing auth guards
})
```

### 2. Onboarding Wizard Component

```
src/
  pages/
    onboarding/
      OnboardingLayout.vue    → Wizard shell with progress bar
      StepCompanyReview.vue   → Review/edit company details
      StepDepartments.vue     → Review/customize departments
      StepLeavePolicy.vue     → Review/customize leave types
      StepInviteTeam.vue      → Invite employees by email
      StepReviewLaunch.vue    → Summary + "Get Started" button
  components/
    onboarding/
      OnboardingProgress.vue  → Reusable progress bar
      OnboardingChecklist.vue → Dashboard widget
      EmptyState.vue          → Reusable empty state with CTA
```

### 3. Guarded Routes Enhancement

```typescript
// Enhanced route guard: check onboarding state
if (authStore.isAuthenticated) {
  const onboardingState = await onboardingStore.fetchStatus()

  if (onboardingState.state === 'ACCOUNT_CREATED' ||
      onboardingState.state === 'DEFAULTS_SEEDED') {
    // Redirect to onboarding wizard (unless already there)
    if (!to.path.startsWith('/onboarding')) {
      return next('/onboarding')
    }
  }
}
```

### 4. Dashboard Onboarding Widget

Add a conditional widget to the Dashboard:

```vue
<!-- In Dashboard.vue -->
<OnboardingChecklist
  v-if="onboardingStore.state !== 'FULLY_ONBOARDED'"
  :steps="onboardingStore.steps"
  @dismiss="onboardingStore.dismiss()"
  @continue="router.push('/onboarding')"
/>
```

### 5. Empty State Components

Replace empty tables with guided empty states:

```vue
<!-- Reusable EmptyState.vue -->
<template>
  <v-card class="text-center pa-8">
    <v-icon size="64" color="grey-lighten-1">{{ icon }}</v-icon>
    <h3 class="mt-4">{{ title }}</h3>
    <p class="text-grey mt-2">{{ description }}</p>
    <v-btn color="primary" class="mt-4" @click="$emit('action')">
      {{ actionText }}
    </v-btn>
  </v-card>
</template>

<!-- Usage in Employees list -->
<EmptyState
  v-if="employees.length === 0"
  icon="mdi-account-group"
  title="No employees yet"
  description="Add your first employee to get started with HR management."
  actionText="Add Employee"
  @action="router.push('/employees/new')"
/>
```

---

## Database Improvements

### 1. Enrich Company Model

```sql
ALTER TABLE companies ADD COLUMN country VARCHAR(2);       -- ISO 3166-1
ALTER TABLE companies ADD COLUMN timezone VARCHAR(50);     -- IANA timezone
ALTER TABLE companies ADD COLUMN industry VARCHAR(100);
ALTER TABLE companies ADD COLUMN employee_count_range VARCHAR(20); -- '1-10', '11-50', etc.
ALTER TABLE companies ADD COLUMN logo_url VARCHAR(500);
ALTER TABLE companies ADD COLUMN settings JSONB DEFAULT '{}';
-- settings: { date_format, currency, working_days, fiscal_year_start }
```

### 2. Feature Flags Table (in auth_db)

```sql
CREATE TABLE company_features (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id),
    feature_key VARCHAR NOT NULL,
    -- e.g., 'payroll', 'students', 'geofence_attendance', 'magic_link_login'
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    UNIQUE(company_id, feature_key)
);
```

### 3. Onboarding Tables (in onboarding_db)

As described in the Onboarding Service section above:
- `onboarding_status` — per-company state machine
- `onboarding_steps` — granular step tracking
- `onboarding_templates` — seed data templates by country/industry

---

## Infrastructure Improvements

### 1. Fix RabbitMQ Persistence

```yaml
# docker-compose.yml — replace tmpfs with volume
rabbitmq:
  volumes:
    - rabbitmq-data:/var/lib/rabbitmq  # was tmpfs
# Add to volumes section:
volumes:
  rabbitmq-data:
```

### 2. Add Redis Authentication

```yaml
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD}
  environment:
    - REDIS_PASSWORD=your-secure-redis-password
```

Update all service configs:
```env
REDIS_URL=redis://:${REDIS_PASSWORD}@hrms-redis:6379/0
```

### 3. Add Onboarding Service to Docker Compose

```yaml
onboarding-service:
  build: ./services/onboarding-service
  container_name: hrms-onboarding
  profiles: ["core"]
  environment:
    - DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASS}@hrms-db:5432/onboarding_db
    - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
  depends_on:
    hrms-db:
      condition: service_healthy
    rabbitmq:
      condition: service_healthy
  networks:
    - hrms-network
```

Update Nginx to route `/api/v1/onboarding/*` to the new service.

### 4. Add Database to Init Script

```bash
# infra/init-databases.sh — add:
CREATE DATABASE onboarding_db;
```

---

## Final Architecture (To-Be)

```
┌─────────────┐     ┌──────────┐     ┌────────────────┐
│   Frontend   │────▶│  Nginx   │────▶│  Auth Service   │──▶ auth_db
│  (Vue 3)     │     │ Gateway  │     │  + Bootstrap    │     (companies enriched)
│  + Wizard    │     └──────────┘     │  + Invites      │     (+ company_features)
│  + Checklist │          │           │  + Events Pub   │
└─────────────┘          │           └────────────────┘
                          │                    │
                          │              ┌─────▼─────┐
                          │              │ RabbitMQ   │ (persistent volume)
                          │              │ hrms_events│
                          │              └─────┬─────┘
                          │                    │
                          ├──▶ Onboarding Service ──▶ onboarding_db [NEW]
                          │       (state machine, coordination)
                          │
                          ├──▶ Employee Service ──▶ employee_db
                          │       (+ seed handler)
                          │
                          ├──▶ Leave Service ──▶ leave_db
                          │       (+ seed handler)
                          │
                          ├──▶ Payroll Service ──▶ payroll_db
                          │       (+ seed handler)
                          │
                          ├──▶ Attendance Service ──▶ attendance_db
                          │       (+ seed handler)
                          │
                          ├──▶ Students Service ──▶ students_db
                          ├──▶ Audit Service ──▶ audit_db
                          └──▶ Notification Service ──▶ notification_db
                                  (+ invite email handler)

Infrastructure: PostgreSQL 16 | RabbitMQ 3.12 (persistent) | Redis 7 (with AUTH)
```
