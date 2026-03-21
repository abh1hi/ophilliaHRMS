# Payroll Service Contract (v3)

The Payroll Service manages salary structures, employee salary assignments, payroll runs, and payslip generation for the HRMS platform. All data is tenant-isolated by `company_id`.

## Base URL
- **Internal (Docker)**: `http://payroll-service:8004/api/v1`
- **Gateway**: `/api/v1/payroll/*`, `/api/v1/salary/*`

---

## Authentication
- JWT Bearer Token (shared public key with auth-service)
- **Tenant Isolation**: `company_id` is extracted from the JWT and automatically applied to all queries
- See [SERVICE_AUTH_INTEGRATION_GUIDE.md](../SERVICE_AUTH_INTEGRATION_GUIDE.md)

---

## JWT Blacklist

Before accepting any JWT, the payroll-service checks Redis for a `bl:{jti}` key (written by auth-service on logout). If the key exists, the token is considered revoked and the request is rejected with `401 Unauthorized`.

- **Fail-open**: If Redis is unavailable, the blacklist check is skipped and the token is accepted. This ensures that a Redis outage does not block all authenticated requests.
- See the [Auth Service Contract](../auth-service/service_contract.md) for full blacklist details.

---

## Endpoints

### Payroll Runs

#### 1. Execute Payroll Run
Runs payroll for a given period. Idempotent — rejects duplicate runs for the same period.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/payroll/run` | Bearer Token | HR, Super Admin |

**Request Body**
```json
{
  "period_start": "2026-03-01",
  "period_end": "2026-03-31"
}
```

**Response (201 Created)**
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "period_start": "2026-03-01",
  "period_end": "2026-03-31",
  "status": "completed",
  "total_employees": 50,
  "total_gross": 2500000.00,
  "total_deductions": 500000.00,
  "total_net": 2000000.00,
  "created_at": "ISO-8601"
}
```

---

#### 2. List Payroll Runs

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/payroll/runs` | Bearer Token | HR, Super Admin |

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `skip` | int | 0 | Records to skip |
| `limit` | int | 20 | Max records (1-100) |

**Response (200 OK)**: List of PayrollRunResponse objects

---

#### 3. Get Payroll Run Details

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/payroll/runs/{run_id}` | Bearer Token | HR, Super Admin |

**Response (200 OK)**: Single PayrollRunResponse object

---

#### 4. Get Payslips for Run

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/payroll/runs/{run_id}/payslips` | Bearer Token | HR, Super Admin |

**Response (200 OK)**
```json
[
  {
    "id": "uuid",
    "company_id": "uuid",
    "payroll_run_id": "uuid",
    "employee_id": "uuid",
    "basic": 30000.00,
    "hra": 15000.00,
    "allowances": 10000.00,
    "gross": 55000.00,
    "pf_deduction": 3600.00,
    "esi_deduction": 425.00,
    "professional_tax": 200.00,
    "total_deductions": 4225.00,
    "net_pay": 50775.00,
    "created_at": "ISO-8601"
  }
]
```

---

#### 5. Get My Payslips
Returns payslips for the authenticated employee.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/payroll/my-payslips` | Bearer Token | Any Authenticated |

**Response (200 OK)**: List of PayslipResponse objects

---

### Salary Structures

#### 6. Create Salary Structure

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/salary/structures` | Bearer Token | HR, Super Admin |

**Request Body**
```json
{
  "name": "Standard CTC",
  "description": "Default salary structure",
  "basic_pct": 40.0,
  "hra_pct": 20.0,
  "allowances_pct": 40.0,
  "pf_pct": 12.0,
  "esi_pct": 0.75,
  "professional_tax": 200.00
}
```

**Response (201 Created)**
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "name": "Standard CTC",
  "description": "Default salary structure",
  "basic_pct": 40.0,
  "hra_pct": 20.0,
  "allowances_pct": 40.0,
  "pf_pct": 12.0,
  "esi_pct": 0.75,
  "professional_tax": 200.00,
  "is_active": true,
  "created_at": "ISO-8601"
}
```

---

#### 7. List Salary Structures

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/salary/structures` | Bearer Token | HR, Super Admin |

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `skip` | int | 0 | Records to skip |
| `limit` | int | 20 | Max records (1-100) |
| `include_inactive` | boolean | false | Include soft-deleted (inactive) structures |

**Response (200 OK)**: List of SalaryStructureResponse objects

---

#### 8. Get Salary Structure

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/salary/structures/{structure_id}` | Bearer Token | HR, Super Admin |

---

#### 9. Update Salary Structure
Updates percentages or metadata for an existing salary structure. All fields are optional.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PATCH` | `/salary/structures/{id}` | Bearer Token | HR, Super Admin |

**Request Body** (all fields optional)
```json
{
  "name": "Updated CTC",
  "description": "Updated salary structure",
  "basic_pct": 45.0,
  "hra_pct": 25.0,
  "allowances_pct": 30.0,
  "pf_pct": 12.0,
  "esi_pct": 0.75,
  "professional_tax": 200.00
}
```

**Response (200 OK)**: SalaryStructureResponse

---

#### 10. Delete Salary Structure (Soft Delete)
Soft-deletes a salary structure by setting `is_active=0`. Existing employee salary assignments using this structure remain unchanged.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `DELETE` | `/salary/structures/{id}` | Bearer Token | HR, Super Admin |

**Response (200 OK)**: SalaryStructureResponse (with `is_active: false`)

---

### Employee Salary

#### 11. Assign Salary to Employee
Assigns a salary structure and CTC to an employee. Deactivates any previous active salary.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/salary/assign` | Bearer Token | HR, Super Admin |

