# Service-by-Service Deep Dive Analysis

---

## 1. Auth Service (Port 8000)

### Bounded Context
Identity & Access Management

### Aggregate Roots
- **Company** (Tenant)
- **User** (Identity)

### What's Implemented
- Email/password login with Argon2id hashing (OWASP 2024 compliant)
- RS256 JWT access tokens (15-min expiry) with `jti` blacklist
- Stateful refresh tokens (30-day, bcrypt-hashed, rotation on use)
- Magic link passwordless authentication
- Password reset with enumeration-safe responses
- 4-tier RBAC: `super_admin > hr > manager > employee`
- Privilege escalation guards (can't grant higher role than own)
- Multi-tenant company registration and management
- Company selection for multi-company admins
- Post-login context routing for frontend
- Rate limiting: 3/hr (company reg), 5/min (register), 10/min (login)
- APScheduler background jobs: token cleanup (hourly), magic token purge (6hr)

### API Endpoints (17)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/companies` | None | Register company |
| GET | `/api/v1/auth/companies` | JWT | List companies (SA) |
| PATCH | `/api/v1/auth/companies/{id}` | JWT | Update company (SA) |
| DELETE | `/api/v1/auth/companies/{id}` | JWT | Soft-delete company (SA) |
| POST | `/api/v1/auth/register` | None | Self-registration |
| POST | `/api/v1/auth/users` | JWT | Admin create user (SA) |
| POST | `/api/v1/auth/login` | None | Login |
| POST | `/api/v1/auth/refresh` | None | Refresh token |
| GET | `/api/v1/auth/me` | JWT | Get profile |
| POST | `/api/v1/auth/logout` | JWT | Logout (blacklist+revoke) |
| POST | `/api/v1/auth/magic-link` | None | Request magic link |
| GET | `/api/v1/auth/verify-magic` | None | Verify magic link |
| POST | `/api/v1/auth/forgot-password` | None | Forgot password |
| POST | `/api/v1/auth/reset-password` | None | Reset password |
| PATCH | `/api/v1/auth/users/{id}/role` | JWT | Update role (HR/SA) |
| GET | `/api/v1/auth/post-login-context` | JWT | Frontend routing |
| POST | `/api/v1/auth/select-company` | JWT | Switch company |

### Database (4 tables)
- **companies**: id, name (unique), domain, is_active, created_at
- **users**: id, company_id (FK), email (unique), hashed_password, role, is_active, timestamps
- **refresh_tokens**: id, user_id (FK CASCADE), token_hash (bcrypt), expires_at, revoked
- **magic_tokens**: id, user_id (FK CASCADE), token_hash (bcrypt), purpose, expires_at, used

### Key Technical Decisions
- RS256 (asymmetric) for JWT — private key only on auth-service, public key shared
- Argon2id with 19MB memory cost (resists GPU attacks)
- Token blacklist in Redis with TTL matching JWT expiry
- Refresh token rotation (old revoked on each refresh)
- Email service is a stub (logs to stdout) — needs production SMTP integration

---

## 2. Employee Service (Port 8001)

### Bounded Context
Core HR / Employee Master Data

### Aggregate Roots
- **Employee** (with 52 columns)
- **Department**

### What's Implemented
- Full CRUD for employees with 52-field profile
- AES-256-GCM encryption for PII (Aadhaar, PAN, bank details, driving license)
- Department CRUD with soft-delete
- Bulk employee import with per-row error handling
- Internal service-to-service endpoint (`/employees/internal/{user_id}`)
- Pagination with search (name/email), filtering (department, status)
- Event publishing: `employee.created`, `employee.updated`, `employee.deactivated`
- Rate limiting: 30/min (CRUD), 10/min (bulk)
- Alembic migrations (3 versions: initial → multi-tenancy → expanded fields)

### API Endpoints (14)

| Method | Path | Auth | RBAC | Description |
|--------|------|------|------|-------------|
| POST | `/employees` | JWT | HR, SA | Create employee |
| GET | `/employees` | JWT | HR, SA, Mgr | List (paginated) |
| GET | `/employees/me` | JWT | Any | Own profile |
| GET | `/employees/{id}` | JWT | Any | Get by ID |
| PATCH | `/employees/{id}` | JWT | HR, SA | Update |
| DELETE | `/employees/{id}` | JWT | HR, SA | Soft-deactivate |
| POST | `/employees/bulk` | JWT | HR, SA | Bulk import |
| GET | `/employees/internal/{user_id}` | Token | Internal | Lookup by user_id |
| POST | `/departments` | JWT | HR, SA | Create dept |
| GET | `/departments` | JWT | Any | List depts |
| GET | `/departments/{id}` | JWT | Any | Get dept |
| PATCH | `/departments/{id}` | JWT | HR, SA | Update dept |
| DELETE | `/departments/{id}` | JWT | HR, SA | Soft-delete dept |
| GET | `/health` | None | — | Health check |

### Database (2 tables)
- **employees**: 52 columns including encrypted PII fields, UUID PKs, company_id scoping
- **departments**: id, company_id, name, description, manager_id, is_active, timestamps

### Key Technical Decisions
- PII encryption via SQLAlchemy `TypeDecorator` (transparent encrypt/decrypt)
- Tenant isolation at ORM level with `do_orm_execute` and `before_flush` event listeners
- Soft-delete for employees (status=terminated), departments (is_active=0)
- No cascade: deleting department sets employee's department_id to NULL

---

## 3. Attendance Service (Port 8002)

### Bounded Context
Time & Attendance Tracking

### Aggregate Roots
- **AttendanceRecord**
- **GeofenceLocation**
- **AttendancePolicy**

### What's Implemented
- Clock-in/out with GPS geofence validation (Haversine formula)
- Late detection based on configurable work_start_time
- Overtime calculation (work_hours - policy.work_hours_per_day)
- Half-day auto-detection
- Daily task management (add, assign, complete at punch-out)
- School-mode attendance (mark on behalf, with bulk option)
- Manual entry for backdated records
- Geofence management (CRUD with soft-delete)
- Policy management (employee > department > default resolution)
- Productivity reports (monthly task completion, ratings, expenses)
- Real-time alerts (late punch-ins, missed punch-outs)
- Cross-service employee validation before clock-in

### API Endpoints (27)

**Attendance Records (10):** clock-in, clock-out, today, my-history, all, get, update, manual, school-mode, bulk-school-mode
**Tasks (6):** add, today's-tasks, update, delete, complete, assign
**Reports (2):** productivity, alerts
**Geofences (4):** create, list, update, delete
**Policies (4):** create, list, update, delete
**Health (1):** health check

### Database (4 tables)
- **attendance_records**: employee_id+date unique, GPS coords, work/overtime hours, status, method, day_rating (1-5)
- **attendance_tasks**: title, details, estimated_finish_time, expected/actual_expenses, status, completion_notes
- **geofence_locations**: name, lat/lng center, radius_meters (default 200), is_active
- **attendance_policies**: method (manual/geofence/both), geofence_id FK, work_start_time, work_hours_per_day

### Key Technical Decisions
- Policy resolution chain: employee-specific → department-level → company default
- Geofence validation at both clock-in AND clock-out
- Inline task completion during clock-out (batch update tasks in same request)
- Events: `attendance.clock_in`, `attendance.clock_out`, `attendance.manual_entry`, `attendance.school_mode_entry`

---

## 4. Leave Service (Port 8005)

### Bounded Context
Leave & Absence Management

### Aggregate Roots
- **LeaveRequest**
- **LeaveType**
- **LeaveBalance**

### What's Implemented
- Leave application with 3-day intimation policy enforcement
- Multi-level approval workflow (PROJECT_IN_CHARGE → HR → SUPER_ADMIN)
- Holiday-aware business day calculation (weekends + company holidays excluded)
- Leave balance tracking (total, used, pending, remaining)
- Concurrent balance protection (`SELECT ... FOR UPDATE`)
- Overlapping leave prevention
- Bulk balance allocation
- Leave calendar view (approved leaves by date range)
- Holiday management with in-memory cache (5-min TTL)
- Emergency leave bypass for intimation rule
- Rate limiting: 10/min on leave application

### API Endpoints (16)

**Leave Requests (3):** apply, list, approve/reject/cancel
**Leave Types (4):** list, create, update, soft-delete
**Leave Balances (4):** get-for-employee, create, update, bulk-allocate
**Holidays (3):** create, list, soft-delete
**Leave Calendar (1):** date-range view
**Health (1):** health check

### Database (5 tables)
- **leave_types**: name, days_allowed, requires_approval, is_active
- **leave_balances**: employee_id, leave_type_id, total/used/pending_days, year
- **leave_requests**: start/end_date, total_days, duration_type, is_emergency, status, reason
- **leave_approvals**: leave_request_id, approver_id, level, status, remarks
- **holidays**: name, date, description, is_active

### Key Technical Decisions
- Multi-level sequential approval chain with per-level records
- Balance holds: pending_days reserved at application, moved to used_days on approval
- Business day calculation excludes both weekends and tenant-specific holidays
- Events: `leave.requested`, `leave.approved.{level}`, `leave.rejected`, `leave.cancelled`, `leave.emergency`

---

## 5. Payroll Service (Port 8004)

### Bounded Context
Compensation & Payroll Processing

### Aggregate Roots
- **PayrollRun**
- **SalaryStructure**
- **EmployeeSalary**

### What's Implemented
- Salary structure management (percentage-based components)
- Employee salary assignment with cross-service employee validation
- Payroll execution: DRAFT → PROCESSING → COMPLETED/FAILED
- Idempotent payroll runs (unique constraint on company+period)
- Atomic payslip generation (nested transaction)
- Snapshot-based payslips (salary frozen at processing time)
- India-standard tax rules: PF (capped at ₹15K basic), ESI (gross ≤ ₹21K), Professional Tax
- Strategy pattern for regional calculation variants (BaseSalaryCalculator)
- Employee self-service payslip view (`/my-payslips`)
- Precise decimal arithmetic (ROUND_HALF_UP)
- Event consumption: `employee.created` (logged, no auto-action)
- Event publishing: `payroll.run` on completion

### API Endpoints (13)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/payroll/run` | Execute payroll |
| GET | `/api/v1/payroll/runs` | List runs |
| GET | `/api/v1/payroll/runs/{id}` | Get run |
| GET | `/api/v1/payroll/runs/{id}/payslips` | Run's payslips |
| GET | `/api/v1/payroll/my-payslips` | Own payslips |
| POST | `/api/v1/salary/structures` | Create structure |
| GET | `/api/v1/salary/structures` | List structures |
| GET | `/api/v1/salary/structures/{id}` | Get structure |
| PATCH | `/api/v1/salary/structures/{id}` | Update structure |
| DELETE | `/api/v1/salary/structures/{id}` | Soft-delete |
| POST | `/api/v1/salary/assign` | Assign salary |
| GET | `/api/v1/salary/employee/{id}` | Active salary |
| GET | `/api/v1/salary/employee/{id}/history` | Salary history |

### Database (4 tables)
- **salary_structures**: component percentages (basic, hra, allowances, pf, esi, pt)
- **employee_salaries**: employee_id, structure FK, CTC, effective_from/to, is_active
- **payroll_runs**: period_start/end, status, totals (employees, gross, net, deductions), processed_by
- **payslips**: snapshot of all salary components, gross, deductions, net (immutable)

### Key Technical Decisions
- Salary calculation uses `Decimal` throughout (no floating-point errors)
- PF capped at ₹15,000 basic (India statutory rule)
- ESI only for gross ≤ ₹21,000 (India statutory rule)
- Payslips are snapshots — never reference live salary table
- Cross-service employee validation is fail-open (logs warning, allows request)

---

## 6. Notification Service (Port 8007)

### Bounded Context
Communication & Alerts

### What's Implemented
- Email delivery via aiosmtplib with 3-retry exponential backoff
- Jinja2 HTML templates (employee_created, leave_update, payroll_processed)
- User notification preferences (email/sms enable/disable)
- Preference enforcement before sending
- RabbitMQ event consumption: `leave.*`, `employee.created`, `payroll.run`, `salary.processed`
- Notification log persistence (status: PENDING/SENT/FAILED)
- Dead-letter queue for failed messages

### API Endpoints (4)
- GET `/notifications/logs/` — List logs (RBAC-scoped)
- GET `/notifications/preferences/` — Get/create preferences
- PUT `/notifications/preferences/` — Update preferences
- GET `/health` — Health check

### Database (2 tables)
- **notification_logs**: type (EMAIL/SMS/PUSH), subject, message, status, error_message
- **notification_preferences**: user_id (unique), email_enabled, sms_enabled

---

## 7. Audit Service (Port 8006)

### Bounded Context
Compliance & Audit Trail

### What's Implemented
- Immutable insert-only audit log (no updates/deletes via API)
- RabbitMQ wildcard subscription (`#`) captures ALL system events
- Payload sanitization (redacts passwords, tokens, secrets, bank accounts)
- Event idempotency via unique `event_id` constraint
- Comprehensive filtering (event_type, service_source, user_id, date range, correlation_id)
- CSV export (Super Admin only, rate-limited 5/min, max 10K rows)
- Log retention policy (default 730 days, cleanup at startup)
- DLQ for unparseable or failed messages
- Distributed tracing support via `correlation_id`

### API Endpoints (4)
- GET `/audit/logs` — List with filters (HR, SA)
- GET `/audit/logs/{id}` — Single log (HR, SA)
- GET `/audit/logs/export/csv` — CSV export (SA, 5/min)
- GET `/health` — Health check

### Database (1 table)
- **audit_logs**: event_id (unique), event_type, service_source, company_id, user_id, correlation_id, payload (JSON), ip_address, user_agent, http_method, endpoint, timestamp

---

## 8. Students Service (Port 8003)

### Bounded Context
Academic / Student Management (Education Vertical)

### What's Implemented
- Student lifecycle (enrollment → active → graduated/expelled)
- Class management (grade_level, section, academic_year, capacity)
- Guardian management (relationship types, primary guardian flag, cascade delete)
- Event publishing: `student.enrolled`, `student.status_changed`, `student.graduated`
- Pagination with filtering (status, class_id, academic_year, grade_level)

### API Endpoints (16)
**Students (6):** create, list, get, update, change-status, delete
**Classes (5):** create, list, get, update, delete
**Guardians (5):** add, get, list-by-student, update, delete

### Database (3 tables)
- **students**: student_number (unique), personal info, class_id FK, status enum, enrollment_date
- **classes**: name, grade_level, section, academic_year, capacity
- **guardians**: student_id FK (CASCADE), relationship enum, is_primary, contact info

---

## 9. API Gateway (Nginx — Port 80)

### What's Implemented
- Path-based routing to all 8 backend services
- Rate limiting: 5 req/s (auth login), 30 req/s (general API)
- CORS preflight handling per service block
- Security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection)
- Request ID propagation (X-Request-ID)
- JSON error responses (429, 502, 503, 504)
- Health endpoint aggregation for all services
- Docker internal DNS resolution (valid=10s, survives restarts)
- Timeouts: 3s connect, 10s send/read
- Max body size: 10MB
- Metrics endpoint blocked externally (403)
- Frontend SPA routing to Vue 3 app
