# DDD Bounded Contexts & Domain Analysis

---

## Domain Model Overview

Ophillia HRMS operates across multiple bounded contexts. Each microservice corresponds to one bounded context, following the database-per-service pattern.

---

## Bounded Context Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                      OPHILLIA HRMS DOMAIN MAP                       │
└─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────┐         ┌─────────────────────┐
  │  IDENTITY & ACCESS  │ ──U──►  │    CORE HR          │
  │                     │         │                     │
  │  Auth Service       │         │  Employee Service   │
  │                     │         │                     │
  │  • Company (Tenant) │         │  • Employee         │
  │  • User             │         │  • Department       │
  │  • Token            │         │                     │
  │  • Magic Link       │         │  (References User   │
  │                     │         │   from Identity)    │
  └─────────┬───────────┘         └──────────┬──────────┘
            │                                │
            │ U = Upstream                    │
            │ D = Downstream                  │ Shared Kernel:
            │                                │ employee_id, company_id
            │                                │
  ┌─────────▼───────────┐         ┌──────────▼──────────┐
  │  TIME & ATTENDANCE  │ ◄──D──  │  LEAVE MANAGEMENT   │
  │                     │         │                     │
  │  Attendance Service │         │  Leave Service      │
  │                     │         │                     │
  │  • AttendanceRecord │         │  • LeaveType        │
  │  • AttendanceTask   │         │  • LeaveBalance     │
  │  • GeofenceLocation │         │  • LeaveRequest     │
  │  • AttendancePolicy │         │  • LeaveApproval    │
  │                     │         │  • Holiday          │
  └─────────────────────┘         └─────────────────────┘
            │                                │
            │                                │
  ┌─────────▼───────────┐         ┌──────────▼──────────┐
  │  COMPENSATION       │ ◄──D──  │  COMMUNICATION      │
  │                     │         │                     │
  │  Payroll Service    │         │  Notification Svc   │
  │                     │         │                     │
  │  • SalaryStructure  │         │  • NotificationLog  │
  │  • EmployeeSalary   │         │  • NotifPreference  │
  │  • PayrollRun       │         │                     │
  │  • Payslip          │         │  (Reacts to events  │
  │                     │         │   from all contexts)│
  └─────────────────────┘         └─────────────────────┘

  ┌─────────────────────┐         ┌─────────────────────┐
  │  COMPLIANCE         │         │  EDUCATION          │
  │                     │         │                     │
  │  Audit Service      │         │  Students Service   │
  │                     │         │                     │
  │  • AuditLog         │         │  • Student          │
  │                     │         │  • Class            │
  │  (Consumes ALL      │         │  • Guardian         │
  │   domain events)    │         │                     │
  └─────────────────────┘         └─────────────────────┘

  ════════════════════════════════════════════════════════
  MISSING BOUNDED CONTEXTS (Future)
  ════════════════════════════════════════════════════════

  ┌─────────────────────┐         ┌─────────────────────┐
  │  ORGANIZATION       │         │  TALENT ACQUISITION │
  │                     │         │                     │
  │  Organization Svc   │         │  Recruitment Svc    │
  │                     │         │                     │
  │  • OrgUnit          │         │  • JobPosting       │
  │  • Location         │         │  • Application      │
  │  • CostCenter       │         │  • Interview        │
  │  • ReportingChain   │         │  • Offer            │
  └─────────────────────┘         └─────────────────────┘

  ┌─────────────────────┐         ┌─────────────────────┐
  │  PERFORMANCE        │         │  WORKFLOW           │
  │                     │         │                     │
  │  Performance Svc    │         │  Workflow Engine     │
  │                     │         │                     │
  │  • Goal             │         │  • WorkflowTemplate │
  │  • ReviewCycle      │         │  • WorkflowInstance │
  │  • Review           │         │  • ApprovalStep     │
  │  • PIP              │         │  • Delegation       │
  └─────────────────────┘         └─────────────────────┘
