OphilliaHRMS — Complete ER Design Document
Database Type: PostgreSQL (per-service isolated databases — microservices architecture)
Architecture: 8 independent services, each with its own PostgreSQL instance. Cross-service references are logical UUIDs only (no physical FK constraints across service boundaries).

1. System Understanding
Core Domains & Services
Service	Database	Core Responsibility
auth-service	auth_db	Multi-tenant identity, JWT, magic-link auth
employee-service	employee_db	HR profiles, departments
attendance-service	attendance_db	Clock-in/out, geofence, tasks
leave-service	leave_db	Leave types, balances, multi-level approval
payroll-service	payroll_db	Salary structures, payslip generation
notification-service	notification_db	Email/SMS/push delivery log
audit-service	audit_db	Immutable event sourcing log
students-service	students_db	Student profiles, classes, guardians
Entity Map (24 tables total)

companies ──< users ──< refresh_tokens
                    └──< magic_tokens

departments ──< employees

geofence_locations ──< attendance_policies
attendance_records ──< attendance_tasks

leave_types ──< leave_balances
leave_types ──< leave_requests ──< leave_approvals
holidays (standalone)

salary_structures ──< employee_salaries
payroll_runs ──< payslips

notification_logs (standalone)
notification_preferences (standalone)

audit_logs (insert-only)

classes ──< students ──< guardians
2. Entities Definition
AUTH SERVICE
companies
Root multi-tenant entity. Every user belongs to exactly one company.

Column	Type	Constraints
id	UUID	PK, default uuid4
name	VARCHAR	NOT NULL, UNIQUE, INDEX
domain	VARCHAR	UNIQUE, INDEX, nullable
is_active	BOOLEAN	NOT NULL, DEFAULT true
created_at	TIMESTAMP	NOT NULL, DEFAULT now()
Indexes: ix_companies_name, ix_companies_domain

users
Authenticated identity. One user per email globally. Linked to a company.

Column	Type	Constraints
id	UUID	PK, default uuid4
company_id	UUID	FK → companies.id, NOT NULL, INDEX
email	VARCHAR	NOT NULL, UNIQUE, INDEX
hashed_password	VARCHAR	nullable (magic-link accounts have no password)
role	VARCHAR	NOT NULL, DEFAULT 'employee', INDEX
is_active	BOOLEAN	NOT NULL, DEFAULT true
created_at	TIMESTAMP	NOT NULL, DEFAULT now()
updated_at	TIMESTAMP	NOT NULL, DEFAULT now(), onupdate
Indexes: ix_users_role, ix_users_created_at, ix_users_company_id

refresh_tokens
JWT refresh tokens. Revocable.

Column	Type	Constraints
id	UUID	PK
user_id	UUID	FK → users.id ON DELETE CASCADE, NOT NULL, INDEX
token_hash	VARCHAR	NOT NULL, INDEX
expires_at	TIMESTAMP	NOT NULL
revoked	BOOLEAN	NOT NULL, DEFAULT false
created_at	TIMESTAMP	NOT NULL, DEFAULT now()
magic_tokens
One-time tokens for passwordless login and password reset.

Column	Type	Constraints
id	UUID	PK
user_id	UUID	FK → users.id ON DELETE CASCADE, NOT NULL, INDEX
token_hash	VARCHAR	NOT NULL, INDEX
expires_at	TIMESTAMP	NOT NULL
used	BOOLEAN	NOT NULL, DEFAULT false
purpose	VARCHAR	NOT NULL (login | reset_password)
created_at	TIMESTAMP	NOT NULL
EMPLOYEE SERVICE
departments
Column	Type	Constraints
id	UUID	PK
name	VARCHAR(150)	NOT NULL, UNIQUE, INDEX
description	VARCHAR(500)	nullable
manager_id	UUID	nullable — logical ref → employees.id (cross-service)
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
Indexes: ix_departments_name, ix_departments_created_at

employees
Core HR profile. Sensitive fields encrypted AES-256-GCM at rest.

