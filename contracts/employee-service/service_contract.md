# Employee Service Contract (v3)

The Employee Service manages employee profiles, departments, and designations for the HRMS platform. All data is tenant-isolated by `company_id`.

## Base URL
- **Internal (Docker)**: `http://employee-service:8001/api/v1`
- **Gateway**: `/api/v1/employees/*`, `/api/v1/departments/*`

---

## Authentication
- **Mechanism**: JWT (Bearer Token) — validated locally using shared public key
- **Headers**: `Authorization: Bearer <token>`
- **Tenant Isolation**: `company_id` is extracted from the JWT and automatically applied to all queries
- **JWT Blacklist**: This service checks a Redis-based JWT blacklist (`bl:{jti}` key) on every authenticated request. If Redis is unavailable, the check fails open (request is allowed).
- Refer to [SERVICE_AUTH_INTEGRATION_GUIDE.md](../SERVICE_AUTH_INTEGRATION_GUIDE.md)

---

## Rate Limiting

| Endpoint | Limit |
| :--- | :--- |
| `POST /employees` | 30/min |
| `PATCH /employees/{id}` | 30/min |
| `DELETE /employees/{id}` | 30/min |
| `POST /employees/bulk` | 10/min |

---

## Endpoints

### Employee Endpoints

#### 1. Create Employee
Creates a new employee profile linked to an auth-service user. `company_id` is auto-injected from the JWT.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/employees` | Bearer Token | HR, Super Admin |

**Request Body**
```json
{
  "user_id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+91-9876543210",
  "phone_2": "+91-1234567890",
  "personal_email": "john@gmail.com",
  "gender": "male",
  "date_of_birth": "1995-06-15",
  "door_no": "12A",
  "street": "MG Road",
  "village_town": "Bangalore",
  "pin_code": "560001",
  "driving_license_number": "KA0120190001234",
  "aadhaar_number": "123456789012",
  "uan_number": "100012345678",
  "esi_number": "1234567890",
  "pan_number": "ABCDE1234F",
  "bank_account_number": "1234567890123456",
  "bank_name": "SBI",
  "bank_branch": "MG Road Branch",
  "ifsc_code": "SBIN0001234",
  "emergency_contact_name": "Jane Doe",
  "emergency_contact_number": "+91-9999999999",
  "emergency_contact_relation": "Spouse",
  "highest_qualification": "B.Tech",
  "year_of_passing": "2017",
  "percentage": "85",
  "institute_name": "IIT Delhi",
  "last_firm_name": "Previous Corp",
  "years_of_experience": "5",
  "last_designation": "Engineer",
  "last_drawn_salary": 50000.00,
  "reason_to_quit": "Career growth",
  "referred_by": "Internal referral",
  "health_issues": "None",
  "allergies": "None",
  "date_joined": "2026-01-15",
  "department_id": "uuid",
  "designation": "Software Engineer",
  "project": "HRMS",
  "joining_salary": 75000.00,
  "role": "employee",
  "staff_photo_url": "https://storage.example.com/photo.jpg",
  "staff_documents_urls": "doc1.pdf,doc2.pdf"
}
```

Most fields are optional except: `user_id`, `first_name`, `last_name`, `email`, `date_joined`.

**Response (201 Created)**
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "user_id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "employment_status": "active",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

**Events Published**: `employee.created`

---

#### 2. List Employees
Returns paginated list of employees scoped to the authenticated user's company.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/employees` | Bearer Token | HR, Super Admin, Manager |

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `skip` | int | 0 | Records to skip |
| `limit` | int | 20 | Max records (1-100) |
| `department_id` | UUID | — | Filter by department |
| `employment_status` | string | — | Filter: active, inactive, terminated |
| `search` | string | — | Search by name or email |

**Response (200 OK)**
```json
{
  "total": 150,
  "skip": 0,
  "limit": 20,
  "employees": [...]
}
```

---

