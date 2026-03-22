# 🏗️ OphilliaHRMS — Complete System Design Document

**Version:** 2.0
**Last Updated:** 2026-03-22
**Architecture Type:** Microservices (Database-per-Service)
**Status:** MVP Stage (Production Readiness Score: 58/100)
**Audit Reference:** See `sdlc-audit/` directory for full SDLC audit (12 documents)

---

## 📋 Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Microservices Breakdown](#2-microservices-breakdown)
3. [Architecture Diagram](#3-architecture-diagram)
4. [Service Communication Map](#4-service-communication-map)
5. [Sequence Diagrams (Critical Flows)](#5-sequence-diagrams-critical-flows)
6. [Data Flow Diagram](#6-data-flow-diagram)
7. [API Design Overview](#7-api-design-overview)
8. [Infrastructure & Deployment](#8-infrastructure--deployment)
9. [Security Architecture](#9-security-architecture)
10. [Observability & Debugging Guide](#10-observability--debugging-guide)
11. [Failure Points & Bottlenecks](#11-failure-points--bottlenecks)
12. [Scaling Strategy](#12-scaling-strategy)
13. [Suggested Improvements & New Services](#13-suggested-improvements--new-services)
14. [Developer Onboarding Guide](#14-developer-onboarding-guide)
15. [Request Lifecycle Walkthrough](#15-request-lifecycle-walkthrough)
16. [Top 10 Debugging Commands](#16-top-10-debugging-commands)

---

## 1. 🧠 High-Level Overview

### **System Purpose**
OphilliaHRMS is a **modular, multi-tenant Human Resource Management System** designed to handle:
- **Employee Management** (profiles, departments, organizational hierarchy)
- **Attendance Tracking** (clock-in/out, presence management)
- **Leave Management** (requests, approvals, balances)
- **Payroll Processing** (salary calculation, tax, payslips)
- **Student Management** (for educational institutions)
- **Audit & Compliance** (immutable event logging)
- **Notifications** (email, alerts, event-driven)

### **Core Users**
- **Employees**: Clock in/out, request leaves, view payslips
- **Managers**: Approve leaves, view team attendance, manage departments
- **HR Personnel**: Full system control, payroll processing, employee management
- **Super Admin**: System configuration, role management, audit access

### **System Boundaries**
```
External World
    ↓ (HTTPS/TLS)
┌─────────────────────────────────────┐
│   API Gateway (Nginx)               │ ← Single entry point
│   - Rate limiting                   │
│   - CORS enforcement                │
│   - Logging & Tracing               │
└──────────────┬──────────────────────┘
               ↓
┌──────────────────────────────────────────────────────┐
│         Microservices Network (Docker)               │
│  (Auth, Employee, Attendance, Leave, Payroll, etc)   │
│  - Stateless services                                │
│  - No shared models                                  │
│  - Communication via REST + Events                   │
└──────────────┬──────────────────────────────────────┘
               ↓
┌──────────────────────────────────────────────────────┐
│    Data & Infrastructure Layer                       │
│  - PostgreSQL (DB-per-Service)                       │
│  - RabbitMQ (Event Broker)                           │
│  - Redis (Cache)                                     │
└──────────────────────────────────────────────────────┘
```

---

## 2. 🧩 Microservices Breakdown

### **2.1 Core Services (Always Running)**

#### **Authentication Service** (auth-service:8000)
| Aspect | Details |
|--------|---------|
| **Responsibility** | User login, JWT token generation, credential validation, role assignment |
| **Tech Stack** | FastAPI, Python 3.11, SQLAlchemy |
| **Database** | PostgreSQL (`auth_db`) |
| **Key Features** | JWT RS256 tokens (4096-bit RSA), refresh token rotation (bcrypt-hashed), Argon2id password hashing (19MB/2 iter), magic link auth, company registration, role management |
| **External Deps** | PostgreSQL, Redis (token blacklist), RabbitMQ (event publishing — not yet implemented) |
| **Scaling** | Horizontal (stateless) |
| **Failure Impact** | **CRITICAL**: System becomes inaccessible without authentication |
| **Key Endpoints** | `POST /auth/companies`, `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`, `PUT /auth/me`, `POST /auth/forgot-password`, `POST /auth/reset-password`, `POST /auth/magic-link/request`, `POST /auth/magic-link/verify`, `GET /auth/users`, `PUT /auth/users/{id}/role`, `POST /auth/admin/create-admin` |

#### **Employee Service** (employee-service:8001)
| Aspect | Details |
|--------|---------|
| **Responsibility** | Employee profiles, departments, organizational structure |
| **Tech Stack** | FastAPI, Python 3.11, SQLAlchemy |
| **Database** | PostgreSQL (`employee_db`) |
| **Key Features** | Department management, employee profiles (52-column model), AES-256-GCM PII encryption (Aadhaar, PAN, bank details), bulk import, photo upload, manager hierarchy |
| **External Deps** | Auth Service (token validation), RabbitMQ (publishes employee.created/updated/deactivated) |
| **Scaling** | Horizontal (stateless) |
| **Failure Impact** | **HIGH**: Breaks employee lookups, organizational queries |
| **Key Endpoints** | `POST /employees`, `GET /employees`, `GET /employees/me`, `GET /employees/{id}`, `PUT /employees/{id}`, `DELETE /employees/{id}`, `POST /employees/bulk`, `POST /employees/{id}/photo`, `GET /departments`, `POST /departments`, `PUT /departments/{id}`, `DELETE /departments/{id}`, `GET /internal/employees/{id}` |

#### **Attendance Service** (attendance-service:8002)
| Aspect | Details |
|--------|---------|
| **Responsibility** | Clock-in/out tracking, presence logs, daily attendance records |
| **Tech Stack** | FastAPI, Python 3.11, SQLAlchemy |
| **Database** | PostgreSQL (`attendance_db`) |
| **Key Features** | Geofence validation (Haversine distance), task management, day rating (1-5), school mode, attendance policies (employee/department/default scope), manual entry, overtime calculation |
| **External Deps** | Auth Service, Employee Service (REST), RabbitMQ (publishes clock_in/clock_out/manual_entry/school_mode events) |
| **Scaling** | Horizontal (stateless) |
| **Failure Impact** | **HIGH**: Employees cannot log attendance |
| **Key Endpoints** | `POST /attendance/clock-in`, `POST /attendance/clock-out`, `POST /attendance/manual`, `POST /attendance/school-mode`, `GET /attendance`, `GET /attendance/summary`, `GET /attendance/alerts`, `POST /attendance/tasks`, `GET /geofence-locations`, `POST /geofence-locations`, `GET /attendance-policies`, `POST /attendance-policies` |

#### **Notification Service** (notification-service:8007)
| Aspect | Details |
|--------|---------|
| **Responsibility** | Email notifications, event-driven alerts, preference management |
| **Tech Stack** | FastAPI, Python 3.11, Email libraries |
| **Database** | PostgreSQL (`notification_db`) |
| **Key Features** | Email queue, notification templates, user preferences |
| **External Deps** | RabbitMQ (consumer), SMTP server, PostgreSQL |
| **Scaling** | Horizontal (event-driven) |
| **Failure Impact** | **MEDIUM**: Users don't receive alerts; system continues |
| **Key Endpoints** | `GET /notifications/preferences`, `PATCH /notifications/preferences/{user_id}` |

#### **Audit Service** (audit-service:8006)
| Aspect | Details |
|--------|---------|
| **Responsibility** | Immutable event logging, compliance tracking, system audit trail |
| **Tech Stack** | FastAPI, Python 3.11, Event Consumer |
| **Database** | PostgreSQL (`audit_db`) |
| **Key Features** | Consumes all events from RabbitMQ, immutable append-only logs |
| **External Deps** | RabbitMQ (mandatory consumer), PostgreSQL |
| **Scaling** | Horizontal (event-driven, append-only) |
| **Failure Impact** | **MEDIUM**: Audit trail incomplete; legal/compliance risk |
| **Key Endpoints** | `GET /audit/logs`, `GET /audit/logs/{entity_type}` |

---

### **2.2 HR Module Services (Profile: "hr")**

#### **Leave Service** (leave-service:8005)
| Aspect | Details |
|--------|---------|
| **Responsibility** | Leave requests, approvals, balance tracking, holiday management |
| **Tech Stack** | FastAPI, Python 3.11, SQLAlchemy |
| **Database** | PostgreSQL (`leave_db`) |
| **Key Features** | Leave types with configurable days, multi-level approval chain (PROJECT_IN_CHARGE → HR → SUPER_ADMIN), balance tracking (used+pending+remaining), overlap detection, 3-day intimation rule, emergency leave, business day calculation (excludes weekends/holidays), holiday management |
| **External Deps** | Employee Service (REST), Auth Service, RabbitMQ (publishes leave.requested/approved/rejected/cancelled/emergency) |
| **Scaling** | Horizontal (stateless) |
| **Failure Impact** | **HIGH**: Cannot request/approve leaves |
| **Key Endpoints** | `POST /leave-requests`, `GET /leave-requests`, `GET /leave-requests/me`, `POST /leave-requests/{id}/approve`, `POST /leave-requests/{id}/reject`, `POST /leave-requests/{id}/cancel`, `GET /leave-balances`, `POST /leave-balances/initialize`, `GET /leave-types`, `POST /leave-types`, `GET /holidays`, `POST /holidays` |

#### **Payroll Service** (payroll-service:8004)
| Aspect | Details |
|--------|---------|
| **Responsibility** | Salary calculation, tax computation, payslip generation |
| **Tech Stack** | FastAPI, Python 3.11, SQLAlchemy |
| **Database** | PostgreSQL (`payroll_db`) |
| **Key Features** | India-standard payroll: PF (capped at ₹15K basic), ESI (gross ≤ ₹21K), Professional Tax; salary structures with component percentages; Strategy pattern calculator for regional variants; Decimal precision (ROUND_HALF_UP); idempotent payroll runs (DRAFT → PROCESSING → COMPLETED/FAILED); payslip snapshots |
| **External Deps** | Employee Service (REST), RabbitMQ (publishes payroll.run event) |
| **Scaling** | Vertical preferred (complex calculations) |
| **Failure Impact** | **CRITICAL**: Cannot run payroll, salary processing blocked |
| **Key Endpoints** | `POST /payroll/run`, `GET /payroll/runs`, `GET /payroll/payslips`, `GET /payroll/payslips/me`, `GET /payroll/payslips/{id}`, `POST /salary/structures`, `GET /salary/structures`, `POST /salary/assign`, `GET /salary/employee/{id}` |

---

### **2.3 Student Module Services (Profile: "student")**

#### **Students Service** (students-service:8003)
| Aspect | Details |
|--------|---------|
| **Responsibility** | Student profiles, classes, guardians, enrollment management |
| **Tech Stack** | FastAPI, Python 3.11, SQLAlchemy |
| **Database** | PostgreSQL (`students_db`) |
| **Key Features** | Guardian relationships, class assignments, student records |
| **External Deps** | Auth Service, RabbitMQ |
| **Scaling** | Horizontal (stateless) |
| **Failure Impact** | **MEDIUM**: Educational functions blocked |
| **Key Endpoints** | `GET /students`, `POST /students`, `GET /students/{id}/guardians`, `POST /classes` |

---

### **2.4 Infrastructure Services**

#### **API Gateway (Nginx)**
| Component | Details |
|-----------|---------|
| **Role** | Single entry point, reverse proxy, rate limiting, logging |
| **Port** | 80 (HTTP), should be 443 (HTTPS) in production |
| **Features** | Request routing, header injection, correlation IDs, CORS |
| **Performance** | Can handle 10k+ concurrent connections (tune worker_processes) |
| **Healthcheck** | HTTP health endpoint at `/health` |

#### **PostgreSQL (Single Master)**
| Component | Details |
|-----------|---------|
| **Role** | Data persistence, database-per-service isolation |
| **Databases** | 8 databases (auth_db, employee_db, attendance_db, leave_db, payroll_db, notification_db, audit_db, students_db) |
| **Port** | 5432 |
| **Resource Limits** | 1024MB RAM, 1.0 vCPU |
| **Scaling Strategy** | Replication to read replicas in prod, multi-region in future |

#### **RabbitMQ (Event Broker)**
| Component | Details |
|-----------|---------|
| **Role** | Asynchronous event publishing/consumption, event bus |
| **Port** | 5672 (AMQP), 15672 (Management UI) |
| **Exchanges** | `hrms_events` (topic exchange), `students_events` (topic exchange — separate for students service) |
| **Consumer Model** | Push-based with manual ack, dead-letter queues (DLQ), 3 retries with exponential backoff |
| **Persistence** | ⚠ **VOLATILE**: Uses tmpfs mount — messages lost on restart. Must migrate to Docker volume for production |

#### **Redis (Cache Layer)**
| Component | Details |
|-----------|---------|
| **Role** | JWT token blacklist (revoked tokens), rate limit counters |
| **Port** | 6379 |
| **Memory Policy** | LRU eviction (100MB max) |
| **Authentication** | ⚠ **NONE**: No AUTH password configured — must add `requirepass` for production |
| **Persistence** | AOF enabled for durability |
| **Scaling** | Single instance (can upgrade to Redis Cluster in prod) |

---

## 3. 🏗️ Architecture Diagram

```mermaid
flowchart TD
    User["👤 User/Browser"]
    Mobile["📱 Mobile App"]
    External["🔗 External Systems"]

    User -->|HTTPS| GW["🚪 API Gateway<br/>Nginx:80"]
    Mobile -->|HTTPS| GW
    External -->|HTTPS| GW

    GW -->|Rate Limit<br/>Routing| Auth["🔐 Auth Service<br/>FastAPI:8000"]
    GW -->|Routing| Emp["👥 Employee Service<br/>FastAPI:8001"]
    GW -->|Routing| Att["📍 Attendance Service<br/>FastAPI:8002"]
    GW -->|Routing| Stud["🎓 Students Service<br/>FastAPI:8003"]
    GW -->|Routing| Pay["💰 Payroll Service<br/>FastAPI:8004"]
    GW -->|Routing| Leave["📅 Leave Service<br/>FastAPI:8005"]
    GW -->|Routing| Audit["📋 Audit Service<br/>FastAPI:8006"]
    GW -->|Routing| Notif["📧 Notification Service<br/>FastAPI:8007"]

    Auth -->|Query| AuthDB["auth_db<br/>PostgreSQL"]
    Emp -->|Query| EmpDB["employee_db<br/>PostgreSQL"]
    Att -->|Query| AttDB["attendance_db<br/>PostgreSQL"]
    Stud -->|Query| StudDB["students_db<br/>PostgreSQL"]
    Pay -->|Query| PayDB["payroll_db<br/>PostgreSQL"]
    Leave -->|Query| LeaveDB["leave_db<br/>PostgreSQL"]
    Audit -->|Query| AuditDB["audit_db<br/>PostgreSQL"]
    Notif -->|Query| NotifDB["notification_db<br/>PostgreSQL"]

    AuthDB ---|Single Instance| PG["🗄️ PostgreSQL:5432<br/>Master"]
    EmpDB ---|Single Instance| PG
    AttDB ---|Single Instance| PG
    StudDB ---|Single Instance| PG
    PayDB ---|Single Instance| PG
    LeaveDB ---|Single Instance| PG
    AuditDB ---|Single Instance| PG
    NotifDB ---|Single Instance| PG

    Emp -->|Publish<br/>Events| RMQ["🐰 RabbitMQ:5672<br/>Event Broker"]
    Att -->|Publish<br/>Events| RMQ
    Pay -->|Publish<br/>Events| RMQ
    Leave -->|Publish<br/>Events| RMQ
    Stud -->|Publish<br/>Events| RMQ

    RMQ -->|Subscribe<br/>Events| Audit
    RMQ -->|Subscribe<br/>Events| Notif

    Auth -->|Token<br/>Blacklist| Redis["⚡ Redis:6379<br/>Cache"]

    PG -->|Backup| Storage["💾 Volumes"]
    RMQ -->|Persist| Storage
    Redis -->|Persist| Storage

    style GW fill:#ff9999
    style Auth fill:#99ccff
    style Emp fill:#99ccff
    style Att fill:#99ccff
    style Stud fill:#99ccff
    style Pay fill:#99ccff
    style Leave fill:#99ccff
    style Audit fill:#99ccff
    style Notif fill:#99ccff
    style PG fill:#99ff99
    style RMQ fill:#ffcc99
    style Redis fill:#ffff99
```

---

## 4. 🔄 Service Communication Map

### **4.1 Synchronous Communication (REST)**

```mermaid
graph LR
    subgraph "REST Calls (Synchronous)"
        Auth["Auth Service"]
        Emp["Employee Service"]
        Att["Attendance Service"]
        Leave["Leave Service"]
        Pay["Payroll Service"]
        Audit["Audit Service"]
    end

    Att -->|GET /employees/{id}| Emp
    Leave -->|GET /employees/{id}| Emp
    Pay -->|GET /employees/{id}| Emp
    Pay -->|GET /attendance/summary| Att
    Att -->|GET /auth/verify| Auth
    Leave -->|GET /auth/verify| Auth
    Emp -->|GET /auth/verify| Auth

    style Att fill:#e1f5ff
    style Emp fill:#e1f5ff
    style Leave fill:#e1f5ff
    style Pay fill:#e1f5ff
```

### **4.2 Asynchronous Communication (RabbitMQ)**

```
Exchange: hrms_events (topic)
═════════════════════════════

[AUTH SERVICE]
  └── (No events published — planned: user.created, user.login, role.changed)

[EMPLOYEE SERVICE]
  ├── employee.created → Audit, Notification
  ├── employee.updated → Audit
  └── employee.deactivated → Audit, Notification

[ATTENDANCE SERVICE]
  ├── attendance.clock_in → Audit
  ├── attendance.clock_out → Audit
  ├── attendance.manual_entry → Audit
  └── attendance.school_mode_entry → Audit

[LEAVE SERVICE]
  ├── leave.requested → Audit, Notification
  ├── leave.approved.{level} → Audit, Notification (per approval level)
  ├── leave.approved → Audit, Notification (final approval)
  ├── leave.rejected → Audit, Notification
  ├── leave.cancelled → Audit
  └── leave.emergency → Audit, Notification

[PAYROLL SERVICE]
  └── payroll.run → Audit, Notification

Exchange: students_events (topic) — ⚠ separate exchange, should unify with hrms_events
═════════════════════════════════

[STUDENTS SERVICE]
  ├── student.enrolled → Audit
  ├── student.status_changed → Audit
  └── student.graduated → Audit

[Consumers]
─────────
AUDIT SERVICE: Wildcard binding (#) on both exchanges — consumes ALL events
NOTIFICATION SERVICE: Selective bindings on employee.*, leave.*, payroll.*
```

### **4.3 Communication Patterns**

| Pattern | Use Case | Retry Strategy | Timeout / Circuit Breaker |
|---------|----------|----------------|---------------------------|
| **REST (Sync)** | Real-time queries (employee lookup, token verify) | Exponential backoff (3 retries) | 5s HTTP timeout via `httpx.AsyncClient(timeout=5.0)` |
| **RabbitMQ (Async)** | Event notifications, audit logging | 3 retries with exponential backoff (2^attempt seconds) | N/A (event-driven) |
| **Cache (Redis)** | Session tokens, rate limit counters | N/A (fail-open) | N/A |

---

## 5. 🔁 Sequence Diagrams (Critical Flows)

### **5.1 User Login & Token Generation**

```mermaid
sequenceDiagram
    actor User
    participant Gateway as API Gateway
    participant AuthSvc as Auth Service
    participant AuthDB as auth_db
    participant Redis as Redis
    participant RMQ as RabbitMQ

    User->>Gateway: POST /auth/login
    Gateway->>Gateway: Rate limit check
    Gateway->>AuthSvc: Forward request

    AuthSvc->>AuthDB: Query user by email
    AuthDB-->>AuthSvc: User record

    AuthSvc->>AuthSvc: Verify password (Argon2id)
    AuthSvc->>AuthSvc: Generate JWT token<br/>(RS256 4096-bit, 15min expiry)
    AuthSvc->>AuthDB: Store refresh token<br/>(bcrypt-hashed, 30 days)

    AuthSvc-->>Gateway: {access_token, refresh_token}
    Gateway-->>User: 200 OK + tokens

    Note over RMQ: Auth service does NOT<br/>publish events yet (planned)
```

### **5.2 Employee Clock-In (Attendance)**

```mermaid
sequenceDiagram
    actor Employee
    participant Gateway as API Gateway
    participant AttSvc as Attendance Service
    participant EmpSvc as Employee Service
    participant AttDB as attendance_db
    participant Redis as Redis
    participant RMQ as RabbitMQ

    Employee->>Gateway: POST /attendance/clock-in<br/>Header: Authorization: Bearer JWT
    Gateway->>Gateway: Extract JWT token
    Gateway->>Gateway: Inject X-Request-ID

    Gateway->>AttSvc: Forward + headers
    AttSvc->>AttSvc: Validate JWT token
    AttSvc->>Redis: Check if user<br/>already clocked in today

    alt Already Clocked In
        AttSvc-->>Employee: 400 Bad Request
    else New Clock-In
        AttSvc->>EmpSvc: GET /employees/{user_id}
        EmpSvc-->>AttSvc: Employee record

        AttSvc->>AttDB: Create attendance record<br/>(clock_in_time, location)
        AttDB-->>AttSvc: Record created

        AttSvc->>Redis: Cache clock-in status
        AttSvc->>RMQ: Publish 'attendance.clock_in'<br/>+ X-Request-ID

        RMQ-->>AttSvc: Event queued
        AttSvc-->>Employee: 201 Created

        RMQ->>AuditSvc: Log event
        RMQ->>NotifSvc: Send notification
    end
```

### **5.3 Leave Request Approval Workflow**

```mermaid
sequenceDiagram
    actor Manager
    participant Gateway as API Gateway
    participant LeaveSvc as Leave Service
    participant EmpSvc as Employee Service
    participant LeaveDB as leave_db
    participant RMQ as RabbitMQ

    Manager->>Gateway: PATCH /leave-requests/{id}/approve
    Gateway->>LeaveSvc: Validate RBAC (role=manager)

    LeaveSvc->>LeaveDB: Fetch leave request
    LeaveDB-->>LeaveSvc: Leave record

    LeaveSvc->>LeaveSvc: Check manager authority<br/>(over requesting employee)
    LeaveSvc->>EmpSvc: GET /employees/{requester_id}
    EmpSvc-->>LeaveSvc: Employee + department

    LeaveSvc->>LeaveDB: Update leave status → 'APPROVED'
    LeaveDB-->>LeaveSvc: Updated record

    LeaveSvc->>RMQ: Publish 'leave.approved'<br/>(user_id, leave_days, approval_date)

    RMQ-->>LeaveSvc: Event queued
    LeaveSvc-->>Manager: 200 OK

    par Async Processing
        RMQ->>AuditSvc: Create audit entry
        RMQ->>NotifSvc: Send approval notification<br/>to employee
        RMQ->>PaySvc: Update leave balance<br/>& salary calculation
    end
```

---

## 6. 🗄️ Data Flow Diagram

```mermaid
flowchart TD
    subgraph "Data Ingestion Layer"
        UI["Vue3 Frontend"]
        API["REST API Calls"]
    end

    subgraph "Processing Layer"
        Gateway["API Gateway<br/>(Routing, Auth, Logging)"]
        AuthSvc["Auth Service<br/>(Token validation)"]
        EmpSvc["Employee Service<br/>(Profile data)"]
        AttSvc["Attendance Service<br/>(Time tracking)"]
        LeaveSvc["Leave Service<br/>(Leave logic)"]
        PaySvc["Payroll Service<br/>(Salary calculation)"]
        AuditSvc["Audit Service<br/>(Logging)"]
    end

    subgraph "Data Storage Layer"
        Cache["Redis Cache<br/>(Sessions, counters)"]
        AuthDB["auth_db"]
        EmpDB["employee_db"]
        AttDB["attendance_db"]
        LeaveDB["leave_db"]
        PayDB["payroll_db"]
        AuditDB["audit_db"]
    end

    subgraph "Event Layer"
        RMQ["RabbitMQ<br/>(Event Bus)"]
    end

    UI -->|HTTP/HTTPS| API
    API -->|Request| Gateway

    Gateway -->|Route| AuthSvc
    Gateway -->|Route| EmpSvc
    Gateway -->|Route| AttSvc
    Gateway -->|Route| LeaveSvc
    Gateway -->|Route| PaySvc

    AuthSvc -->|Query| Cache
    AuthSvc -->|Query| AuthDB
    EmpSvc -->|Query| EmpDB
    AttSvc -->|Query| AttDB
    LeaveSvc -->|Query| LeaveDB
    PaySvc -->|Query| PayDB

    AuthSvc -->|Publish| RMQ
    EmpSvc -->|Publish| RMQ
    AttSvc -->|Publish| RMQ
    LeaveSvc -->|Publish| RMQ
    PaySvc -->|Publish| RMQ

    RMQ -->|Subscribe| AuditSvc
    RMQ -->|Subscribe| NotifSvc["Notification Service"]

    AuditSvc -->|Write| AuditDB
    NotifSvc -->|Store logs| Cache

    style UI fill:#e3f2fd
    style Gateway fill:#ffcccc
    style Cache fill:#ffffcc
    style RMQ fill:#ffcccc
    style AuthDB fill:#ccffcc
    style EmpDB fill:#ccffcc
    style AuditDB fill:#ccffcc
```

### **Data Transformation Example: Attendance Clock-In**

```
INPUT (Client):
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "notes": "At office"
}
    ↓
ENRICHMENT (Service):
{
  "user_id": "from JWT",
  "employee_id": "from Employee Service lookup",
  "clock_in_time": "current timestamp",
  "location": {...},
  "notes": "...",
  "created_at": "ISO timestamp",
  "request_id": "X-Request-ID header"
}
    ↓
STORAGE (Database):
INSERT INTO attendance_records (
  employee_id, clock_in_time, latitude, longitude, notes
) VALUES (...)
    ↓
EVENT (RabbitMQ):
{
  "event_id": "uuid",
  "event_type": "attendance.clock_in",
  "timestamp": "ISO",
  "user_id": "...",
  "employee_id": "...",
  "request_id": "for tracing"
}
    ↓
CONSUMERS:
Audit Service → Logs immutable record
Notification Service → Sends confirmation email
```

---

## 7. 📡 API Design Overview

### **7.1 Authentication Endpoints**

```
Base URL: http://localhost/api/v1/auth

POST   /auth/register
       Body: { email, password, role }
       Response: 201 Created { user_id, email, role }

POST   /auth/login
       Body: { email, password }
       Response: 200 OK { access_token, refresh_token, token_type }

POST   /auth/refresh
       Body: { refresh_token }
       Response: 200 OK { access_token }

GET    /auth/me
       Headers: Authorization: Bearer <access_token>
       Response: 200 OK { user_id, email, role, status }

POST   /auth/logout
       Headers: Authorization: Bearer <access_token>
       Response: 200 OK { message: "Logged out" }
```

### **7.2 Employee Service Endpoints**

```
Base URL: http://localhost/api/v1/employees

GET    /employees/me
       Headers: Authorization: Bearer <token>
       Response: 200 OK { employee_id, name, dept, designation, ... }

GET    /employees?skip=0&limit=100&department_id=<uuid>
       Headers: Authorization: Bearer <token>
       RBAC: hr, manager, super_admin
       Response: 200 OK [ { employee }, ... ]

POST   /employees
       Headers: Authorization: Bearer <token>
       RBAC: super_admin
       Body: { user_id, first_name, last_name, department_id, ... }
       Response: 201 Created { employee_id, ... }

GET    /employees/{employee_id}
       Headers: Authorization: Bearer <token>
       Response: 200 OK { employee_id, name, ... }

PATCH  /employees/{employee_id}
       Headers: Authorization: Bearer <token>
       RBAC: self or super_admin
       Body: { field: new_value, ... }
       Response: 200 OK { updated_employee }

GET    /departments
       Headers: Authorization: Bearer <token>
       Response: 200 OK [ { dept_id, name, manager_id, ... }, ... ]

POST   /departments
       Headers: Authorization: Bearer <token>
       RBAC: super_admin
       Body: { name, description, manager_id }
       Response: 201 Created { dept_id, ... }
```

### **7.3 Attendance Service Endpoints**

```
Base URL: http://localhost/api/v1/attendance

POST   /attendance/clock-in
       Headers: Authorization: Bearer <token>
       Body: { latitude, longitude, notes }
       Response: 201 Created { record_id, clock_in_time, ... }

POST   /attendance/clock-out
       Headers: Authorization: Bearer <token>
       Body: { latitude, longitude, notes }
       Response: 201 Created { record_id, clock_out_time, ... }

GET    /attendance?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
       Headers: Authorization: Bearer <token>
       Response: 200 OK [ { date, clock_in_time, clock_out_time, ... }, ... ]

POST   /attendance/school-mode
       Headers: Authorization: Bearer <token>
       RBAC: hr, super_admin
       Body: { employee_id, status, notes }
       Response: 201 Created { marked_at, status, ... }

GET    /attendance/summary?month=2026-03
       Headers: Authorization: Bearer <token>
       RBAC: hr, manager
       Response: 200 OK { total_hours, present_days, absent_days, ... }
```

### **7.4 Leave Service Endpoints**

```
Base URL: http://localhost/api/v1/leave

GET    /leave-types
       Headers: Authorization: Bearer <token>
       Response: 200 OK [ { type_id, name, days_allowed, ... }, ... ]

POST   /leave-requests
       Headers: Authorization: Bearer <token>
       Body: { leave_type_id, start_date, end_date, reason }
       Response: 201 Created { request_id, status: 'PENDING', ... }

GET    /leave-requests
       Headers: Authorization: Bearer <token>
       Response: 200 OK [ { request_id, status, ... }, ... ]

PATCH  /leave-requests/{request_id}/approve
       Headers: Authorization: Bearer <token>
       RBAC: manager, hr, super_admin
       Body: { comments }
       Response: 200 OK { status: 'APPROVED', ... }

PATCH  /leave-requests/{request_id}/reject
       Headers: Authorization: Bearer <token>
       RBAC: manager, hr, super_admin
       Body: { reason }
       Response: 200 OK { status: 'REJECTED', ... }

GET    /leave-balances
       Headers: Authorization: Bearer <token>
       Response: 200 OK { casual_leaves_used, sick_leaves_used, ... }
```

### **7.5 Payroll Service Endpoints**

```
Base URL: http://localhost/api/v1/payroll

POST   /payroll/run
       Headers: Authorization: Bearer <token>, Idempotency-Key: <uuid>
       RBAC: hr, super_admin
       Body: { month, year, include_adjustments }
       Response: 202 Accepted { payroll_run_id, status: 'PROCESSING', ... }

GET    /payroll/{payroll_run_id}
       Headers: Authorization: Bearer <token>
       Response: 200 OK { payroll_run_id, month, total_salary, ... }

GET    /payroll/payslips/{employee_id}?month=2026-03
       Headers: Authorization: Bearer <token>
       RBAC: self or hr
       Response: 200 OK { payslip_id, gross_salary, deductions, net_salary, ... }

GET    /salary/structure/{employee_id}
       Headers: Authorization: Bearer <token>
       Response: 200 OK { base_salary, allowances, deductions, ... }
```

### **7.6 Audit Service Endpoints**

```
Base URL: http://localhost/api/v1/audit

GET    /audit/logs?entity_type=user&skip=0&limit=100
       Headers: Authorization: Bearer <token>
       RBAC: super_admin
       Response: 200 OK [ { event_id, event_type, user_id, timestamp, ... }, ... ]

GET    /audit/logs/{event_id}
       Headers: Authorization: Bearer <token>
       RBAC: super_admin
       Response: 200 OK { event_id, event_type, payload, ... }
```

### **7.7 Response Format & Error Handling**

**Success Response (2xx):**
```json
{
  "status": "success",
  "message": "Operation completed",
  "data": { ... },
  "timestamp": "2026-03-19T10:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (4xx, 5xx):**
```json
{
  "status": "error",
  "error_code": "INVALID_TOKEN",
  "message": "JWT token has expired",
  "details": { ... },
  "timestamp": "2026-03-19T10:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| **200** | Success | Proceed |
| **201** | Created | Resource created |
| **202** | Accepted | Async operation queued |
| **400** | Bad Request | Fix data & retry |
| **401** | Unauthorized | Re-authenticate |
| **403** | Forbidden | Insufficient permissions |
| **404** | Not Found | Check resource ID |
| **422** | Unprocessable Entity | Validation error in JSON |
| **429** | Too Many Requests | Implement exponential backoff |
| **500** | Server Error | Retry with backoff; escalate to ops |

---

## 8. ⚙️ Infrastructure & Deployment

### **8.1 Deployment Architecture**

```mermaid
graph LR
    subgraph "Development"
        DevDocker["Docker Compose<br/>Local Machine<br/>All Services"]
    end

    subgraph "Staging"
        StageK8s["Kubernetes Cluster<br/>(Optional)<br/>Replicated Services"]
    end

    subgraph "Production"
        ProdK8s["Kubernetes Cluster<br/>or Docker Swarm<br/>Auto-scaling"]
        ProdDB["PostgreSQL RDS<br/>(Master-Slave)"]
        ProdCache["Redis Cluster<br/>High Availability"]
        ProdMsg["RabbitMQ Cluster<br/>3+ Nodes"]
        LB["Load Balancer<br/>(AWS ALB)"]
    end

    DevDocker -->|Build & Test| StageK8s
    StageK8s -->|Promote| ProdK8s
    ProdK8s -->|Uses| ProdDB
    ProdK8s -->|Uses| ProdCache
    ProdK8s -->|Uses| ProdMsg
    LB -->|Routes| ProdK8s
```

### **8.2 Docker Compose Profiles (Local Development)**

```bash
# Core services only (lightweight)
docker compose --profile core up -d

# Full HR system
docker compose --profile core --profile hr up -d

# Full system with students module
docker compose --profile core --profile hr --profile student up -d

# Production simulation (all services)
docker compose --profile core --profile hr --profile student up --build -d
```

### **8.3 Service Resource Allocation (Docker Compose)**

| Service | CPU | Memory | Notes |
|---------|-----|--------|-------|
| Frontend | 0.5 | 512MB | Vue3 development server |
| Gateway | 0.5 | 256MB | Nginx reverse proxy |
| Auth | 0.5 | 512MB | JWT, Argon2id password hashing |
| Employee | 0.5 | 512MB | Employee data, AES-256-GCM encryption |
| Attendance | 0.5 | 512MB | High I/O for location data |
| Leave | 0.5 | 512MB | Leave management |
| Payroll | 1.0 | 512MB | Complex salary calculations |
| Students | 0.5 | 512MB | Student records |
| Notification | 0.5 | 512MB | Email queue worker |
| Audit | 0.5 | 512MB | Event consumer |
| PostgreSQL | 1.0 | 1024MB | Single master (8 databases) |
| RabbitMQ | 0.5 | 512MB | Message broker (⚠ tmpfs storage) |
| Redis | 0.25 | 256MB | Token blacklist, rate limits |
| **TOTAL** | **~7.25** | **~6.5GB** | Requires 4 vCPU, 8GB RAM recommended |

### **8.4 CI/CD Pipeline (Recommended: GitHub Actions)**

```yaml
name: HRMS CI/CD Pipeline

on: [push, pull_request]

jobs:
  lint:
    - Run linting (pylint, black)
    - Check security (bandit)

  test:
    - Unit tests (pytest)
    - Integration tests
    - Coverage > 80%

  build:
    - Build Docker images
    - Push to registry

  deploy-staging:
    - Deploy to staging cluster
    - Run smoke tests
    - Notify team

  deploy-prod:
    - Manual approval required
    - Blue-green deployment
    - Health checks
    - Rollback on failure
```

### **8.5 Environment Configuration**

**Local (.env.local):**
```env
DATABASE_URL=postgresql://postgres:changeme@hrms-db:5432/postgres
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
SMTP_SERVER=localhost
SMTP_PORT=1025
LOG_LEVEL=DEBUG
```

**Production (Secrets Manager):**
- Store in AWS Secrets Manager / Azure Key Vault / HashiCorp Vault
- Inject at container startup
- Rotate keys every 90 days
- Encrypt sensitive fields (JWT secret, DB password)

---

## 9. 🔐 Security Architecture

### **9.1 Authentication & Authorization Flow**

```mermaid
graph TD
    User["User"] -->|1. Credentials| Auth["Auth Service"]
    Auth -->|2. Validate<br/>Argon2id| DB["Database"]
    DB -->|Record| Auth
    Auth -->|3. Generate JWT<br/>RS256| Auth
    Auth -->|4. Store Refresh Token<br/>TTL 30d| Redis["Redis"]
    Auth -->|5. Return Tokens| User

    User -->|6. API Request<br/>+ Access Token| GW["API Gateway"]
    GW -->|7. Validate JWT<br/>Extract Claims| GW
    GW -->|8. Extract role<br/>& permissions| GW

    GW -->|9. Route + Headers| Service["Service"]
    Service -->|10. Double-check<br/>authorization| Service
    Service -->|11. Business Logic| Service
    Service -->|12. Response| GW
    GW -->|13. Response| User
```

### **9.2 RBAC Matrix**

| Role | Auth | Employee | Attendance | Leave | Payroll | Audit |
|------|------|----------|-----------|-------|---------|-------|
| **employee** | Login, Refresh | Read Self | Clock in/out | Request | View Payslip | — |
| **manager** | Login, Refresh | Read Team | View Team | Approve Team | View Team | — |
| **hr** | Login, Refresh | CRUD All | Edit All | Approve All | Run, View | View |
| **super_admin** | All | All | All | All | All | **Full Access** |

### **9.3 JWT Token Structure**

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "email": "user@example.com",
    "role": "manager",
    "company_id": "company_uuid",
    "jti": "token_id",
    "iat": 1710854400,
    "exp": 1710855300
  },
  "signature": "..."
}
```

### **9.4 Data Encryption**

| Type | Method | Implementation | Status |
|------|--------|-----------------|--------|
| **In Transit** | ⚠ **NONE** | No TLS configured — all traffic (client→gateway, gateway→services, services→DB/RabbitMQ/Redis) is plaintext | ❌ CRITICAL GAP |
| **PII at Rest** | AES-256-GCM | Employee service encrypts Aadhaar, PAN, DL, bank details with per-field encryption | ✅ Implemented |
| **Passwords** | Argon2id | 19MB memory cost, 2 iterations, 1 parallelism | ✅ Implemented |
| **Refresh Tokens** | Bcrypt | One-way hashed, stored in DB with 30-day expiry | ✅ Implemented |
| **Magic Link Tokens** | Bcrypt | One-way hashed, single-use, 15-min expiry | ✅ Implemented |
| **JWT Signing** | RS256 | 4096-bit RSA asymmetric key pair | ✅ Implemented |
| **Payroll Data** | ⚠ **NONE** | Salary data stored in plaintext | ❌ GAP |
| **Secrets** | ⚠ `.env` files | Secrets currently in `.env.docker` files tracked in Git — must migrate to vault | ❌ CRITICAL GAP |

### **9.5 Security Hardening Checklist**

**Implemented:**
- ✅ Rate limiting at gateway (Nginx: 5 req/s login, 30 req/s general; slowapi per-endpoint limits)
- ✅ Input validation via Pydantic schemas
- ✅ SQL injection prevention (SQLAlchemy ORM, no string concatenation)
- ✅ XSS prevention (JSON responses, no inline scripts)
- ✅ CORS restriction (explicit method/header whitelists, configurable origins via env var)
- ✅ Database-per-service isolation (8 separate databases)
- ✅ No cross-database queries
- ✅ Audit trail for sensitive operations (with retry-based delivery guarantee)
- ✅ Payload sanitization in audit logs (redacts passwords, tokens, secrets)
- ✅ Database connection pooling (pool_size=20, max_overflow=40, pool_recycle=3600)
- ✅ HTTP timeouts on inter-service calls (5s via httpx.AsyncClient)
- ✅ Graceful shutdown handlers (5s grace period)
- ✅ Privilege escalation guards (cannot grant role above own, cannot change own role)
- ✅ Enumeration protection (forgot-password returns same response always)
- ✅ Multi-tenant row-level isolation (SQLAlchemy ORM event listeners: `do_orm_execute`, `before_flush`)

**Not Implemented (Gaps):**
- ❌ TLS/HTTPS — all traffic is plaintext (CRITICAL)
- ❌ Secrets management — secrets in `.env.docker` files tracked in Git (CRITICAL)
- ❌ Redis authentication — no AUTH password configured
- ❌ RabbitMQ security — using default guest/guest credentials
- ❌ 2FA/MFA — no multi-factor authentication
- ❌ Login attempt tracking / account lockout
- ❌ CSRF tokens — not implemented (stateless JWT API, lower risk)
- ❌ Dependency vulnerability scanning (no safety/snyk in CI)
- ❌ mTLS between services
- ❌ Swagger/OpenAPI docs — accessible in all environments (should disable in production)

---

## 10. 🧪 Observability & Debugging Guide

### **10.1 Logging Strategy**

**Structured JSON Logging Format:**
```json
{
  "timestamp": "2026-03-19T10:30:15.123Z",
  "level": "INFO",
  "service_name": "attendance-service",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-uuid-123",
  "action": "clock_in",
  "duration_ms": 45,
  "status": "success",
  "message": "User clocked in successfully"
}
```

**Log Levels & Thresholds:**
- **ERROR**: System failures, exceptions, 5xx responses → Trigger alerts
- **WARN**: 4xx responses, degraded performance, retries → Log & monitor
- **INFO**: Normal flow, API calls, state changes → Standard logging
- **DEBUG**: Detailed variable values, function entry/exit → Dev only

### **10.2 Centralized Logging (ELK / Loki Stack)**

```mermaid
graph LR
    Auth["Auth Service<br/>stdout: JSON logs"]
    Emp["Employee Service<br/>stdout: JSON logs"]
    Att["Attendance Service<br/>stdout: JSON logs"]

    Auth -->|Aggregate| Fluent["Fluent-bit<br/>Log Aggregator"]
    Emp -->|Aggregate| Fluent
    Att -->|Aggregate| Fluent

    Fluent -->|Ship| ES["Elasticsearch<br/>or Loki"]
    ES -->|Query| Kibana["Kibana<br/>or Grafana"]
    Kibana -->|Visualize| Ops["Ops Team"]
```

**Example Query (Kibana):**
```
service_name: "attendance-service" AND level: "ERROR" AND timestamp > now-1h
```

### **10.3 Metrics & Monitoring (Prometheus + Grafana)**

**Standard Metrics (RED Pattern):**

```
# Requests (Rate)
hrms_http_requests_total{service="auth-service", method="POST", path="/login"}
hrms_http_requests_per_second{service="employee-service"}

# Errors (Rate)
hrms_http_errors_total{service="attendance-service", status="500"}
hrms_error_rate_percent{service="payroll-service"}

# Duration (Latency)
hrms_http_request_duration_seconds{service="leave-service", quantile="0.95"}
hrms_http_request_duration_seconds{service="leave-service", quantile="0.99"}

# Custom Metrics
hrms_active_users{company_id="org-123"}
hrms_attendance_clock_ins_per_hour{department="engineering"}
hrms_payroll_run_duration_seconds{}
hrms_cache_hits_total{service="attendance-service"}
hrms_cache_misses_total{service="attendance-service"}
```

### **10.4 Distributed Tracing (Request ID)**

Every request is tagged with a unique `X-Request-ID` (UUID) that flows through all services:

```
Client Request
    ↓ (X-Request-ID: 550e8400-e29b-41d4-a716-446655440000)
Gateway (logs with request_id)
    ↓ (injects header)
Auth Service (logs with request_id)
    ↓ (forwards to RabbitMQ)
Audit Service (logs with request_id)
```

**Trace Example:**
```bash
# Find all logs for a single request
kubectl logs -f -l app=hrms --all-containers=true | grep "550e8400-e29b-41d4-a716-446655440000"
```

### **10.5 Health Check Endpoints**

Every service implements `/health`:

```json
GET /health

Response 200 OK:
{
  "status": "healthy",
  "service": "attendance-service",
  "timestamp": "2026-03-19T10:30:15Z",
  "checks": {
    "database": "healthy",
    "rabbitmq": "healthy",
    "redis": "healthy",
    "cache_hits": 1250,
    "uptime_seconds": 86400
  }
}

Response 503 Service Unavailable:
{
  "status": "unhealthy",
  "service": "payroll-service",
  "timestamp": "2026-03-19T10:30:15Z",
  "checks": {
    "database": "unhealthy (connection timeout)",
    "rabbitmq": "healthy"
  }
}
```

### **10.6 Common Failure Scenarios & Debugging**

| Scenario | Symptoms | Root Causes | Debug Steps |
|----------|----------|-------------|------------|
| **User Can't Login** | 401 Unauthorized | Wrong password, DB down, JWT expired | Check auth logs, verify DB connectivity |
| **Slow Attendance Clock-In** | Timeout after 30s | Employee Service unreachable, DB slow query | Monitor network latency, check slow query logs |
| **Leave Approval Stuck** | Request stays PENDING | RabbitMQ down, Consumer crashed | Check RabbitMQ mgmt UI, inspect dead-letter queue |
| **Payroll Run Fails** | 500 Server Error | Salary calculation error, concurrent run | Check payroll logs, verify idempotency key, inspect data |
| **Missing Audit Logs** | Gaps in audit trail | Audit Service down, Events dropped | Restart Audit Service, check RabbitMQ queue depth |

---

## 11. ⚠️ Failure Points & Bottlenecks

### **11.1 Single Points of Failure (SPOF)**

```mermaid
graph TD
    subgraph "Critical SPOF"
        PG["PostgreSQL<br/>(Single Master)"]
        RMQ["RabbitMQ<br/>(Single Instance)"]
        Gateway["API Gateway<br/>(Single Nginx)"]
    end

    subgraph "Fault-Tolerant"
        Svcs["Microservices<br/>(Stateless, Horizontal)"]
        Redis["Redis<br/>(Can be replaced)"]
    end

    style PG fill:#ff9999
    style RMQ fill:#ff9999
    style Gateway fill:#ff9999
    style Svcs fill:#99ff99
    style Redis fill:#ffcc99
```

### **11.2 Production Risk Matrix**

| Component | MTBF | MTTR | Impact | Mitigation |
|-----------|------|------|--------|-----------|
| **PostgreSQL** | 99.9% (1h/1000h) | 15-30 min | **Critical** | Master-Slave replication, automated failover |
| **RabbitMQ** | 99.9% | 10-15 min | **High** | RabbitMQ Cluster (3 nodes), durable queues, persistent storage |
| **API Gateway** | 99.95% | 5-10 min | **Critical** | Load balancer + multiple Nginx instances |
| **Auth Service** | 99.9% | 2-3 min | **Critical** | Horizontal scaling (3+ replicas) |
| **Attendance Service** | 99.8% | 2-3 min | **High** | Circuit breaker on Employee Service calls |
| **Redis** | 99.9% | 5 min | **Low** | Sentinel for failover (prod), can survive loss |

### **11.3 Latency Bottlenecks**

```
Client Request → Gateway (2ms)
                → Auth Validation (5ms)
                → Service Route (1ms)
                → DB Query (10-50ms) ← BOTTLENECK
                → RabbitMQ Publish (5ms)
                → Response (1ms)
━━━━━━━━━━━━━━━━━━━━━━
Total: 24-65ms (p95: 100ms, p99: 200ms)
```

**Optimization Strategies (Applied):**
- ✅ Connection pooling configured (pool_size=20, max_overflow=40) → Eliminates per-request handshake overhead
- ✅ HTTP timeouts (5s) on inter-service calls → Prevents cascading latency
- ✅ RabbitMQ publish retry with exponential backoff → Prevents event loss
- Cache frequent queries in Redis (employee lookups) → 1ms
- Index database columns (user_id, created_at) → 5ms reduction
- Pagination (limit 100) → Reduce payload size
- Lazy loading (don't fetch all employee data) → 20ms savings

### **11.4 Scaling Limits**

| Component | Current Limit | Scaling Strategy |
|-----------|---------------|------------------|
| **PostgreSQL** | ~5,000 concurrent connections | Read replicas, sharding by company_id |
| **RabbitMQ** | ~10k messages/sec on single node | RabbitMQ Cluster |
| **Redis** | ~100k ops/sec | Redis Cluster |
| **API Gateway** | ~10k concurrent connections | Load balancer + multiple nodes |
| **Services** | Horizontal: add more containers | K8s HPA (auto-scale on CPU) |

---

## 12. 🚀 Scaling Strategy

### **12.1 Scaling Decision Tree**

```mermaid
graph TD
    A["Monitor Metrics"] -->|CPU > 70%?| B["Vertical or<br/>Horizontal?"]
    A -->|Memory > 80%?| B
    A -->|P95 latency > 200ms?| C["Optimize or<br/>Scale?"]

    B -->|Stateless Service| D["Horizontal Scale<br/>(Add Replicas)"]
    B -->|DB/Cache| E["Vertical Scale<br/>(Increase Resources)"]

    C -->|Add Caching| F["Redis Cache"]
    C -->|DB Slow| G["Index Columns"]
    C -->|Still High| D

    style D fill:#99ff99
    style E fill:#ffcc99
    style F fill:#99ccff
    style G fill:#99ccff
```

### **12.2 Horizontal Scaling (Services)**

**Before (1 replica per service):**
```
auth-service: 1 pod → CPU: 85%, Memory: 350MB
```

**After (3 replicas with load balancer):**
```
auth-service: 3 pods (each 30% CPU, 120MB memory)
Load Balancer → Round Robin
Kubernetes HPA: auto-scale to 5 replicas if CPU > 70%
```

**Kubernetes Configuration:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: hrms/auth-service:latest
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "400Mi"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: auth-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: auth-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### **12.3 Database Scaling**

**Current (Single Master):**
- Write throughput: ~500 TPS
- Read throughput: ~2,000 TPS
- Storage: 100GB (single partition)

**Scaling to 100k+ Employees:**

```mermaid
graph TD
    App["Applications"] -->|Write| Master["PostgreSQL Master<br/>Primary DB"]
    App -->|Read 70%| Replica1["Read Replica 1"]
    App -->|Read 30%| Replica2["Read Replica 2"]

    Master -->|Replication| Replica1
    Master -->|Replication| Replica2

    Master -->|Backups| Archive["AWS S3<br/>Backup Vault"]

    style Master fill:#ff9999
    style Replica1 fill:#99ff99
    style Replica2 fill:#99ff99
```

**Sharding Strategy (for multi-tenant):**
```
Database Shard by company_id:
  - company_id 0-333333 → shard-1
  - company_id 333333-666666 → shard-2
  - company_id 666666-999999 → shard-3

Connection pooling:
  - PgBouncer (or pgpool-II) routes connections
  - Service queries from sharded DB
```

### **12.4 Cache Scaling (Redis)**

**Current (Single Redis):**
```
Max Memory: 100MB
Keys: ~50,000
Hit Rate: 85%
```

**Scaling to Multi-Node (Redis Cluster):**
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --cluster-enabled yes

  nodes:
    - node1:6379 (slot 0-5461)
    - node2:6379 (slot 5462-10922)
    - node3:6379 (slot 10923-16383)

  total_memory: 300MB
  master_slave: yes  (each node has replica)
```

### **12.5 Event Broker Scaling (RabbitMQ)**

**Upgrade from single to cluster:**
```bash
# Current: 1 RabbitMQ node
docker run rabbitmq:3.12-management

# Cluster: 3 nodes (disk, disk, ram)
rabbitmq-1 (master) → rabbitmq-2, rabbitmq-3 join
```

---

## 13. 📦 Suggested Improvements & New Services

### **13.1 Architecture Improvements (High Priority)**

| Improvement | Impact | Effort | Status |
|-------------|--------|--------|--------|
| **Database Connection Pooling** | Reduce connection overhead | Low | ✅ Done |
| **CORS Hardening** | Prevent cross-origin attacks | Low | ✅ Done |
| **HTTP Timeouts** | Prevent cascading failures | Low | ✅ Done |
| **RabbitMQ Retry Logic** | Prevent event loss | Low | ✅ Done |
| **Graceful Shutdown** | Prevent data inconsistency | Low | ✅ Done |
| **Environment-Based Config** | Multi-environment support | Low | ✅ Done |
| **PostgreSQL Read Replicas** | Reduce write lock contention, scale reads | Medium | Planned (2-3 weeks) |
| **RabbitMQ Cluster** | HA for event broker, prevent message loss | Medium | Planned (1-2 weeks) |
| **Redis Sentinel** | Automatic failover for cache layer | Low | Planned (1 week) |
| **mTLS Between Services** | Prevent service spoofing attacks | High | Planned (3-4 weeks) |
| **API Rate Limiting per User** | Prevent abuse, fairer resource allocation | Low | Planned (1 week) |
| **Request Caching** | Reduce DB queries, improve latency | Medium | Planned (2 weeks) |
| **Async Database Migrations** | Zero-downtime schema updates | Medium | Planned (2-3 weeks) |

### **13.2 New Services to Add**

#### **1. 📊 Analytics & Reporting Service (HIGH PRIORITY)**
```yaml
Service: analytics-service:8008
Responsibility:
  - Generate HR analytics dashboards
  - Attendance trends, leave patterns
  - Department-wise performance metrics
  - Payroll analytics & budget forecasting

Tech Stack: FastAPI, PostgreSQL (analytics_db), Pandas, SQL aggregation
Event Consumers: attendance.daily_summary, leave.approved, payroll.run
Key Endpoints:
  - GET /analytics/attendance?month=2026-03&department=eng
  - GET /analytics/leave-trends?quarter=Q1
  - GET /analytics/payroll-forecast?year=2026
Scaling: Horizontal (batch jobs can be scheduled)
Database: Separate analytics_db with materialized views
```

#### **2. 🏢 Configuration & Settings Service (HIGH PRIORITY)**
```yaml
Service: config-service:8009
Responsibility:
  - Global system settings (working hours, fiscal year)
  - Company-wide configurations
  - Feature flags, A/B testing
  - Holiday calendars per region

Tech Stack: FastAPI, PostgreSQL (config_db), Redis cache
Key Endpoints:
  - GET /config/company-settings
  - GET /config/holidays?year=2026&region=US
  - POST /config/feature-flags (admin only)
Scaling: Horizontal, heavy caching in Redis
```

#### **3. 📱 Mobile API Service (MEDIUM PRIORITY)**
```yaml
Service: mobile-api-service:8010
Responsibility:
  - Optimized endpoints for mobile clients
  - Offline sync capabilities
  - Push notification management
  - Device token registration

Tech Stack: FastAPI, Mobile-specific pagination, push service SDK
Key Endpoints:
  - POST /mobile/attendance/clock-in (optimized payload)
  - GET /mobile/my-payslips (cached)
  - POST /mobile/device-tokens (for push)
Scaling: Horizontal
```

#### **4. 💬 Communication & Chat Service (MEDIUM PRIORITY)**
```yaml
Service: chat-service:8011
Responsibility:
  - Real-time messaging between employees
  - Department/team channels
  - Manager-employee 1-on-1 chats
  - WebSocket support for live updates

Tech Stack: FastAPI, WebSockets, Redis (message queue), PostgreSQL (chat_db)
Key Endpoints:
  - WS /chat/messages/{channel_id}
  - POST /chat/channels
  - GET /chat/history/{channel_id}
Scaling: Horizontal, Redis pub/sub for cross-instance messaging
```

#### **5. 🎓 Learning & Development Service (LOW PRIORITY)**
```yaml
Service: learning-service:8012
Responsibility:
  - Training courses & certifications
  - Employee skill tracking
  - Learning progress monitoring
  - Course completion certificates

Tech Stack: FastAPI, PostgreSQL (learning_db)
Key Endpoints:
  - GET /courses
  - POST /courses/{id}/enroll
  - GET /my-progress
Scaling: Horizontal
```

#### **6. 📈 Performance Management Service (HIGH PRIORITY)**
```yaml
Service: performance-service:8013
Responsibility:
  - Employee performance reviews
  - Goal tracking (OKRs)
  - Appraisal management
  - Feedback collection

Tech Stack: FastAPI, PostgreSQL (performance_db)
Key Endpoints:
  - POST /reviews/{employee_id}
  - GET /reviews/my-ratings
  - POST /goals
Scaling: Horizontal
```

#### **7. 🏥 Compliance & Legal Service (HIGH PRIORITY)**
```yaml
Service: compliance-service:8014
Responsibility:
  - Document management (contracts, policies)
  - Compliance checklist tracking
  - Policy acknowledgment tracking
  - Legal holds

Tech Stack: FastAPI, PostgreSQL (compliance_db), Document storage
Key Endpoints:
  - GET /policies
  - POST /policies/{id}/acknowledge
  - GET /compliance-status
Scaling: Horizontal
```

#### **8. 🔔 Advanced Notifications Service (MEDIUM PRIORITY)**
```yaml
Service: advanced-notifications-service:8015
Responsibility:
  - Multi-channel notifications (SMS, push, Slack, Teams)
  - Notification scheduling
  - Smart routing (quiet hours, do-not-disturb)
  - Notification preferences per channel

Tech Stack: FastAPI, PostgreSQL (notifications_db), Twilio/SendGrid
Event Consumers: All system events
Key Endpoints:
  - GET /notifications/settings
  - PATCH /notifications/quiet-hours
Scaling: Horizontal, essential for scale
```

### **13.3 Technology Stack Improvements**

| Component | Current | Recommended | Reason |
|-----------|---------|-------------|--------|
| **API Gateway** | Nginx | Kong or Traefik | Better service discovery, plugin ecosystem |
| **Orchestration** | Docker Compose | Kubernetes (EKS/AKS) | Auto-scaling, self-healing, multi-region |
| **Logging** | stdout | ELK / Loki / Datadog | Centralized, searchable, alerting |
| **Monitoring** | None | Prometheus + Grafana | Real-time metrics, alerting, dashboards |
| **Tracing** | Request ID | Jaeger / Datadog APM | Visual request flows, bottleneck identification |
| **Testing** | pytest | pytest + pytest-cov + Hypothesis | Better mutation testing, property-based testing |
| **Documentation** | Markdown | OpenAPI (Swagger) auto-docs | Auto-generated API docs, client SDKs |
| **Message Queue** | RabbitMQ | Apache Kafka (for scale) | Better log retention, replay, stream processing |

---

## 14. 👨‍💻 Developer Onboarding Guide

### **14.1 Prerequisites**

```bash
# Required tools
- Docker Desktop (latest)
- Git
- Python 3.11+
- Node.js 18+ (for frontend)
- VSCode or PyCharm
- Postman (API testing)

# Recommended tools
- DBeaver (database GUI)
- RabbitMQ Management UI
- Redis CLI (redis-cli)
```

### **14.2 Local Setup (5 minutes)**

```bash
# 1. Clone the repository
git clone https://github.com/yourorg/ophillia-hrms.git
cd ophillia-hrms

# 2. Start all services
docker compose --profile core --profile hr --profile student up -d

# 3. Verify services are running
docker compose ps

# 4. Run database migrations
docker exec hrms-auth python -m alembic upgrade head
docker exec hrms-employee python -m alembic upgrade head
# ... repeat for all services

# 5. Access the system
Frontend: http://localhost:3000
API Gateway: http://localhost/api/v1
RabbitMQ UI: http://localhost:15672 (guest/guest)
PostgreSQL: localhost:5432 (postgres/changeme)
Redis CLI: redis-cli -h localhost
```

### **14.3 Project Structure Navigation**

```
ophilliaHRMS/
├── services/
│   ├── auth-service/          ← Start here: user authentication
│   ├── employee-service/       ← Employee CRUD, departments
│   ├── attendance-service/     ← Clock-in/out tracking
│   ├── leave-service/          ← Leave requests & approvals
│   ├── payroll-service/        ← Salary calculation
│   ├── notification-service/   ← Email alerts
│   ├── audit-service/          ← Event logging
│   ├── students-service/       ← Student management
│   └── gateway/                ← Nginx configuration
│
├── frontend-tailless-ophillia-hrms-vue/  ← Vue3 frontend
│
├── docker-compose.yml          ← Service orchestration
├── docs/                        ← Documentation
│   ├── security_architecture.md
│   ├── logging_observability_standard.md
│   └── frontend_api_integration.md
│
├── contracts/                   ← API contracts
└── SYSTEM_DESIGN_DOCUMENT.md   ← THIS FILE
```

### **14.4 Making Your First Change**

**Task: Add "nickname" field to Employee Profile**

```bash
# Step 1: Create database migration
cd services/employee-service
python -m alembic revision --autogenerate -m "add nickname to employee"

# Step 2: Edit migration file (auto-generated)
# Review: versions/xxxx_add_nickname_to_employee.py
# Ensure: op.add_column('employees', sa.Column('nickname', sa.String(100)))

# Step 3: Update SQLAlchemy model
vim app/models/employee.py
# Add: nickname: str | None = Field(None, max_length=100)

# Step 4: Update Pydantic schema
vim app/schemas/request_response_models.py
# Add: nickname: str | None = None

# Step 5: Update API endpoint
vim app/api/v1/endpoints/employees.py
# Ensure nickname is included in response

# Step 6: Test the change
docker compose up -d
docker exec hrms-employee python -m alembic upgrade head
curl -X GET http://localhost/api/v1/employees/me -H "Authorization: Bearer <token>"

# Step 7: Commit
git add .
git commit -m "feat: add nickname field to employee profiles"
git push origin feature/employee-nickname
```

### **14.5 Testing Your Service**

```bash
# Run unit tests
cd services/auth-service
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Check coverage
pytest --cov=app tests/ --cov-report=html

# Lint code
black .
pylint app/

# Security check
bandit -r app/
```

### **14.6 Debugging Common Issues**

| Issue | Solution |
|-------|----------|
| `Connection refused: PostgreSQL` | `docker compose logs hrms-db` + check port 5432 |
| `RabbitMQ connection timeout` | Visit http://localhost:15672, verify running |
| `JWT token expired` | Refresh token: `POST /auth/refresh` with refresh_token |
| `Permission denied (403)` | Check RBAC: user role must match endpoint requirement |
| `Slow API response (>1s)` | Check DB slow query log, add indexes |
| `Service crashes on startup` | `docker compose logs <service>` to see error |

---

## 15. 📋 Request Lifecycle Walkthrough

### **Example: Employee Requests Leave**

```
TIME: 10:00:00 AM

┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Frontend sends request                                  │
├─────────────────────────────────────────────────────────────────┤
POST /api/v1/leave-requests
Headers: Authorization: Bearer eyJhbGci...

Body:
{
  "leave_type_id": "casual-001",
  "start_date": "2026-04-01",
  "end_date": "2026-04-05",
  "reason": "Family vacation"
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: API Gateway receives request                           │
├─────────────────────────────────────────────────────────────────┤
Gateway (Nginx):
  ✓ Check rate limit (10 req/sec per IP) → PASS
  ✓ Extract JWT from Authorization header
  ✓ Generate X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
  ✓ Log request: {timestamp, method, path, request_id}
  ✓ Route to leave-service:8005
  ✓ Inject headers: X-Request-ID, X-User-ID (from JWT)

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Leave Service processes request                        │
├─────────────────────────────────────────────────────────────────┤
Leave Service:
  1. Middleware: Attach request_id to logging context
  2. Extract JWT from header
  3. Validate JWT signature (RS256) → Valid
  4. Extract claims: user_id=emp-123, role=employee
  5. Check endpoint RBAC: POST /leave-requests → role must be >=employee ✓

  6. Validate request body (Pydantic):
     - leave_type_id exists?
     - dates valid (start < end)?
     - already on leave those dates?
     → All valid

  7. Query database:
     SELECT * FROM leave_types WHERE id = 'casual-001'
     → Returns: {id, name, max_days_per_year, carryover}

  8. Query employee service (REST):
     GET http://employee-service:8001/employees/emp-123
     → Returns: {id, name, department, manager_id}

  9. Create leave record in database:
     INSERT INTO leave_requests (
       employee_id, leave_type_id, start_date, end_date,
       reason, status, created_at, request_id
     ) VALUES (...)
     → Returns: request_id=lr-456

  10. Publish event to RabbitMQ:
      Exchange: hrms.events
      Routing Key: leave.requested
      Message: {
        event_id: uuid(),
        event_type: "leave.requested",
        timestamp: "2026-03-19T10:00:00Z",
        employee_id: "emp-123",
        leave_request_id: "lr-456",
        leave_type: "casual",
        days: 5,
        request_id: "550e8400-e29b-41d4-a716-446655440000"
      }

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Response sent to client                                 │
├─────────────────────────────────────────────────────────────────┤
Response (201 Created):
{
  "status": "success",
  "data": {
    "request_id": "lr-456",
    "employee_id": "emp-123",
    "leave_type": "casual",
    "start_date": "2026-04-01",
    "end_date": "2026-04-05",
    "status": "PENDING",
    "created_at": "2026-03-19T10:00:00Z"
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}

Total latency: 45ms (gateway 2ms + service 35ms + db 8ms)

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Asynchronous event processing                          │
├─────────────────────────────────────────────────────────────────┤
RabbitMQ receives event, routes to subscribers:

AUDIT SERVICE:
  Consumes: leave.requested event
  Action: INSERT INTO audit_logs (
    event_type, user_id, resource, action, timestamp, payload
  ) VALUES (...)
  Result: Immutable audit trail created

NOTIFICATION SERVICE:
  Consumes: leave.requested event
  Action 1: INSERT INTO notification_queue (type='email', ...)
  Action 2: SELECT from email_templates WHERE template_name='leave_requested'
  Action 3: Render template with {employee_name, manager_name, dates}
  Action 4: Send email to manager_email
  Result: Manager receives email notification

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Manager reviews and approves (2 hours later)           │
├─────────────────────────────────────────────────────────────────┤
Manager opens HRMS, sees notification, clicks "Approve"

PATCH /api/v1/leave-requests/lr-456/approve
Headers: Authorization: Bearer eyJhbGci...
Body: { comments: "Approved. Have a great vacation!" }

Leave Service:
  1. Validate JWT: role must be manager, hr, or super_admin
  2. Check authority: manager_id matches authenticated user ✓
  3. Update database:
     UPDATE leave_requests
     SET status='APPROVED', approved_at=NOW(), approved_by=mgr-789
     WHERE id='lr-456'
  4. Publish event: leave.approved
     → Triggers Audit, Notification, Payroll updates

Async Processing:
  - Audit Service: Log approval action
  - Notification Service: Send approval email to employee
  - Payroll Service: Update leave balance calculation

┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: End-to-end tracing                                     │
├─────────────────────────────────────────────────────────────────┤
All logs tagged with same request_id:

time=10:00:00 service=gateway level=info request_id=550e8400... msg="Request received"
time=10:00:01 service=leave-service level=info request_id=550e8400... msg="Leave request created"
time=10:00:02 service=leave-service level=info request_id=550e8400... msg="Event published"
time=10:00:03 service=audit-service level=info request_id=550e8400... msg="Audit logged"
time=10:00:04 service=notification-service level=info request_id=550e8400... msg="Email sent"

Operations team can now:
  - Track complete request through all services
  - Identify bottlenecks (service layer was 35ms)
  - Debug issues by searching for request_id
```

---

## 16. 🔧 Top 10 Debugging Commands / Checks

### **1. Verify All Services Are Running**

```bash
docker compose ps

# Expected output (green "Up" for all):
NAME                    STATUS
hrms-frontend           Up (healthy)
hrms-gateway            Up
hrms-auth               Up (healthy)
hrms-employee           Up (healthy)
hrms-attendance         Up (healthy)
...
hrms-db                 Up (healthy)
hrms-rabbitmq           Up (healthy)
hrms-redis              Up (healthy)
```

### **2. Check Service Logs**

```bash
# Real-time logs (Auth Service)
docker compose logs -f hrms-auth

# Last 100 lines, with timestamps
docker compose logs --tail=100 -t hrms-employee

# Search for errors
docker compose logs hrms-attendance | grep -i error

# Follow specific service + grep for request_id
docker compose logs -f hrms-leave | grep "550e8400-e29b"
```

### **3. Test API Gateway Routing**

```bash
# Check if gateway is running
curl -i http://localhost/health

# Test auth service through gateway
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# Check response headers (should include X-Request-ID)
curl -v http://localhost/api/v1/auth/me \
  -H "Authorization: Bearer <your_token>"
```

### **4. Verify Database Connectivity**

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d postgres
# Password: changeme

# List all databases
\l

# Connect to a specific database
\c auth_db

# List tables
\dt

# Query users
SELECT * FROM users LIMIT 5;

# Check connection count
SELECT count(*) FROM pg_stat_activity;
```

### **5. Monitor RabbitMQ**

```bash
# Open management UI
http://localhost:15672
# Username: guest, Password: guest

# Check queue depth (CLI)
docker exec hrms-rabbitmq rabbitmqctl list_queues

# Monitor message rates
docker exec hrms-rabbitmq rabbitmq-diagnostics -n rabbit queue_memory_breakdown

# Reset RabbitMQ (dangerous: clears all messages)
docker exec hrms-rabbitmq rabbitmqctl reset
```

### **6. Test Redis Cache**

```bash
# Connect to Redis CLI
docker exec -it hrms-redis redis-cli

# Check keys
KEYS *

# View specific key
GET session:user:emp-123

# Monitor real-time commands
MONITOR

# Check memory usage
INFO memory

# Flush cache (dangerous)
FLUSHALL
```

### **7. Test JWT Token Validity**

```bash
# Decode JWT (online at jwt.io or locally)
python3 -c "
import jwt
import json

token = 'eyJhbGc...'
payload = jwt.decode(token, options={'verify_signature': False})
print(json.dumps(payload, indent=2))
"

# Check token expiry
python3 -c "
import jwt
from datetime import datetime

token = 'eyJhbGc...'
payload = jwt.decode(token, options={'verify_signature': False})
exp = payload.get('exp')
print(f'Expires at: {datetime.fromtimestamp(exp)}')
"
```

### **8. Check Service Health**

```bash
# Auth Service health
curl http://localhost:8000/health | jq .

# Employee Service health
curl http://localhost:8001/health | jq .

# Expected response:
{
  "status": "healthy",
  "service": "auth-service",
  "checks": {
    "database": "healthy",
    "rabbitmq": "healthy",
    "redis": "healthy"
  }
}
```

### **9. Profile Database Performance**

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d postgres

# Enable query logging
SET log_min_duration_statement = 100;  -- Log queries > 100ms

# Find slow queries
SELECT query, mean_exec_time FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Analyze query execution plan
EXPLAIN ANALYZE
SELECT * FROM attendance_records
WHERE employee_id = 'emp-123' AND created_at > '2026-03-01';
```

### **10. Rebuild & Clean Environment**

```bash
# Stop all services
docker compose down

# Remove volumes (clears data)
docker compose down -v

# Rebuild all images
docker compose build --no-cache

# Start fresh
docker compose --profile core --profile hr up -d

# Tail logs to verify startup
docker compose logs -f
```

---

## Summary Table: System Checklist

| Component | Status | Criticality | Gaps |
|-----------|--------|-------------|------|
| **Frontend (Vue3)** | ⚠ In Progress | Yes | Separate repo, under development |
| **API Gateway (Nginx)** | ⚠ MVP | Yes | No TLS, no WAF, no IP filtering |
| **Auth Service** | ⚠ MVP | **Critical** | JWT+RBAC+Argon2id working; missing 2FA, login lockout, event publishing |
| **Employee Service** | ⚠ MVP | High | Core CRUD + PII encryption working; 52-col model needs splitting |
| **Attendance Service** | ⚠ MVP | High | Clock-in/out + geofence working; missing shift management, overtime rules |
| **Leave Service** | ⚠ MVP | High | Multi-level approval working; missing accrual cron, department limits |
| **Payroll Service** | ⚠ MVP | **Critical** | India-standard calc working; missing income tax/TDS, PDF payslips |
| **Notification Service** | ⚠ MVP | Medium | Event consumption working; email delivery not connected (no SMTP) |
| **Audit Service** | ✅ Functional | High | Immutable logs, sanitization, DLQ — most complete service |
| **Students Service** | ⚠ MVP | Medium | CRUD working; missing grades, academic records, capacity enforcement |
| **PostgreSQL** | ⚠ Needs Hardening | **Critical** | 8 databases working; no TLS, no backup automation, single master |
| **RabbitMQ** | ❌ Not Production-Ready | High | Events working; **tmpfs = volatile**, default credentials |
| **Redis** | ⚠ Needs Hardening | Medium | Token blacklist working; no AUTH password, fail-open on outage |

---

## 🎯 Next Steps (Based on SDLC Audit — 2026-03-22)

> **Full audit details:** See `sdlc-audit/` directory (12 documents).
> **Current Score:** 58/100 (MVP Stage) → **Target:** 90+/100 (Production-Ready)

### Phase 0: Emergency Security Fixes (Week 1–2) → Score: 58 → ~68
- [ ] Remove all secrets from Git history (BFG Repo-Cleaner)
- [ ] Rotate ALL keys: JWT RSA keys, DB passwords, PII encryption key, service tokens
- [ ] Move secrets to `.env` files excluded from Git (verify .gitignore)
- [ ] Switch RabbitMQ from tmpfs to Docker volume
- [ ] Add Redis AUTH password (`requirepass`)
- [ ] Change RabbitMQ credentials from guest/guest
- [ ] Add TLS termination at Nginx gateway
- [ ] Add `git-secrets` pre-commit hook

### Phase 1: CI/CD & Quality Foundation (Week 3–6) → Score: ~68 → ~75
- [ ] Create shared CI pipeline (GitHub Actions matrix for all 8 services)
- [ ] Add linting (ruff + mypy) and security scanning (bandit + safety)
- [ ] Expand unit tests to 70% coverage
- [ ] Create `ophillia-commons` shared Python package (reduce duplication)
- [ ] Standardize pagination across all services

### Phase 2: Observability & Hardening (Week 7–10) → Score: ~75 → ~82
- [ ] Deploy Loki + Promtail for centralized logging
- [ ] Deploy Prometheus + Grafana with pre-built dashboards
- [ ] Add OpenTelemetry SDK to all services
- [ ] Implement circuit breakers on cross-service HTTP calls
- [ ] Move rate limiting to Redis backend
- [ ] Add database backup automation (pg_dump)

### Phase 3: Missing Core Features (Week 11–18) → Score: ~82 → ~88
- [ ] Build Organization Service (hierarchy, org chart, locations)
- [ ] Build Reporting/Analytics Service (dashboards, KPIs, exports)
- [ ] Add income tax + TDS to Payroll
- [ ] Implement email delivery (SendGrid/SES integration)
- [ ] Implement leave accrual cron
- [ ] Add PDF payslip generation
- [ ] Unify `students_events` → `hrms_events` exchange

### Phase 4: Enterprise Features (Week 19–30) → Score: ~88 → ~93
- [ ] Build Workflow/Approval Engine (extract from leave/payroll)
- [ ] Build Recruitment/ATS Service
- [ ] Build Performance Management Service
- [ ] Add 2FA/MFA to auth service
- [ ] Add contract tests (Pact) for all service boundaries

### Phase 5: Scale & Optimize (Week 31+) → Score: ~93 → ~98
- [ ] Create Kubernetes manifests (Kustomize)
- [ ] Set up managed PostgreSQL (Multi-AZ, read replicas)
- [ ] Deploy HashiCorp Vault for secrets management
- [ ] Implement blue-green deployments
- [ ] SOC 2 / GDPR compliance audit

---

**Document Generated:** 2026-03-19
**Last Updated:** 2026-03-22 (Updated with full SDLC audit findings — see `sdlc-audit/`)
**Architecture Status:** MVP Stage (Production Readiness Score: 58/100)
**Maintenance:** Review quarterly; update on major changes