Column	Type	Constraints
id	UUID	PK
user_id	UUID	NOT NULL, UNIQUE, INDEX — logical ref → users.id (auth-service)
first_name	VARCHAR(100)	NOT NULL
last_name	VARCHAR(100)	NOT NULL
gender	VARCHAR(10)	nullable
date_of_birth	DATE	nullable
door_no	VARCHAR(50)	nullable
street	VARCHAR(200)	nullable
village_town	VARCHAR(150)	nullable
pin_code	VARCHAR(10)	nullable
phone	VARCHAR(20)	nullable
phone_2	VARCHAR(20)	nullable
personal_email	VARCHAR(255)	nullable
email	VARCHAR(255)	NOT NULL, UNIQUE, INDEX (work email)
driving_license_number	TEXT (encrypted)	nullable
aadhaar_number	TEXT (encrypted)	nullable
uan_number	TEXT (encrypted)	nullable
esi_number	TEXT (encrypted)	nullable
pan_number	TEXT (encrypted)	nullable
bank_account_number	TEXT (encrypted)	nullable
bank_name	VARCHAR(150)	nullable
bank_branch	VARCHAR(150)	nullable
ifsc_code	VARCHAR(11)	nullable
emergency_contact_name	VARCHAR(150)	nullable
emergency_contact_number	VARCHAR(20)	nullable
emergency_contact_relation	VARCHAR(100)	nullable
highest_qualification	VARCHAR(200)	nullable
year_of_passing	VARCHAR(4)	nullable
percentage	VARCHAR(10)	nullable
institute_name	VARCHAR(300)	nullable
last_firm_name	VARCHAR(300)	nullable
years_of_experience	VARCHAR(10)	nullable
last_designation	VARCHAR(100)	nullable
last_drawn_salary	NUMERIC(12,2)	nullable
reason_to_quit	TEXT	nullable
referred_by	VARCHAR(200)	nullable
health_issues	TEXT	nullable
allergies	TEXT	nullable
date_joined	DATE	NOT NULL
department_id	UUID	FK → departments.id ON DELETE SET NULL, nullable, INDEX
designation	VARCHAR(100)	nullable
employment_status	VARCHAR(20)	NOT NULL, DEFAULT 'active', INDEX
project	VARCHAR(200)	nullable
joining_salary	NUMERIC(12,2)	nullable
role	VARCHAR(50)	nullable
staff_photo_url	VARCHAR(500)	nullable
staff_documents_urls	TEXT	nullable (comma-sep/JSON URLs)
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
Indexes: ix_employees_employment_status, ix_employees_department_id, ix_employees_created_at

ATTENDANCE SERVICE
geofence_locations
Column	Type	Constraints
id	UUID	PK
name	VARCHAR(150)	NOT NULL, UNIQUE, INDEX
latitude	FLOAT	NOT NULL
longitude	FLOAT	NOT NULL
radius_meters	INTEGER	NOT NULL, DEFAULT 200
is_active	BOOLEAN	NOT NULL, DEFAULT true
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
attendance_policies
Determines attendance method (manual/geofence/both) per employee or department.

Column	Type	Constraints
id	UUID	PK
department_id	UUID	nullable, INDEX — logical ref (cross-service)
employee_id	UUID	nullable, INDEX — logical ref (cross-service)
method	VARCHAR(20)	NOT NULL, DEFAULT 'manual'
geofence_id	UUID	FK → geofence_locations.id ON DELETE SET NULL, nullable
work_start_time	TIME	nullable, DEFAULT 09:00
work_hours_per_day	FLOAT	NOT NULL, DEFAULT 8.0
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
attendance_records
One row per employee per day. Unique constraint enforces no duplicates.

Column	Type	Constraints
id	UUID	PK
employee_id	UUID	NOT NULL, INDEX — logical ref (cross-service)
clock_in	TIMESTAMP WITH TIME ZONE	NOT NULL
clock_out	TIMESTAMP WITH TIME ZONE	nullable
clock_in_lat	FLOAT	nullable
clock_in_lng	FLOAT	nullable
clock_out_lat	FLOAT	nullable
clock_out_lng	FLOAT	nullable
clock_in_location_name	VARCHAR(200)	nullable
clock_out_location_name	VARCHAR(200)	nullable
work_hours	FLOAT	nullable (computed)
overtime_hours	FLOAT	DEFAULT 0.0
day_rating	INTEGER	nullable (1–5 stars)
status	VARCHAR(20)	NOT NULL, DEFAULT 'present', INDEX
method	VARCHAR(20)	NOT NULL, DEFAULT 'manual'
notes	VARCHAR(500)	nullable
date	DATE	NOT NULL, INDEX
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
Unique: (employee_id, date) — uq_employee_date
Indexes: ix_attendance_employee_date, ix_attendance_status, ix_attendance_created_at

attendance_tasks
Daily tasks logged against an attendance record.

Column	Type	Constraints
id	UUID	PK
company_id	UUID	NOT NULL, INDEX
attendance_record_id	UUID	FK → attendance_records.id ON DELETE CASCADE, NOT NULL, INDEX
employee_id	UUID	NOT NULL, INDEX — logical ref (cross-service)
assigned_by	UUID	nullable — logical ref (cross-service)
title	VARCHAR(200)	NOT NULL
details	TEXT	nullable
estimated_finish_time	VARCHAR(20)	nullable
expected_expenses	NUMERIC(10,2)	nullable
status	VARCHAR(30)	NOT NULL, DEFAULT 'pending', INDEX
completion_notes	TEXT	nullable
actual_expenses	NUMERIC(10,2)	nullable
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
LEAVE SERVICE
leave_types
Column	Type	Constraints
id	UUID	PK
name	VARCHAR(100)	NOT NULL, UNIQUE, INDEX
description	VARCHAR(255)	nullable
days_allowed	INTEGER	NOT NULL
requires_approval	INTEGER	NOT NULL, DEFAULT 1 (1=True)
is_active	INTEGER	NOT NULL, DEFAULT 1
leave_balances
Column	Type	Constraints
id	UUID	PK
employee_id	UUID	NOT NULL, INDEX — logical ref (cross-service)
leave_type_id	UUID	FK → leave_types.id ON DELETE CASCADE, NOT NULL
total_days	INTEGER	NOT NULL, DEFAULT 0
used_days	INTEGER	NOT NULL, DEFAULT 0
pending_days	INTEGER	NOT NULL, DEFAULT 0
year	INTEGER	NOT NULL, INDEX
Index: ix_leave_balance_emp_year (employee_id, year)