#### 3. Get Employee by ID

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/employees/{id}` | Bearer Token | Any Authenticated |

**Response (200 OK)**: Full EmployeeResponse object

---

#### 4. Get My Profile

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/employees/me` | Bearer Token | Any Authenticated |

**Response (200 OK)**: Employee object for the authenticated user (looked up by `user_id` from JWT)

---

#### 5. Update Employee

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PATCH` | `/employees/{id}` | Bearer Token | HR, Super Admin |

**Request Body** (all fields optional)
```json
{
  "first_name": "Jane",
  "phone": "+91-1234567890",
  "department_id": "uuid",
  "designation": "Senior Engineer",
  "employment_status": "active"
}
```

**Response (200 OK)**: Updated employee object

**Events Published**: `employee.updated`

---

#### 6. Deactivate Employee (Soft Delete)

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `DELETE` | `/employees/{id}` | Bearer Token | HR, Super Admin |

**Response (200 OK)**: Deactivated employee object (status = `terminated`)

**Events Published**: `employee.deactivated`

---

#### 7. Bulk Import Employees
Bulk import employees from a JSON array. `company_id` is auto-injected from the JWT for all entries.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/employees/bulk` | Bearer Token | HR, Super Admin |

**Request Body**
```json
[
  {
    "user_id": "uuid",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "date_joined": "2026-01-15"
  },
  {
    "user_id": "uuid",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com",
    "date_joined": "2026-01-20"
  }
]
```

Each element follows the same schema as the Create Employee request body.

**Response (200 OK)**
```json
{
  "total": 2,
  "succeeded": 1,
  "failed": 1,
  "results": [
    {
      "index": 0,
      "success": true,
      "employee": { "id": "uuid", "email": "john.doe@example.com", "..." : "..." }
    },
    {
      "index": 1,
      "success": false,
      "error": "Duplicate email: jane.smith@example.com"
    }
  ]
}
```

---

### Department Endpoints

#### 8. Create Department
`company_id` is auto-injected from the JWT. Department names are unique per company.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/departments` | Bearer Token | HR, Super Admin |

**Request Body**
```json
{
  "name": "Engineering",
  "description": "Software engineering department",
  "manager_id": "uuid"
}
```

**Response (201 Created)**
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "name": "Engineering",
  "description": "Software engineering department",
  "manager_id": "uuid",
  "is_active": 1,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

---

#### 9. List Departments

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/departments` | Bearer Token | Any Authenticated |

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `include_inactive` | boolean | false | Include soft-deleted (inactive) departments |

**Response (200 OK)**
```json
{
  "total": 5,
  "departments": [...]
}
```

---

#### 10. Get Department by ID

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/departments/{id}` | Bearer Token | Any Authenticated |

---

#### 11. Update Department

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PATCH` | `/departments/{id}` | Bearer Token | HR, Super Admin |

---

#### 12. Delete Department (Soft Delete)
Sets `is_active` to 0 on the department. Does not physically remove the record.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `DELETE` | `/departments/{id}` | Bearer Token | HR, Super Admin |

**Response (200 OK)**
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "name": "Engineering",
  "description": "Software engineering department",
  "manager_id": "uuid",
  "is_active": 0,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

---

### Health Check

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/health` | None |

**Response (200 OK)**
```json
{
  "status": "healthy",
  "service": "employee-service",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "rabbitmq": "ok",
    "redis": "ok"
  }
}
```

---

## Internal Endpoints (Service-to-Service)

### Get Employee by User ID (Internal)

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/employees/internal/{user_id}` | `X-Service-Token` header |

Not exposed via API docs. Protected by internal service token.

---

## Events Published (RabbitMQ)

| Event Type | When | Payload |
| :--- | :--- | :--- |
| `employee.created` | New employee profile created | employee_id, company_id, user_id, email, first_name, last_name |
| `employee.updated` | Employee profile updated | employee_id, user_id, updated_fields |
| `employee.deactivated` | Employee terminated | employee_id, user_id, email |