```

---

## Context Relationships

| Relationship | Type | Description |
|-------------|------|-------------|
| Identity → Core HR | Upstream/Downstream | Auth creates users; Employee references user_id |
| Core HR → Time & Attendance | Upstream/Downstream | Employee exists before clock-in; attendance validates employee |
| Core HR → Leave Management | Upstream/Downstream | Employee exists before leave application |
| Core HR → Compensation | Upstream/Downstream | Employee exists before salary assignment |
| All → Compliance | Published Language | All services publish events; audit consumes all |
| All → Communication | Published Language | Events trigger notifications |
| Identity → All | Shared Kernel | JWT claims (company_id, user_id, role) shared across all contexts |

---

## Per-Service DDD Analysis

### 1. Identity & Access Context (Auth Service)

**Aggregate Roots:**

| Aggregate | Entities | Value Objects |
|-----------|----------|---------------|
| **Company** | Company | Domain (String), CompanyStatus (Active/Inactive) |
| **User** | User, RefreshToken[], MagicToken[] | Email, HashedPassword, Role (Enum), UserStatus |

**Invariants:**
- Email must be globally unique
- Company name must be globally unique
- User belongs to exactly one company
- Refresh token is revoked on rotation
- Magic token is single-use
- Cannot escalate role beyond own level

**Domain Events (Should Publish):**
- `auth.company_registered`
- `auth.user_registered`
- `auth.user_logged_in`
- `auth.user_logged_out`
- `auth.role_changed`
- `auth.failed_login`

**SRP Check:** ✅ Single responsibility — identity and access only. Company management is borderline (could be separate Organization context).

---

### 2. Core HR Context (Employee Service)

**Aggregate Roots:**

| Aggregate | Entities | Value Objects |
|-----------|----------|---------------|
| **Employee** | Employee | PersonalInfo (name, DOB, gender), Address (door_no, street, village, pin), ContactInfo (phone, email), GovernmentIds (aadhaar, PAN, DL — encrypted), BankDetails (account, IFSC — encrypted), EmergencyContact, Education, WorkHistory, HealthInfo, EmploymentDetails (status, designation, project) |
| **Department** | Department | DepartmentName, ManagerAssignment |

**Invariants:**
- Employee email globally unique
- Employee user_id globally unique
- Department name unique per company
- Employee must have company_id (tenant)
- Terminated employees cannot be re-activated (not enforced — gap)

**Domain Events:**
- `employee.created` ✅
- `employee.updated` ✅
- `employee.deactivated` ✅
- `employee.department_changed` (missing)
- `employee.promoted` (missing)

**SRP Check:** ⚠ Employee model has 52 columns spanning personal, professional, financial, health, and education domains. Consider splitting into sub-aggregates:
- `EmployeeProfile` (personal + contact)
- `EmployeeEmployment` (job details + department)
- `EmployeeFinancial` (bank details, salary reference)
- `EmployeeDocuments` (photos, files)

---

### 3. Time & Attendance Context (Attendance Service)

**Aggregate Roots:**

| Aggregate | Entities | Value Objects |
|-----------|----------|---------------|
| **AttendanceRecord** | AttendanceRecord, AttendanceTask[] | ClockTime, GPSCoordinate (lat, lng), LocationName, WorkHours, OvertimeHours, DayRating (1-5), Status (present/late/half_day/absent), Method (manual/geofence/school_mode) |
| **GeofenceLocation** | GeofenceLocation | Coordinate (lat, lng), Radius, LocationName |
| **AttendancePolicy** | AttendancePolicy | WorkSchedule (start_time, hours_per_day), AttendanceMethod, PolicyScope (employee/department/default) |

**Invariants:**
- One attendance record per employee per day
- Clock-out requires prior clock-in
- Geofence validation: distance ≤ radius
- Policy resolution: employee > department > default
- Tasks belong to an attendance record

**Domain Events:**
- `attendance.clock_in` ✅
- `attendance.clock_out` ✅
- `attendance.manual_entry` ✅
- `attendance.school_mode_entry` ✅
- `attendance.late_alert` (missing — generated in alerts endpoint but not published)

**SRP Check:** ✅ Well-scoped. Tasks are part of the attendance aggregate (daily tasks logged with clock-out). Policies and geofences are supporting aggregates.

---

### 4. Leave Management Context (Leave Service)

**Aggregate Roots:**

| Aggregate | Entities | Value Objects |
|-----------|----------|---------------|
| **LeaveRequest** | LeaveRequest, LeaveApproval[] | DateRange (start, end), TotalDays, DurationType (FULL/HALF), LeaveStatus (PENDING/APPROVED/REJECTED/CANCELLED), Reason, SupportingDocument |
| **LeaveType** | LeaveType | TypeName, DaysAllowed, RequiresApproval |
| **LeaveBalance** | LeaveBalance | TotalDays, UsedDays, PendingDays, Year |
| **Holiday** | Holiday | HolidayDate, HolidayName |

**Invariants:**
- No overlapping leave requests (same employee, overlapping dates)
- Balance must be sufficient: remaining ≥ requested
- 3-day intimation rule (unless emergency)
- Approval chain: PROJECT_IN_CHARGE → HR → SUPER_ADMIN
- Balance: total = used + pending + remaining
- Business days exclude weekends and holidays

**Domain Events:**
- `leave.requested` ✅
- `leave.approved.{level}` ✅
- `leave.approved` (final) ✅
- `leave.rejected` ✅
- `leave.cancelled` ✅
- `leave.emergency` ✅
- `leave.balance_adjusted` (missing)

**SRP Check:** ✅ Well-bounded. Approval workflow is embedded (acceptable for now, should extract to Workflow Engine long-term).

---

### 5. Compensation Context (Payroll Service)

**Aggregate Roots:**

| Aggregate | Entities | Value Objects |
|-----------|----------|---------------|
| **PayrollRun** | PayrollRun, Payslip[] | Period (start, end), RunStatus (DRAFT/PROCESSING/COMPLETED/FAILED), RunTotals (employees, gross, net, deductions) |
| **SalaryStructure** | SalaryStructure | ComponentPercentages (basic, hra, allowances, pf, esi, pt) |
| **EmployeeSalary** | EmployeeSalary | CTC, EffectivePeriod (from, to), StructureReference |

**Invariants:**
- One payroll run per company per period (idempotent)
- Payslip is a snapshot (immutable after creation)
- Salary calculation uses Decimal with ROUND_HALF_UP
- PF capped at ₹15,000 basic
- ESI only if gross ≤ ₹21,000
- PayrollRun status transitions: DRAFT → PROCESSING → COMPLETED/FAILED

**Domain Events:**
- `payroll.run` ✅
- `payroll.payslip_generated` (missing)
- `salary.assigned` (missing)
- `salary.revised` (missing)

**SRP Check:** ✅ Well-bounded. Calculator uses Strategy pattern for regional variants.

---

### 6. Communication Context (Notification Service)

**Aggregate Roots:**

| Aggregate | Entities | Value Objects |
|-----------|----------|---------------|
| **NotificationLog** | NotificationLog | Channel (EMAIL/SMS/PUSH), Subject, Message, DeliveryStatus, ErrorMessage |
| **NotificationPreference** | NotificationPreference | EmailEnabled, SmsEnabled |

**Invariants:**
- Check user preferences before sending
- Log all notification attempts (success or failure)
- Retry with exponential backoff on failure

**Domain Events:** None (consumer only)

**SRP Check:** ✅ Single responsibility — notification delivery and logging.

---

### 7. Compliance Context (Audit Service)

**Aggregate Roots:**

| Aggregate | Entities | Value Objects |
|-----------|----------|---------------|
| **AuditLog** | AuditLog | EventId (idempotency key), EventType, ServiceSource, SanitizedPayload, Timestamp, CorrelationId |

**Invariants:**
- Insert-only (no updates or deletes via API)
- Event deduplication via unique event_id
- Payload sanitization (redact passwords, tokens, secrets)
- Retention policy (default 730 days)

**Domain Events:** None (consumer only)

**SRP Check:** ✅ Single responsibility — immutable audit trail.

---

### 8. Education Context (Students Service)

**Aggregate Roots:**

| Aggregate | Entities | Value Objects |
|-----------|----------|---------------|
| **Student** | Student, Guardian[] | StudentNumber, PersonalInfo, EnrollmentDate, EnrollmentStatus (active/inactive/graduated/expelled) |
| **Class** | Class | ClassName, GradeLevel, Section, AcademicYear, Capacity |

**Invariants:**
- Student number globally unique
- Guardian cascade-deletes with student
- Class capacity should limit enrollment (not enforced — gap)

**Domain Events:**
- `student.enrolled` ✅
- `student.status_changed` ✅
- `student.graduated` ✅

**SRP Check:** ⚠ Missing academic records, grades, and attendance — these would be separate sub-contexts in a full LMS.

---

## Anti-Corruption Layer Analysis

### Where ACLs Are Needed

| Consumer | Provider | Current Coupling | Recommendation |
|----------|----------|-----------------|----------------|
| Attendance → Employee | HTTP call with shared token | Tight coupling (fail-open) | Add ACL: cache employee data locally for 2 min |
| Leave → Employee | HTTP call with shared token | Tight coupling (fail-open) | Add ACL: cache employee data locally for 2 min |
| Payroll → Employee | HTTP call with shared token | Tight coupling (fail-open) | Add ACL: cache employee data locally for 5 min |
| All → Auth | Shared JWT public key | Shared kernel (acceptable) | No change needed |
| Notification → All | Event consumption | Published language (good) | No change needed |
| Audit → All | Wildcard event consumption | Published language (good) | No change needed |

### Shared Kernel

The JWT payload acts as a shared kernel across all bounded contexts:
```json
{
  "sub": "user_id",
  "role": "super_admin|hr|manager|employee",
  "email": "user@company.com",
  "company_id": "tenant_uuid",
  "jti": "token_id"
}
```

**Risk:** Changes to JWT structure require coordinated deployment across all services.
**Mitigation:** JWT schema should be versioned; services should ignore unknown claims.

---

## SOLID Principles Assessment

| Principle | Assessment | Details |
|-----------|-----------|---------|
| **S**ingle Responsibility | ✅ Good | Each service has one bounded context; clean layer separation |
| **O**pen/Closed | ⚠ Partial | Calculator uses Strategy pattern (good); but approval logic is hardcoded |
| **L**iskov Substitution | ✅ Good | Repository interfaces are consistent; services are swappable |
| **I**nterface Segregation | ✅ Good | API endpoints are role-scoped; internal endpoints separated |
| **D**ependency Inversion | ✅ Good | FastAPI DI throughout; repositories injected into services |

---

## Clean Architecture Assessment

```
┌─────────────────────────────────────────┐
│            Frameworks & Drivers          │  FastAPI, SQLAlchemy, aio-pika
│  (Outermost)                            │  Pydantic, Redis, Nginx
├─────────────────────────────────────────┤
│            Interface Adapters            │  API Endpoints, Repositories,
│                                         │  Event Publishers/Consumers
├─────────────────────────────────────────┤
│            Application Services          │  Business logic layer
│                                         │  (services/*.py)
├─────────────────────────────────────────┤
│            Domain Entities              │  Models, Schemas, Constants
│  (Innermost)                            │  Value Objects, Enums
└─────────────────────────────────────────┘
```

**Assessment:** The codebase follows Clean Architecture well:
- Domain entities (models/) don't depend on framework code
- Application services (services/) contain business logic
- Interface adapters (api/, repositories/, events/) handle I/O
- Framework concerns (db/session, middleware/) are at the edge

**Gap:** Some business validation is in endpoint handlers instead of service layer (e.g., RBAC checks in routes rather than in domain logic).