leave_requests
Column	Type	Constraints
id	UUID	PK
employee_id	UUID	NOT NULL, INDEX — logical ref (cross-service)
leave_type_id	UUID	FK → leave_types.id ON DELETE CASCADE, NOT NULL
start_date	DATE	NOT NULL
end_date	DATE	NOT NULL
total_days	INTEGER	NOT NULL
duration_type	VARCHAR(20)	NOT NULL, DEFAULT 'FULL_DAY'
is_emergency	INTEGER	NOT NULL, DEFAULT 0
reason	TEXT	NOT NULL
supporting_document	VARCHAR(255)	nullable
status	VARCHAR(20)	NOT NULL, DEFAULT 'pending', INDEX
approved_by_id	UUID	nullable — cache for quick lookup
manager_notes	TEXT	nullable
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
leave_approvals
Column	Type	Constraints
id	UUID	PK
leave_request_id	UUID	FK → leave_requests.id ON DELETE CASCADE, NOT NULL
approver_id	UUID	NOT NULL — logical ref (cross-service)
level	VARCHAR(50)	NOT NULL (PROJECT_IN_CHARGE | HR | SUPER_ADMIN)
status	VARCHAR(20)	NOT NULL, DEFAULT 'pending'
remarks	TEXT	nullable
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
Index: ix_leave_approval_req_level (leave_request_id, level)

holidays
Column	Type	Constraints
id	UUID	PK
name	VARCHAR(100)	NOT NULL
date	DATE	NOT NULL, UNIQUE, INDEX
description	TEXT	nullable
is_active	INTEGER	NOT NULL, DEFAULT 1
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
PAYROLL SERVICE
salary_structures
Column	Type	Constraints
id	UUID	PK
name	VARCHAR(100)	NOT NULL, INDEX
description	TEXT	nullable
basic_pct	NUMERIC(5,2)	NOT NULL, DEFAULT 50.0
hra_pct	NUMERIC(5,2)	NOT NULL, DEFAULT 20.0
allowances_pct	NUMERIC(5,2)	NOT NULL, DEFAULT 15.0
pf_pct	NUMERIC(5,2)	NOT NULL, DEFAULT 12.0
esi_pct	NUMERIC(5,2)	NOT NULL, DEFAULT 1.75
professional_tax	NUMERIC(10,2)	NOT NULL, DEFAULT 200.0
is_active	INTEGER	NOT NULL, DEFAULT 1
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
employee_salaries
Column	Type	Constraints
id	UUID	PK
employee_id	UUID	NOT NULL, INDEX — logical ref (cross-service)
salary_structure_id	UUID	NOT NULL, INDEX — logical ref (same service, missing FK!)
ctc	NUMERIC(12,2)	NOT NULL
effective_from	DATE	NOT NULL
effective_to	DATE	nullable
is_active	INTEGER	NOT NULL, DEFAULT 1
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
Index: idx_emp_salary_active (employee_id, is_active)

payroll_runs
Column	Type	Constraints
id	UUID	PK
company_id	UUID	NOT NULL — from Base class (in UniqueConstraint)
period_start	DATE	NOT NULL
period_end	DATE	NOT NULL
status	VARCHAR(20)	NOT NULL, DEFAULT 'DRAFT', INDEX
total_employees	INTEGER	NOT NULL, DEFAULT 0
total_gross	NUMERIC(14,2)	NOT NULL, DEFAULT 0
total_net	NUMERIC(14,2)	NOT NULL, DEFAULT 0
total_deductions	NUMERIC(14,2)	NOT NULL, DEFAULT 0
processed_by	UUID	nullable — logical ref (cross-service)
error_message	TEXT	nullable
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
Unique: (company_id, period_start, period_end) — idempotency guard

payslips
Column	Type	Constraints
id	UUID	PK
payroll_run_id	UUID	NOT NULL, INDEX — logical ref (same service, missing FK!)
employee_id	UUID	NOT NULL, INDEX — logical ref (cross-service)
ctc	NUMERIC(12,2)	NOT NULL (snapshot)
basic	NUMERIC(10,2)	NOT NULL (snapshot)
hra	NUMERIC(10,2)	NOT NULL (snapshot)
allowances	NUMERIC(10,2)	NOT NULL (snapshot)
pf_deduction	NUMERIC(10,2)	NOT NULL, DEFAULT 0
esi_deduction	NUMERIC(10,2)	NOT NULL, DEFAULT 0
professional_tax	NUMERIC(10,2)	NOT NULL, DEFAULT 0
other_deductions	NUMERIC(10,2)	NOT NULL, DEFAULT 0
gross	NUMERIC(12,2)	NOT NULL
total_deductions	NUMERIC(12,2)	NOT NULL
net	NUMERIC(12,2)	NOT NULL
period_start	DATE	NOT NULL
period_end	DATE	NOT NULL
created_at	TIMESTAMP	NOT NULL
Unique: (payroll_run_id, employee_id) — one payslip per employee per run