All events follow HRMS standard format with `event_id`, `event_type`, `service_source`, `timestamp`, `payload`.

---

## Multi-Tenancy

- All employee and department data is isolated by `company_id`
- `company_id` is extracted from the JWT at the dependency layer and injected into the DB session
- Every repository query is automatically scoped: `WHERE company_id = :tenant_id`
- On create, `company_id` is auto-set — callers never pass it explicitly
- Department `name` uniqueness is enforced per-company, not globally

---

## Error Codes

| Status Code | Meaning | Description |
| :--- | :--- | :--- |
| `401` | Unauthorized | Missing or invalid JWT |
| `403` | Forbidden | Insufficient role permissions |
| `404` | Not Found | Employee or department not found |
| `409` | Conflict | Duplicate email or department name (within same company) |
| `422` | Validation Error | Input data fails Pydantic validation |
| `429` | Too Many Requests | Rate limit exceeded |
| `503` | Service Unavailable | Dependent service unavailable |

---

## Database Tables

### employees
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Not null, indexed |
| `user_id` | UUID | Unique, indexed (ref to auth-service) |
| `first_name` | String(100) | Not null |
| `last_name` | String(100) | Not null |
| `email` | String(255) | Unique, indexed |
| `phone` | String(20) | Nullable |
| `phone_2` | String(20) | Nullable |
| `personal_email` | String(255) | Nullable |
| `gender` | String(10) | Nullable |
| `date_of_birth` | Date | Nullable |
| `door_no` | String(50) | Nullable |
| `street` | String(200) | Nullable |
| `village_town` | String(150) | Nullable |
| `pin_code` | String(10) | Nullable |
| `driving_license_number` | EncryptedString | AES-256-GCM |
| `aadhaar_number` | EncryptedString | AES-256-GCM |
| `uan_number` | EncryptedString | AES-256-GCM |
| `esi_number` | EncryptedString | AES-256-GCM |
| `pan_number` | EncryptedString | AES-256-GCM |
| `bank_account_number` | EncryptedString | AES-256-GCM |
| `bank_name` | String(150) | Nullable |
| `bank_branch` | String(150) | Nullable |
| `ifsc_code` | String(11) | Nullable |
| `emergency_contact_name` | String(150) | Nullable |
| `emergency_contact_number` | String(20) | Nullable |
| `emergency_contact_relation` | String(100) | Nullable |
| `highest_qualification` | String(200) | Nullable |
| `year_of_passing` | String(4) | Nullable |
| `percentage` | String(10) | Nullable |
| `institute_name` | String(300) | Nullable |
| `last_firm_name` | String(300) | Nullable |
| `years_of_experience` | String(10) | Nullable |
| `last_designation` | String(100) | Nullable |
| `last_drawn_salary` | Numeric(12,2) | Nullable |
| `reason_to_quit` | Text | Nullable |
| `referred_by` | String(200) | Nullable |
| `health_issues` | Text | Nullable |
| `allergies` | Text | Nullable |
| `date_joined` | Date | Not null |
| `department_id` | UUID | FK → departments.id, indexed, nullable |
| `designation` | String(100) | Nullable |
| `employment_status` | String(20) | Default: active, indexed |
| `project` | String(200) | Nullable |
| `joining_salary` | Numeric(12,2) | Nullable |
| `role` | String(50) | Nullable |
| `staff_photo_url` | String(500) | Nullable |
| `staff_documents_urls` | Text | Nullable |
| `created_at` | DateTime | UTC, indexed |
| `updated_at` | DateTime | UTC |

### departments
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Not null, indexed |
| `name` | String(150) | Not null, indexed (unique per company) |
| `description` | String(500) | Nullable |
| `manager_id` | UUID | Nullable |
| `is_active` | Integer | Not null, default 1 |
| `created_at` | DateTime | UTC |
| `updated_at` | DateTime | UTC |