**Cross-Service Validation**: The `employee_id` is validated against the employee-service to confirm the employee exists and belongs to the same `company_id` as the authenticated user. Returns `404` if the employee is not found within the tenant.

**Request Body**
```json
{
  "employee_id": "uuid",
  "salary_structure_id": "uuid",
  "ctc": 660000.00,
  "effective_from": "2026-04-01"
}
```

**Response (201 Created)**
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "employee_id": "uuid",
  "salary_structure_id": "uuid",
  "ctc": 660000.00,
  "effective_from": "2026-04-01",
  "is_active": true,
  "created_at": "ISO-8601"
}
```

---

#### 12. Get Employee's Active Salary

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/salary/employee/{employee_id}` | Bearer Token | HR, Super Admin |

---

#### 13. Get Employee Salary History
Returns the full salary history for an employee, including both active and inactive salary records.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/salary/employee/{employee_id}/history` | Bearer Token | HR, Super Admin |

**Response (200 OK)**
```json
[
  {
    "id": "uuid",
    "company_id": "uuid",
    "employee_id": "uuid",
    "salary_structure_id": "uuid",
    "ctc": 660000.00,
    "effective_from": "2026-04-01",
    "is_active": true,
    "created_at": "ISO-8601"
  },
  {
    "id": "uuid",
    "company_id": "uuid",
    "employee_id": "uuid",
    "salary_structure_id": "uuid",
    "ctc": 550000.00,
    "effective_from": "2025-01-01",
    "is_active": false,
    "created_at": "ISO-8601"
  }
]
```

**Response Type**: `List[EmployeeSalaryResponse]`

---

### Health Check

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/health` | None |

**Response (200 OK)**
```json
{
  "status": "healthy",
  "service": "payroll-service",
  "version": "1.0.0",
  "checks": {
    "database": "connected",
    "redis": "connected"
  }
}
```

---

## Events Published (RabbitMQ)

| Event Type | When | Payload |
| :--- | :--- | :--- |
| `payroll.run_completed` | Payroll run finishes | company_id, run_id, period, total_employees, totals |
| `payroll.payslip_generated` | Each payslip created | company_id, payslip_id, employee_id, net_pay, period |

All events include `company_id` in the payload for tenant-scoped processing by downstream consumers.

---

## Error Codes

| Status Code | Meaning | Description |
| :--- | :--- | :--- |
| `401` | Unauthorized | Missing or invalid JWT, or token blacklisted |
| `403` | Forbidden | Insufficient role permissions |
| `404` | Not Found | Run, structure, salary, or employee not found (within tenant) |
| `409` | Conflict | Duplicate payroll run for same period |
| `422` | Validation Error | Invalid input data |

---

## Database Tables

### payroll_runs
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Not null, indexed |
| `period_start` | Date | Not null |
| `period_end` | Date | Not null |
| `status` | String | pending, completed, failed |
| `total_employees` | Integer | Nullable |
| `total_gross` | Numeric(14,2) | Nullable |
| `total_deductions` | Numeric(14,2) | Nullable |
| `total_net` | Numeric(14,2) | Nullable |
| `created_at` | DateTime | UTC |

### payslips
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Not null, indexed |
| `payroll_run_id` | UUID | FK -> payroll_runs.id |
| `employee_id` | UUID | Not null, indexed |
| `basic` | Numeric(12,2) | Not null |
| `hra` | Numeric(12,2) | Not null |
| `allowances` | Numeric(12,2) | Not null |
| `gross` | Numeric(12,2) | Not null |
| `pf_deduction` | Numeric(12,2) | Not null |
| `esi_deduction` | Numeric(12,2) | Not null |
| `professional_tax` | Numeric(12,2) | Not null |
| `total_deductions` | Numeric(12,2) | Not null |
| `net_pay` | Numeric(12,2) | Not null |
| `created_at` | DateTime | UTC |

### salary_structures
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Not null, indexed |
| `name` | String | Not null, unique per company |
| `description` | Text | Nullable |
| `basic_pct` | Float | Not null |
| `hra_pct` | Float | Not null |
| `allowances_pct` | Float | Not null |
| `pf_pct` | Float | Not null |
| `esi_pct` | Float | Not null |
| `professional_tax` | Numeric(10,2) | Not null |
| `is_active` | Boolean | Default: true |
| `created_at` | DateTime | UTC |

### employee_salaries
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Not null, indexed |
| `employee_id` | UUID | Not null, indexed |
| `salary_structure_id` | UUID | FK -> salary_structures.id |
| `ctc` | Numeric(14,2) | Not null |
| `effective_from` | Date | Not null |
| `is_active` | Boolean | Default: true |
| `created_at` | DateTime | UTC |
