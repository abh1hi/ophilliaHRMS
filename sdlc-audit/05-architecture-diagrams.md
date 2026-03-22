# Architecture Diagrams

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                        │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│   │  Web Browser  │  │  Mobile App  │  │  Admin Panel │  │  API Client  │  │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└──────────┼─────────────────┼─────────────────┼─────────────────┼───────────┘
           │                 │                 │                 │
           └─────────────────┴────────┬────────┴─────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY (Nginx :80)                              │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐ ┌─────────────────┐  │
│  │ Rate Limiter │ │ CORS Handler │ │ Security Hdrs  │ │ Request ID Gen  │  │
│  │ 5r/s login   │ │ Preflight    │ │ X-Frame-Opts   │ │ X-Request-ID    │  │
│  │ 30r/s API    │ │ Per-service  │ │ X-XSS-Protect  │ │ Propagation     │  │
│  └─────────────┘ └──────────────┘ └────────────────┘ └─────────────────┘  │
│                                                                             │
│  Path-Based Routing:                                                        │
│  /api/v1/auth/*          → auth-service:8000                                │
│  /api/v1/employees/*     → employee-service:8001                            │
│  /api/v1/attendance/*    → attendance-service:8002                           │
│  /api/v1/students/*      → students-service:8003                            │
│  /api/v1/payroll/*       → payroll-service:8004                             │
│  /api/v1/salary/*        → payroll-service:8004                             │
│  /api/v1/leave/*         → leave-service:8005                               │
│  /api/v1/audit/*         → audit-service:8006                               │
│  /api/v1/notifications/* → notification-service:8007                        │
│  /                       → frontend:3000                                    │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                    ─────────────────┼──────────────────
                    │  hrms-network (Docker bridge)    │
                    ───────────────────────────────────
                                     │
    ┌────────────────────────────────┼────────────────────────────────────┐
    │                                │                                    │
    │   ┌─────────────────────────────────────────────────────────────┐   │
    │   │                    BACKEND SERVICES                         │   │
    │   │                                                             │   │
    │   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │   │
    │   │  │ Auth Service  │  │ Employee Svc │  │ Attendance Svc   │  │   │
    │   │  │ :8000         │  │ :8001        │  │ :8002            │  │   │
    │   │  │               │  │              │  │                  │  │   │
    │   │  │ • JWT Issue   │  │ • CRUD       │  │ • Clock In/Out   │  │   │
    │   │  │ • RBAC        │  │ • PII Encrypt│  │ • Geofence       │  │   │
    │   │  │ • Companies   │  │ • Departments│  │ • Tasks          │  │   │
    │   │  │ • Magic Links │  │ • Bulk Import│  │ • Policies       │  │   │
    │   │  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘  │   │
    │   │         │                 │                  │              │   │
    │   │  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────────┐  │   │
    │   │  │ Students Svc │  │ Payroll Svc  │  │ Leave Service    │  │   │
    │   │  │ :8003        │  │ :8004        │  │ :8005            │  │   │
    │   │  │              │  │              │  │                  │  │   │
    │   │  │ • Students   │  │ • Salary Str │  │ • Leave Requests │  │   │
    │   │  │ • Classes    │  │ • Payroll Run│  │ • Approvals      │  │   │
    │   │  │ • Guardians  │  │ • Payslips   │  │ • Balances       │  │   │
    │   │  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘  │   │
    │   │         │                 │                  │              │   │
    │   │  ┌──────┴───────┐  ┌──────┴──────────────────┴───────────┐  │   │
    │   │  │ Audit Svc    │  │ Notification Service                │  │   │
    │   │  │ :8006        │  │ :8007                               │  │   │
    │   │  │              │  │                                     │  │   │
    │   │  │ • Event Log  │  │ • Email (SMTP)                     │  │   │
    │   │  │ • CSV Export  │  │ • Preferences                     │  │   │
    │   │  │ • Retention  │  │ • Templates                        │  │   │
    │   │  └──────────────┘  └─────────────────────────────────────┘  │   │
    │   └─────────────────────────────────────────────────────────────┘   │
    │                                                                      │
    │   ┌─────────────────────────────────────────────────────────────┐   │
    │   │                   DATA / INFRA LAYER                        │   │
    │   │                                                             │   │
    │   │  ┌──────────────────┐  ┌───────────────┐  ┌─────────────┐  │   │
    │   │  │ PostgreSQL 16    │  │ RabbitMQ 3.12 │  │ Redis 7     │  │   │
    │   │  │ :5432            │  │ :5672 / :15672│  │ :6379       │  │   │
    │   │  │                  │  │               │  │             │  │   │
    │   │  │ 8 databases:     │  │ • hrms_events │  │ • JWT       │  │   │
    │   │  │ • auth_db        │  │   (topic exch)│  │   blacklist │  │   │
    │   │  │ • employee_db    │  │ • DLQ queues  │  │ • Cache     │  │   │
    │   │  │ • attendance_db  │  │ • Per-service │  │ • AOF       │  │   │
    │   │  │ • students_db    │  │   queues      │  │   persist   │  │   │
    │   │  │ • payroll_db     │  │               │  │ • 100MB max │  │   │
    │   │  │ • leave_db       │  │ ⚠ tmpfs       │  │             │  │   │
    │   │  │ • notification_db│  │ (no persist!) │  │             │  │   │
    │   │  │ • audit_db       │  │               │  │             │  │   │
    │   │  └──────────────────┘  └───────────────┘  └─────────────┘  │   │
    │   └─────────────────────────────────────────────────────────────┘   │
    │                                                                      │
    │   ┌─────────────────────────────────────────────────────────────┐   │
    │   │                     FRONTEND                                │   │
    │   │  ┌──────────────────────────────────────────────────────┐   │   │
    │   │  │  Vue 3 SPA  :3000                                   │   │   │
    │   │  │  Served via Nginx gateway at /                      │   │   │
    │   │  └──────────────────────────────────────────────────────┘   │   │
    │   └─────────────────────────────────────────────────────────────┘   │
    └──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Service Interaction Sequence Diagrams

### 2a. Authentication Flow (Login → API Call)

```
User              Gateway         Auth Service        Redis           PostgreSQL
 │                  │                  │                 │                │
 │  POST /login     │                  │                 │                │
 │─────────────────►│                  │                 │                │
 │                  │  Forward         │                 │                │
 │                  │─────────────────►│                 │                │
 │                  │                  │  Find user      │                │
 │                  │                  │────────────────────────────────►│
 │                  │                  │  User record    │                │
 │                  │                  │◄────────────────────────────────│
 │                  │                  │                 │                │
 │                  │                  │  Verify Argon2  │                │
 │                  │                  │  password hash  │                │
 │                  │                  │                 │                │
 │                  │                  │  Create refresh │                │
 │                  │                  │  token in DB    │                │
 │                  │                  │────────────────────────────────►│
 │                  │                  │                 │                │
 │                  │                  │  Sign JWT       │                │
 │                  │                  │  (RS256 priv)   │                │
 │                  │                  │                 │                │
 │                  │  {access, refresh}│                │                │
 │                  │◄─────────────────│                 │                │
 │  JWT + Refresh   │                  │                 │                │
 │◄─────────────────│                  │                 │                │
 │                  │                  │                 │                │
 │  GET /employees  │                  │                 │                │
 │  (Bearer JWT)    │                  │                 │                │
 │─────────────────►│                  │                 │                │
 │                  │                  │                 │                │
 │                  │  Forward to Employee Service       │                │
 │                  │─────────────────────────────────────►               │
 │                  │               Employee Service     │                │
 │                  │                  │                 │                │
 │                  │                  │  Verify JWT     │                │
 │                  │                  │  (RS256 pub)    │                │
 │                  │                  │                 │                │
 │                  │                  │  Check blacklist│                │
 │                  │                  │────────────────►│                │
 │                  │                  │  Not blacklisted│                │
 │                  │                  │◄────────────────│                │
 │                  │                  │                 │                │
 │                  │                  │  Query employees│                │
 │                  │                  │  WHERE company_id = JWT.company  │
 │                  │                  │────────────────────────────────►│
 │                  │                  │  Results        │                │
 │                  │                  │◄────────────────────────────────│
 │                  │                  │                 │                │
 │  Employee list   │◄────────────────│                 │                │
 │◄─────────────────│                  │                 │                │
```

### 2b. Employee Creation → Cross-Service Event Flow

```
HR User          Gateway       Employee Svc      RabbitMQ         Audit Svc     Notification Svc
 │                 │               │                │                │                │
 │ POST /employees │               │                │                │                │
 │────────────────►│               │                │                │                │
 │                 │──────────────►│                │                │                │
 │                 │               │                │                │                │
 │                 │               │ Validate JWT   │                │                │
 │                 │               │ + RBAC (HR/SA) │                │                │
 │                 │               │                │                │                │
 │                 │               │ Encrypt PII    │                │                │
 │                 │               │ (AES-256-GCM)  │                │                │
 │                 │               │                │                │                │
 │                 │               │ INSERT employee│                │                │
 │                 │               │ ────────►DB    │                │                │
 │                 │               │                │                │                │
 │                 │               │ Publish event  │                │                │
 │                 │               │───────────────►│                │                │
 │                 │               │ employee.created│               │                │
 │                 │               │                │                │                │
 │                 │  201 Created  │                │ Route to       │                │
 │                 │◄──────────────│                │ subscribers    │                │
 │ Employee created│               │                │                │                │
 │◄────────────────│               │                │───────────────►│                │
 │                 │               │                │ audit_queue    │                │
 │                 │               │                │                │                │
 │                 │               │                │ Sanitize payload                │
 │                 │               │                │ INSERT audit_log                │
 │                 │               │                │                │                │
 │                 │               │                │───────────────────────────────►│
 │                 │               │                │ notification_q │                │
 │                 │               │                │                │ Check prefs    │
 │                 │               │                │                │ Render template│
 │                 │               │                │                │ Send email     │
 │                 │               │                │                │ Log to DB      │
```

### 2c. Payroll Run Flow

```
HR User          Gateway       Payroll Svc      Employee Svc     RabbitMQ       Audit/Notif
 │                 │               │                │               │               │
 │ POST /payroll/run│              │                │               │               │
 │────────────────►│               │                │               │               │
 │                 │──────────────►│                │               │               │
 │                 │               │                │               │               │
 │                 │               │ Check idempotency               │               │
 │                 │               │ (company+period unique)         │               │
 │                 │               │                │               │               │
 │                 │               │ Create PayrollRun               │               │
 │                 │               │ Status: DRAFT → PROCESSING      │               │
 │                 │               │                │               │               │
 │                 │               │ Fetch active salaries           │               │
 │                 │               │ ────────►DB    │               │               │
 │                 │               │                │               │               │
 │                 │               │ FOR EACH employee:              │               │
 │                 │               │ ┌─────────────────────┐         │               │
 │                 │               │ │ Get salary structure │         │               │
 │                 │               │ │ Calculate:           │         │               │
 │                 │               │ │  basic = CTC*pct/12  │         │               │
 │                 │               │ │  HRA = CTC*pct/12    │         │               │
 │                 │               │ │  PF = min(basic,15K) │         │               │
 │                 │               │ │  ESI = if gross≤21K  │         │               │
 │                 │               │ │  PT = flat amount    │         │               │
 │                 │               │ │  net = gross - deduct│         │               │
 │                 │               │ │ CREATE payslip       │         │               │
 │                 │               │ └─────────────────────┘         │               │
 │                 │               │                │               │               │
 │                 │               │ Update totals  │               │               │
 │                 │               │ Status: COMPLETED               │               │
 │                 │               │                │               │               │
 │                 │               │ Publish event  │               │               │
 │                 │               │────────────────────────────────►│               │
 │                 │               │ payroll.run    │               │──────────────►│
 │                 │               │                │               │  Audit + Email │
 │                 │  200 OK       │                │               │               │
 │                 │◄──────────────│                │               │               │
 │ PayrollRun resp │               │                │               │               │
 │◄────────────────│               │                │               │               │
```

### 2d. Leave Application → Multi-Level Approval

```
Employee         Gateway        Leave Svc        Employee Svc     RabbitMQ
 │                 │               │                │               │
 │ POST /leave-requests            │                │               │
 │────────────────►│               │                │               │
 │                 │──────────────►│                │               │
 │                 │               │                │               │
 │                 │               │ Validate employee               │
 │                 │               │───────────────►│               │
 │                 │               │ {company_id OK}│               │
 │                 │               │◄───────────────│               │
 │                 │               │                │               │
 │                 │               │ Check overlapping leaves        │
 │                 │               │ Check 3-day intimation          │
 │                 │               │ Check balance (FOR UPDATE)      │
 │                 │               │ Calculate business days         │
 │                 │               │ (exclude weekends + holidays)   │
 │                 │               │                │               │
 │                 │               │ Hold balance:  │               │
 │                 │               │ pending_days += N               │
 │                 │               │                │               │
 │                 │               │ Create approval│               │
 │                 │               │ Level 1: PROJECT_IN_CHARGE      │
 │                 │               │                │               │
 │                 │               │ Publish leave.requested         │
 │                 │               │───────────────────────────────►│
 │ 201 Created     │               │                │               │
 │◄────────────────│               │                │               │
 │                 │               │                │               │
 ═══════════════════════════════════════════════════════════════════
 │                 │               │                │               │
 Manager          Gateway        Leave Svc                         │
 │                 │               │                                │
 │ PUT /leave-requests/{id}/status │                                │
 │ {status: APPROVED}              │                                │
 │────────────────►│               │                                │
 │                 │──────────────►│                                │
 │                 │               │ Approve Level 1                │
 │                 │               │ Create Level 2: HR              │
 │                 │               │ Publish leave.approved.level1   │
 │                 │               │──────────────────────────────►│
 │ 200 OK (still pending)         │                                │
 │◄────────────────│               │                                │
 │                 │               │                                │
 ═══════════════════════════════════════════════════════════════════
 │                 │               │                                │
 HR Admin         Gateway        Leave Svc                         │
 │                 │               │                                │
 │ PUT /leave-requests/{id}/status │                                │
 │ {status: APPROVED}              │                                │
 │────────────────►│               │                                │
 │                 │──────────────►│                                │
 │                 │               │ Approve Level 2 (final)        │
 │                 │               │ pending_days -= N              │
 │                 │               │ used_days += N                 │
 │                 │               │ Request status → APPROVED       │
 │                 │               │ Publish leave.approved          │
 │                 │               │──────────────────────────────►│
 │ 200 OK (approved)              │                                │
 │◄────────────────│               │                                │
```

---

## 3. Event Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RabbitMQ (hrms_events exchange)                   │
│                         Type: TOPIC, Durable                        │
│                                                                     │
│  Routing Keys:                                                      │
│  • employee.created / employee.updated / employee.deactivated       │
│  • attendance.clock_in / attendance.clock_out                       │
│  • attendance.manual_entry / attendance.school_mode_entry            │
│  • leave.requested / leave.approved.* / leave.rejected              │
│  • leave.cancelled / leave.emergency                                │
│  • payroll.run / salary.processed                                   │
└─────────────────────────────────────────┬───────────────────────────┘
                                          │
         ┌────────────────────────────────┼────────────────────────┐
         │                                │                        │
         ▼                                ▼                        ▼
┌─────────────────┐           ┌────────────────────┐   ┌──────────────────┐
│   audit_queue   │           │ notification_queue  │   │  payroll_queue   │
│                 │           │                     │   │                  │
│ Binding: #      │           │ Bindings:           │   │ Bindings:        │
│ (ALL events)    │           │ • leave.*           │   │ • employee.*     │
│                 │           │ • employee.created  │   │                  │
│ ┌─────────────┐ │           │ • payroll.run       │   │ ┌──────────────┐ │
│ │ Audit Svc   │ │           │ • salary.processed  │   │ │ Payroll Svc  │ │
│ │             │ │           │                     │   │ │              │ │
│ │ • Sanitize  │ │           │ ┌─────────────────┐ │   │ │ • Log event  │ │
│ │ • Dedup     │ │           │ │ Notification Svc│ │   │ │ • No auto    │ │
│ │ • Insert    │ │           │ │                 │ │   │ │   action     │ │
│ │ • Immutable │ │           │ │ • Check prefs   │ │   │ └──────────────┘ │
│ └─────────────┘ │           │ │ • Render templ  │ │   └──────────────────┘
│                 │           │ │ • Send email    │ │
│ ┌─────────────┐ │           │ │ • Log status    │ │
│ │ DLQ         │ │           │ └─────────────────┘ │
│ │ audit_dlq   │ │           │                     │
│ └─────────────┘ │           │ ┌─────────────────┐ │
└─────────────────┘           │ │ DLQ             │ │
                              │ │ notification_dlq│ │
                              │ └─────────────────┘ │
                              └────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│             students_events exchange (TOPIC, Durable)               │
│                                                                     │
│  Routing Keys:                                                      │
│  • student.enrolled / student.status_changed / student.graduated    │
│                                                                     │
│  NOTE: Separate exchange from hrms_events — should be unified       │
└─────────────────────────────────────────────────────────────────────┘
```

### Event Publishers & Consumers Matrix

| Service | Publishes | Consumes |
|---------|-----------|----------|
| Auth Service | (none currently) | (none) |
| Employee Service | `employee.created`, `employee.updated`, `employee.deactivated` | (none) |
| Attendance Service | `attendance.clock_in`, `attendance.clock_out`, `attendance.manual_entry`, `attendance.school_mode_entry` | (none) |
| Leave Service | `leave.requested`, `leave.approved.*`, `leave.rejected`, `leave.cancelled`, `leave.emergency` | (none) |
| Payroll Service | `payroll.run` | `employee.created` |
| Students Service | `student.enrolled`, `student.status_changed`, `student.graduated` | (none) |
| Audit Service | (none) | `#` (ALL events via wildcard) |
| Notification Service | (none) | `leave.*`, `employee.created`, `payroll.run`, `salary.processed` |

---

## 4. Data Ownership Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA OWNERSHIP MAP                           │
│                  (Database-per-Service Pattern)                      │
└─────────────────────────────────────────────────────────────────────┘

  ┌───────────────────┐        ┌───────────────────┐
  │   auth_db          │        │   employee_db      │
  │                    │        │                    │
  │ ★ companies        │───────►│ ★ employees        │
  │ ★ users            │ ref    │   (52 columns)     │
  │ ★ refresh_tokens   │        │ ★ departments      │
  │ ★ magic_tokens     │        │                    │
  │                    │        │ PII: AES-256-GCM   │
  │ Owner: Auth Svc    │        │ Owner: Employee Svc│
  └───────────────────┘        └────────┬───────────┘
           │                            │
    company_id + user_id          employee_id
    propagated via JWT            referenced by
           │                            │
           ▼                            ▼
  ┌───────────────────┐        ┌───────────────────┐
  │  attendance_db     │        │   leave_db         │
  │                    │        │                    │
  │ ★ attendance_records│       │ ★ leave_types      │
  │ ★ attendance_tasks │        │ ★ leave_balances   │
  │ ★ geofence_locations│       │ ★ leave_requests   │
  │ ★ attendance_policies│      │ ★ leave_approvals  │
  │                    │        │ ★ holidays         │
  │ Owner: Attendance  │        │                    │
  └───────────────────┘        │ Owner: Leave Svc   │
                                └───────────────────┘

  ┌───────────────────┐        ┌───────────────────┐
  │   payroll_db       │        │  notification_db   │
  │                    │        │                    │
  │ ★ salary_structures│        │ ★ notification_logs│
  │ ★ employee_salaries│        │ ★ notification_prefs│
  │ ★ payroll_runs     │        │                    │
  │ ★ payslips         │        │ Owner: Notif Svc   │
  │                    │        └───────────────────┘
  │ Owner: Payroll Svc │
  └───────────────────┘        ┌───────────────────┐
                                │   audit_db         │
  ┌───────────────────┐        │                    │
  │   students_db      │        │ ★ audit_logs       │
  │                    │        │   (INSERT-ONLY)    │
  │ ★ students         │        │                    │
  │ ★ classes          │        │ Owner: Audit Svc   │
  │ ★ guardians        │        └───────────────────┘
  │                    │
  │ Owner: Students Svc│
  └───────────────────┘

  Legend:
  ★ = Table owned by service (full read/write authority)
  ───► ref = Cross-service reference (via UUID, not FK)
  All tables include company_id for tenant isolation
  No shared databases — each service has its own
```

### Cross-Service Data References (No Direct FK)

| Source Service | References | Target Service | Resolution Method |
|----------------|------------|----------------|-------------------|
| Employee → | user_id | Auth | JWT claim at creation |
| Attendance → | employee_id | Employee | HTTP call to validate |
| Leave → | employee_id | Employee | HTTP call to validate |
| Payroll → | employee_id | Employee | HTTP call to validate |
| Payroll → | salary_structure_id | Payroll (self) | Direct FK |
| Leave → | leave_type_id | Leave (self) | Direct FK |
| Students → | class_id | Students (self) | Direct FK |

---

## 5. Network & Container Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Host (Windows 11)                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              hrms-network (bridge)                          │  │
│  │                                                            │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │  │
│  │  │ Gateway │ │ Frontend│ │Auth:8000│ │Emp:8001 │         │  │
│  │  │ :80  ◄──┼─┤ :3000   │ │ 1CPU    │ │ 1CPU    │         │  │
│  │  │ EXPOSED │ │ 0.5CPU  │ │ 768MB   │ │ 768MB   │         │  │
│  │  └─────────┘ │ 512MB   │ └─────────┘ └─────────┘         │  │
│  │              └─────────┘                                   │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │  │
│  │  │Att:8002 │ │Stu:8003 │ │Pay:8004 │ │Leav:8005│         │  │
│  │  │ 1CPU    │ │ 1CPU    │ │ 1CPU    │ │ 1CPU    │         │  │
│  │  │ 768MB   │ │ 768MB   │ │ 768MB   │ │ 768MB   │         │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │  │
│  │                                                            │  │
│  │  ┌─────────┐ ┌─────────┐                                  │  │
│  │  │Aud:8006 │ │Not:8007 │                                  │  │
│  │  │ 1CPU    │ │ 1CPU    │                                  │  │
│  │  │ 768MB   │ │ 768MB   │                                  │  │
│  │  └─────────┘ └─────────┘                                  │  │
│  │                                                            │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌───────────┐          │  │
│  │  │ PostgreSQL   │ │ RabbitMQ     │ │ Redis     │          │  │
│  │  │ :5432        │ │ :5672/:15672 │ │ :6379     │          │  │
│  │  │ 1CPU/1024MB  │ │ 1CPU/768MB   │ │ 0.25CPU   │          │  │
│  │  │ Volume:      │ │ ⚠ tmpfs     │ │ 200MB     │          │  │
│  │  │ hrms-db-data │ │ (volatile!)  │ │ Vol:      │          │  │
│  │  │              │ │              │ │ redis-data│          │  │
│  │  └──────────────┘ └──────────────┘ └───────────┘          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Estimated Total Resources: ~10 CPU cores, ~9GB RAM              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Ideal Future-State Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FUTURE STATE                                │
└─────────────────────────────────────────────────────────────────────┘

  Internet
     │
     ▼
  [CDN / CloudFlare]
     │
     ▼
  [Load Balancer (ALB/NLB)]
     │
     ├──► [API Gateway (Kong/AWS API GW)]
     │         │
     │         ├── Auth Service (2+ replicas)
     │         ├── Employee Service (2+ replicas)
     │         ├── Attendance Service (2+ replicas)
     │         ├── Leave Service (2+ replicas)
     │         ├── Payroll Service (2+ replicas)
     │         ├── Notification Service (2+ replicas)
     │         ├── Audit Service (2+ replicas)
     │         ├── Students Service (2+ replicas)
     │         ├── Organization Service (NEW)
     │         ├── Recruitment Service (NEW)
     │         ├── Performance Service (NEW)
     │         ├── Reporting Service (NEW)
     │         ├── Workflow Engine (NEW)
     │         └── Document Service (NEW)
     │
     ├──► [Frontend CDN] ──► Vue 3 SPA (S3/CloudFront)
     │
     ▼
  [Service Mesh (Istio/Linkerd)]
     │
     ├── mTLS between all services
     ├── Circuit breakers
     ├── Retry policies
     └── Observability sidecar

  [Data Layer]
     ├── PostgreSQL (RDS, Multi-AZ, Read Replicas)
     ├── RabbitMQ Cluster (3 nodes) or Amazon MQ
     ├── Redis Cluster (ElastiCache, 3 nodes)
     ├── S3 (Document storage)
     └── Elasticsearch (Audit log search)

  [Observability]
     ├── Prometheus + Grafana (Metrics)
     ├── Loki / ELK (Centralized Logging)
     ├── Jaeger / Tempo (Distributed Tracing)
     └── PagerDuty / OpsGenie (Alerting)

  [Security]
     ├── HashiCorp Vault (Secrets)
     ├── Cert-Manager (TLS automation)
     └── OWASP ZAP (Security scanning in CI)

  [Orchestration]
     └── Kubernetes (EKS/GKE)
          ├── Horizontal Pod Autoscaler
          ├── Pod Disruption Budgets
          ├── Rolling deployments
          └── Namespace per environment
```