NOTIFICATION SERVICE
notification_logs
Column	Type	Constraints
id	UUID	PK
user_id	UUID	NOT NULL, INDEX — logical ref (cross-service)
type	VARCHAR(50)	NOT NULL (EMAIL | SMS | PUSH)
subject	VARCHAR(255)	nullable
message	TEXT	NOT NULL
status	VARCHAR(20)	NOT NULL, DEFAULT 'pending', INDEX
error_message	TEXT	nullable
created_at	TIMESTAMP	NOT NULL
sent_at	TIMESTAMP	nullable
notification_preferences
Column	Type	Constraints
id	UUID	PK
user_id	UUID	NOT NULL, UNIQUE, INDEX
email_enabled	INTEGER	NOT NULL, DEFAULT 1
sms_enabled	INTEGER	NOT NULL, DEFAULT 1
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
AUDIT SERVICE
audit_logs
Insert-only. Never updated or deleted.

Column	Type	Constraints
id	UUID	PK
event_id	UUID	NOT NULL, UNIQUE
event_version	INTEGER	NOT NULL, DEFAULT 1
event_type	VARCHAR(100)	NOT NULL, INDEX
service_source	VARCHAR(100)	NOT NULL, INDEX
company_id	UUID	NOT NULL (from Base), INDEX
user_id	UUID	nullable, INDEX
correlation_id	UUID	nullable, INDEX
ip_address	VARCHAR(50)	nullable
user_agent	VARCHAR(255)	nullable
http_method	VARCHAR(10)	nullable
endpoint	VARCHAR(255)	nullable
payload	JSON	NOT NULL, DEFAULT {}
timestamp	TIMESTAMP	NOT NULL, INDEX
created_at	TIMESTAMP	NOT NULL
STUDENTS SERVICE
classes
Column	Type	Constraints
id	UUID	PK
name	VARCHAR(100)	NOT NULL
grade_level	INTEGER	NOT NULL
section	VARCHAR(10)	NOT NULL
academic_year	VARCHAR(20)	NOT NULL
capacity	INTEGER	NOT NULL, DEFAULT 40
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
students
Column	Type	Constraints
id	UUID	PK
student_number	VARCHAR(50)	NOT NULL, UNIQUE, INDEX
first_name	VARCHAR(100)	NOT NULL
last_name	VARCHAR(100)	NOT NULL
date_of_birth	DATE	NOT NULL
gender	ENUM(male,female,other)	NOT NULL
email	VARCHAR(255)	nullable
phone	VARCHAR(30)	nullable
address	VARCHAR(500)	nullable
class_id	UUID	FK → classes.id ON DELETE SET NULL, nullable, INDEX
enrollment_date	DATE	NOT NULL, DEFAULT today
status	ENUM(active,inactive,graduated,expelled)	NOT NULL, DEFAULT 'active'
created_at	TIMESTAMP	NOT NULL
updated_at	TIMESTAMP	NOT NULL
guardians
Column	Type	Constraints
id	UUID	PK
student_id	UUID	FK → students.id ON DELETE CASCADE, NOT NULL, INDEX
first_name	VARCHAR(100)	NOT NULL
last_name	VARCHAR(100)	NOT NULL
relationship	ENUM(father,mother,legal_guardian,other)	NOT NULL
phone	VARCHAR(30)	NOT NULL
email	VARCHAR(255)	nullable
is_primary	BOOLEAN	NOT NULL, DEFAULT false
created_at	TIMESTAMP	NOT NULL
3. Relationships Definition
#	From	To	Type	FK	ON DELETE	ON UPDATE	Notes
1	companies	users	1:N	users.company_id	CASCADE	CASCADE	mandatory
2	users	refresh_tokens	1:N	refresh_tokens.user_id	CASCADE	CASCADE	optional
3	users	magic_tokens	1:N	magic_tokens.user_id	CASCADE	CASCADE	optional
4	departments	employees	1:N	employees.department_id	SET NULL	CASCADE	optional
5	employees	departments (manager)	N:1	departments.manager_id	logical	—	cross-service
6	geofence_locations	attendance_policies	1:N	attendance_policies.geofence_id	SET NULL	CASCADE	optional
7	attendance_records	attendance_tasks	1:N	attendance_tasks.attendance_record_id	CASCADE	CASCADE	mandatory
8	leave_types	leave_balances	1:N	leave_balances.leave_type_id	CASCADE	CASCADE	mandatory
9	leave_types	leave_requests	1:N	leave_requests.leave_type_id	CASCADE	CASCADE	mandatory
10	leave_requests	leave_approvals	1:N	leave_approvals.leave_request_id	CASCADE	CASCADE	mandatory
11	salary_structures	employee_salaries	1:N	employee_salaries.salary_structure_id	missing FK!	—	same-service
12	payroll_runs	payslips	1:N	payslips.payroll_run_id	missing FK!	—	same-service
13	classes	students	1:N	students.class_id	SET NULL	CASCADE	optional
14	students	guardians	1:N	guardians.student_id	CASCADE	CASCADE	mandatory
Logical cross-service links (UUID only, no physical FK):

users.id ↔ employees.user_id
employees.id ↔ attendance_records.employee_id, attendance_policies.employee_id, attendance_tasks.employee_id
employees.id ↔ leave_balances.employee_id, leave_requests.employee_id
employees.id ↔ employee_salaries.employee_id, payslips.employee_id
users.id ↔ notification_logs.user_id, notification_preferences.user_id
users.id ↔ audit_logs.user_id
companies.id ↔ audit_logs.company_id, payroll_runs.company_id, attendance_tasks.company_id
4. ER Diagram (Mermaid)

erDiagram

    %% ──────────────────────────────────────────
    %% AUTH SERVICE
    %% ──────────────────────────────────────────
    COMPANIES {
        UUID id PK
        VARCHAR name
        VARCHAR domain
        BOOLEAN is_active
        TIMESTAMP created_at
    }

    USERS {
        UUID id PK
        UUID company_id FK
        VARCHAR email
        VARCHAR hashed_password
        VARCHAR role
        BOOLEAN is_active
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    REFRESH_TOKENS {
        UUID id PK
        UUID user_id FK
        VARCHAR token_hash
        TIMESTAMP expires_at
        BOOLEAN revoked
        TIMESTAMP created_at
    }

    MAGIC_TOKENS {
        UUID id PK
        UUID user_id FK
        VARCHAR token_hash
        TIMESTAMP expires_at
        BOOLEAN used
        VARCHAR purpose
        TIMESTAMP created_at
    }

    %% ──────────────────────────────────────────
    %% EMPLOYEE SERVICE
    %% ──────────────────────────────────────────
    DEPARTMENTS {
        UUID id PK
        VARCHAR name
        VARCHAR description
        UUID manager_id
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    EMPLOYEES {
        UUID id PK
        UUID user_id
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR email
        DATE date_of_birth
        VARCHAR gender
        DATE date_joined
        UUID department_id FK
        VARCHAR designation
        VARCHAR employment_status
        NUMERIC joining_salary
        TEXT health_issues
        TEXT aadhaar_number
        TEXT pan_number
        TEXT bank_account_number
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    %% ──────────────────────────────────────────
    %% ATTENDANCE SERVICE
    %% ──────────────────────────────────────────
    GEOFENCE_LOCATIONS {
        UUID id PK
        VARCHAR name
        FLOAT latitude
        FLOAT longitude
        INTEGER radius_meters
        BOOLEAN is_active
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    ATTENDANCE_POLICIES {
        UUID id PK
        UUID department_id
        UUID employee_id
        VARCHAR method
        UUID geofence_id FK
        TIME work_start_time
        FLOAT work_hours_per_day
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    ATTENDANCE_RECORDS {
        UUID id PK
        UUID employee_id
        TIMESTAMPTZ clock_in
        TIMESTAMPTZ clock_out
        FLOAT clock_in_lat
        FLOAT clock_in_lng
        FLOAT work_hours
        FLOAT overtime_hours
        INTEGER day_rating
        VARCHAR status
        DATE date
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    ATTENDANCE_TASKS {
        UUID id PK
        UUID company_id
        UUID attendance_record_id FK
        UUID employee_id
        UUID assigned_by
        VARCHAR title
        TEXT details
        NUMERIC expected_expenses
        VARCHAR status
        TEXT completion_notes
        NUMERIC actual_expenses
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    %% ──────────────────────────────────────────
    %% LEAVE SERVICE
    %% ──────────────────────────────────────────
    LEAVE_TYPES {
        UUID id PK
        VARCHAR name
        INTEGER days_allowed
        INTEGER requires_approval
        INTEGER is_active
    }

    LEAVE_BALANCES {
        UUID id PK
        UUID employee_id
        UUID leave_type_id FK
        INTEGER total_days
        INTEGER used_days
        INTEGER pending_days
        INTEGER year
    }

    LEAVE_REQUESTS {
        UUID id PK
        UUID employee_id
        UUID leave_type_id FK
        DATE start_date
        DATE end_date
        INTEGER total_days
        VARCHAR status
        TEXT reason
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    LEAVE_APPROVALS {
        UUID id PK
        UUID leave_request_id FK
        UUID approver_id
        VARCHAR level
        VARCHAR status
        TEXT remarks
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    HOLIDAYS {
        UUID id PK
        VARCHAR name
        DATE date
        TEXT description
        INTEGER is_active
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    %% ──────────────────────────────────────────
    %% PAYROLL SERVICE
    %% ──────────────────────────────────────────
    SALARY_STRUCTURES {
        UUID id PK
        VARCHAR name
        NUMERIC basic_pct
        NUMERIC hra_pct
        NUMERIC allowances_pct
        NUMERIC pf_pct
        NUMERIC esi_pct
        NUMERIC professional_tax
        INTEGER is_active
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    EMPLOYEE_SALARIES {
        UUID id PK
        UUID employee_id
        UUID salary_structure_id
        NUMERIC ctc
        DATE effective_from
        DATE effective_to
        INTEGER is_active
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    PAYROLL_RUNS {
        UUID id PK
        UUID company_id
        DATE period_start
        DATE period_end
        VARCHAR status
        INTEGER total_employees
        NUMERIC total_gross
        NUMERIC total_net
        NUMERIC total_deductions
        UUID processed_by
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    PAYSLIPS {
        UUID id PK
        UUID payroll_run_id
        UUID employee_id
        NUMERIC ctc
        NUMERIC basic
        NUMERIC hra
        NUMERIC gross
        NUMERIC total_deductions
        NUMERIC net
        DATE period_start
        DATE period_end
        TIMESTAMP created_at
    }

    %% ──────────────────────────────────────────
    %% NOTIFICATION SERVICE
    %% ──────────────────────────────────────────
    NOTIFICATION_LOGS {
        UUID id PK
        UUID user_id
        VARCHAR type
        VARCHAR subject
        TEXT message
        VARCHAR status
        TEXT error_message
        TIMESTAMP created_at
        TIMESTAMP sent_at
    }

    NOTIFICATION_PREFERENCES {
        UUID id PK
        UUID user_id
        INTEGER email_enabled
        INTEGER sms_enabled
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    %% ──────────────────────────────────────────
    %% AUDIT SERVICE
    %% ──────────────────────────────────────────
    AUDIT_LOGS {
        UUID id PK
        UUID event_id
        VARCHAR event_type
        VARCHAR service_source
        UUID company_id
        UUID user_id
        UUID correlation_id
        VARCHAR ip_address
        VARCHAR http_method
        VARCHAR endpoint
        JSON payload
        TIMESTAMP timestamp
        TIMESTAMP created_at
    }

    %% ──────────────────────────────────────────
    %% STUDENTS SERVICE
    %% ──────────────────────────────────────────
    CLASSES {
        UUID id PK
        VARCHAR name
        INTEGER grade_level
        VARCHAR section
        VARCHAR academic_year
        INTEGER capacity
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    STUDENTS {
        UUID id PK
        VARCHAR student_number
        VARCHAR first_name
        VARCHAR last_name
        DATE date_of_birth
        VARCHAR gender
        UUID class_id FK
        DATE enrollment_date
        VARCHAR status
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    GUARDIANS {
        UUID id PK
        UUID student_id FK
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR relationship
        VARCHAR phone
        VARCHAR email
        BOOLEAN is_primary
        TIMESTAMP created_at
    }

    %% ──────────────────────────────────────────
    %% PHYSICAL RELATIONSHIPS (same-DB FKs)
    %% ──────────────────────────────────────────
    COMPANIES ||--o{ USERS : "has"
    USERS ||--o{ REFRESH_TOKENS : "owns"
    USERS ||--o{ MAGIC_TOKENS : "owns"

    DEPARTMENTS ||--o{ EMPLOYEES : "contains"

    GEOFENCE_LOCATIONS ||--o{ ATTENDANCE_POLICIES : "used_by"
    ATTENDANCE_RECORDS ||--o{ ATTENDANCE_TASKS : "has"

    LEAVE_TYPES ||--o{ LEAVE_BALANCES : "allocated_as"
    LEAVE_TYPES ||--o{ LEAVE_REQUESTS : "used_in"
    LEAVE_REQUESTS ||--o{ LEAVE_APPROVALS : "approved_via"

    SALARY_STRUCTURES ||--o{ EMPLOYEE_SALARIES : "applied_to"
    PAYROLL_RUNS ||--o{ PAYSLIPS : "generates"

    CLASSES ||--o{ STUDENTS : "enrolls"
    STUDENTS ||--o{ GUARDIANS : "has"

    %% ──────────────────────────────────────────
    %% LOGICAL CROSS-SERVICE LINKS (UUID refs)
    %% ──────────────────────────────────────────
    USERS ||--o| EMPLOYEES : "profile (logical)"
    EMPLOYEES ||--o{ ATTENDANCE_RECORDS : "clocks_in (logical)"
    EMPLOYEES ||--o{ ATTENDANCE_POLICIES : "governed_by (logical)"
    EMPLOYEES ||--o{ LEAVE_BALANCES : "holds (logical)"
    EMPLOYEES ||--o{ LEAVE_REQUESTS : "applies (logical)"
    EMPLOYEES ||--o{ EMPLOYEE_SALARIES : "assigned (logical)"
    EMPLOYEES ||--o{ PAYSLIPS : "receives (logical)"
    USERS ||--o{ NOTIFICATION_LOGS : "notified_via (logical)"
    USERS ||--o| NOTIFICATION_PREFERENCES : "configures (logical)"
    USERS ||--o{ AUDIT_LOGS : "audited_by (logical)"
    COMPANIES ||--o{ PAYROLL_RUNS : "runs (logical)"
    COMPANIES ||--o{ AUDIT_LOGS : "tracked_in (logical)"
5. Schema Quality Check
Normalization Level
Service	Level	Notes
Auth	3NF	Clean — no transitive dependencies
Employee	2NF (partial)	employees mixes personal + banking + work info in one fat table — flat by design for single-service simplicity
Attendance	3NF	Good separation of concerns
Leave	3NF	leave_requests.approved_by_id is a deliberate denormalization cache
Payroll	3NF	payslips is an intentional snapshot denormalization — correct pattern
Notification	3NF	Clean
Audit	3NF	Insert-only, by design
Students	3NF	Clean
Redundancy & Issues Found
#	Issue	Location	Severity
1	employee_salaries.salary_structure_id — missing FK declaration (same-DB)	payroll-service	High
2	payslips.payroll_run_id — missing FK declaration (same-DB)	payroll-service	High
3	payroll_runs.company_id — not declared as an explicit Column(), only in UniqueConstraint	payroll-service	High
4	leave_requests.approved_by_id — cached denorm without documentation	leave-service	Low
5	Integer used for booleans (is_active, requires_approval) instead of Boolean	leave, payroll, notification	Medium
6	employees.staff_documents_urls — storing multiple URLs as comma-sep/JSON TEXT	employee-service	Medium
7	departments has no company_id — multi-tenancy not enforced at the DB level	employee-service	Medium
8	holidays has no company_id — holidays are global, not per-company	leave-service	Medium
9	audit_logs has company_id only via Base class — unclear if the column is actually present	audit-service	Medium
10	classes has no unique constraint on (grade_level, section, academic_year)	students-service	Low
6. Performance Considerations
Critical Indexes (already present — verify these exist)
Table	Index	Query Pattern
users	(company_id, role) composite	"All HR managers in company X"
attendance_records	(employee_id, date) UNIQUE	Daily punch lookup
attendance_records	(status, date)	Dashboard: absent today
leave_requests	(employee_id, status)	"My pending leaves"
leave_balances	(employee_id, year)	Balance check at request time
payslips	(employee_id, period_start)	Payslip history
audit_logs	(company_id, timestamp)	Tenant audit trail
audit_logs	partial index on last 90 days	Recent activity queries
Missing Indexes to Add

-- employees: search by employment_status within a company (once company_id added)
CREATE INDEX ix_employees_company_status ON employees(employment_status);

-- attendance_tasks: manager view of pending tasks by company
CREATE INDEX ix_tasks_company_status ON attendance_tasks(company_id, status);

-- leave_requests: date range queries for calendar view
CREATE INDEX ix_leave_requests_dates ON leave_requests(start_date, end_date);

-- payroll_runs: status filter (most ops check DRAFT vs COMPLETED)
CREATE INDEX ix_payroll_runs_company_status ON payroll_runs(company_id, status);

-- notification_logs: TTL-based cleanup query
CREATE INDEX ix_notif_logs_created_at ON notification_logs(created_at);
Denormalization (Intentional & Justified)
Location	Reason
payslips.* (salary snapshot)	Correct — salary changes must not retroactively alter payslips
payroll_runs.total_* aggregates	Correct — avoids re-summing thousands of payslips
leave_requests.approved_by_id	Acceptable cache — document it clearly
7. Data Integrity Rules
Constraints to Add

-- 1. Ensure end_date >= start_date on leave_requests
ALTER TABLE leave_requests
  ADD CONSTRAINT chk_leave_dates CHECK (end_date >= start_date);

-- 2. Ensure total_days > 0
ALTER TABLE leave_requests
  ADD CONSTRAINT chk_leave_total_days CHECK (total_days > 0);

-- 3. Attendance day_rating must be 1–5
ALTER TABLE attendance_records
  ADD CONSTRAINT chk_day_rating CHECK (day_rating BETWEEN 1 AND 5 OR day_rating IS NULL);

-- 4. work_hours must be non-negative
ALTER TABLE attendance_records
  ADD CONSTRAINT chk_work_hours CHECK (work_hours >= 0 OR work_hours IS NULL);

-- 5. Payslip net = gross - total_deductions
-- (enforce via trigger or application logic)

-- 6. leave_balances: used_days + pending_days <= total_days
ALTER TABLE leave_balances
  ADD CONSTRAINT chk_leave_days CHECK (used_days + pending_days <= total_days);

-- 7. employee_salaries: effective_to >= effective_from (if set)
ALTER TABLE employee_salaries
  ADD CONSTRAINT chk_salary_dates CHECK (effective_to IS NULL OR effective_to >= effective_from);

-- 8. Attendance clock_out > clock_in
ALTER TABLE attendance_records
  ADD CONSTRAINT chk_clockout CHECK (clock_out IS NULL OR clock_out > clock_in);

-- 9. classes: unique class per academic year
ALTER TABLE classes
  ADD CONSTRAINT uq_class_grade_section_year UNIQUE (grade_level, section, academic_year);
8. Edge Cases & Risks
Risk	Table	Mitigation
Orphan employees if user deleted in auth-service	employees.user_id	Implement cross-service event (user.deleted → archive employee) via RabbitMQ
Orphan payslips if payroll_run FK missing	payslips.payroll_run_id	Add physical FK within payroll DB
Orphan employee_salaries if FK missing	employee_salaries.salary_structure_id	Add physical FK within payroll DB
Duplicate attendance	attendance_records	UNIQUE(employee_id, date) exists — good
Duplicate payroll runs	payroll_runs	UNIQUE(company_id, period_start, period_end) exists — good
Stale leave balance	leave_balances	used_days + pending_days can drift if request status changes are not transactional — add trigger or compensating logic
Magic token replay	magic_tokens	used flag exists, but TTL check must also be enforced at query time, not just at column level
Refresh token flood	refresh_tokens	No maximum count per user — a loop bug could create thousands; add application-level limit or periodic cleanup job
audit_logs table growth	audit_logs	Partition by month (PostgreSQL range partitioning on timestamp) or archive to cold storage after 1 year
employees.staff_documents_urls TEXT field	employees	Cannot query individual URLs, cannot enforce referential integrity; migrate to a separate employee_documents table
No company_id on departments/holidays	departments, holidays	Adding company_id is necessary before going multi-tenant at scale
Circular reference risk	employees.department_id ↔ departments.manager_id	Both point at each other (employee → dept, dept → manager → employee). Use deferred FK constraints or application-level sequencing
9. Improvement Suggestions
P0 — Fix Immediately (Bugs)

# payroll-service/app/models/payroll.py

# 1. Add company_id as an explicit Column (currently only in UniqueConstraint)
company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

# 2. Add missing FK for salary_structure_id
salary_structure_id = Column(
    UUID(as_uuid=True),
    ForeignKey("salary_structures.id", ondelete="RESTRICT"),
    nullable=False, index=True
)

# 3. Add missing FK for payroll_run_id in Payslip
payroll_run_id = Column(
    UUID(as_uuid=True),
    ForeignKey("payroll_runs.id", ondelete="CASCADE"),
    nullable=False, index=True
)
P1 — Important (Multi-tenancy Gaps)

# employee-service: add company_id to departments
company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

# leave-service: add company_id to holidays
company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
# nullable so global holidays work; non-null for company-specific ones
P2 — Quality (Minor)

# Replace Integer booleans with proper Boolean columns (leave, payroll, notification services)
# Before:
requires_approval = Column(Integer, default=1, nullable=False)
# After:
requires_approval = Column(Boolean, default=True, nullable=False)

# Replace staff_documents_urls TEXT with a proper table:
class EmployeeDocument(Base):
    __tablename__ = "employee_documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String(100), nullable=False)  # 'id_proof', 'certificate', etc.
    url = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=naive_utcnow, nullable=False)

# employees.years_of_experience: change VARCHAR(10) → NUMERIC(4,1)
# employees.percentage: change VARCHAR(10) → NUMERIC(5,2)
# employees.year_of_passing: change VARCHAR(4) → SMALLINT
Bonus: Sample Rows
companies


id: 550e8400-e29b-41d4-a716-446655440000
name: "Acme Corp"
domain: "acme.com"
is_active: true
users


id: 7c9e6679-7425-40de-944b-e07fc1f90ae7
company_id: 550e8400-...
email: "hr@acme.com"
role: "HR"
is_active: true
leave_balances


employee_id: <emp-uuid>
leave_type_id: <casual-leave-uuid>
total_days: 12
used_days: 3
pending_days: 2
year: 2026
Bonus: Naming Conventions
Object	Convention	Example
Tables	snake_case, plural	attendance_records
Columns	snake_case	employee_id, created_at
PKs	always id	id UUID PK
FKs	{referenced_table_singular}_id	department_id, leave_type_id
Indexes	ix_{table}_{column(s)}	ix_users_company_id
Unique constraints	uq_{table}_{column(s)}	uq_employee_date
Check constraints	chk_{table}_{rule}	chk_leave_dates
Enum values	SCREAMING_SNAKE_CASE	FULL_DAY, PROJECT_IN_CHARGE
Bonus: Migration Strategy Tips
Add columns nullable first, backfill data, then add NOT NULL constraint — prevents table locks in production.
Never drop columns in the same migration as the code deploy — deploy code ignoring old column, then drop in a follow-up migration.
company_id backfill on departments and holidays — set a default company first, then tighten to NOT NULL.
Payroll FK additions — add as DEFERRABLE INITIALLY DEFERRED to avoid ordering issues during bulk inserts.
Audit log partitioning — plan range partitioning by timestamp before the table exceeds 10M rows; retrofitting partitions on a live table is painful.
Use Alembic batch_alter_table for SQLite-compatible dev environments, but in production run native ALTER TABLE statements directly for speed.