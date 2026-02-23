# 👤 Employee Service Contract (v1)

The Employee Service manages employee profiles, departments, and designations for the HRMS platform.

## 🚀 Base URL
- **Production**: `https://employee.hrms.com/api/v1`
- **Internal (Docker)**: `http://employee-service:8001/api/v1`

---

## 🔑 Authentication
- **Mechanism**: JWT (Bearer Token) — validated locally using shared `SECRET_KEY`
- **Headers**: `Authorization: Bearer <token>`
- Refer to [SERVICE_AUTH_INTEGRATION_GUIDE.md](../SERVICE_AUTH_INTEGRATION_GUIDE.md)

---

## 📡 Endpoints

### 1. Create Employee
Creates a new employee profile linked to an auth-service user.

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
  "gender": "male",
  "date_of_birth": "1995-06-15",
  "date_joined": "2026-01-15",
  "department_id": "uuid",
  "designation": "Software Engineer",
  "address": "123 Main St, City"
}
```

**Response (201 Created)**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+91-9876543210",
  "gender": "male",
  "date_of_birth": "1995-06-15",
  "date_joined": "2026-01-15",
  "department_id": "uuid",
  "designation": "Software Engineer",
  "employment_status": "active",
  "address": "123 Main St, City",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

**Events Published**: `employee.created`

---

### 2. List Employees
Returns paginated list of employees with optional filters.

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

### 3. Get Employee by ID

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/employees/{id}` | Bearer Token | Any Authenticated |

**Response (200 OK)**: Employee object

---

### 4. Get My Profile

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/employees/me` | Bearer Token | Any Authenticated |

**Response (200 OK)**: Employee object for the authenticated user

---

### 5. Update Employee

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

### 6. Deactivate Employee

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `DELETE` | `/employees/{id}` | Bearer Token | Super Admin |

**Response (200 OK)**: Deactivated employee object (status = `terminated`)

**Events Published**: `employee.deactivated`

---

### 7. Create Department

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
  "name": "Engineering",
  "description": "Software engineering department",
  "manager_id": "uuid",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

---

### 8. List Departments

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/departments` | Bearer Token | Any Authenticated |

**Response (200 OK)**
```json
{
  "total": 5,
  "departments": [...]
}
```

---

### 9. Get Department by ID

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/departments/{id}` | Bearer Token | Any Authenticated |

---

### 10. Update Department

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PATCH` | `/departments/{id}` | Bearer Token | HR, Super Admin |

---

## 🔒 Internal Endpoints (Service-to-Service)

### Get Employee by User ID (Internal)

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/employees/internal/{user_id}` | `X-Service-Token` header |

Not exposed via API docs. Protected by internal service token.

---

## 📢 Events Published (RabbitMQ)

| Event Type | When | Payload |
| :--- | :--- | :--- |
| `employee.created` | New employee profile created | employee_id, user_id, email, name |
| `employee.updated` | Employee profile updated | employee_id, user_id, updated_fields |
| `employee.deactivated` | Employee terminated | employee_id, user_id, email |

All events follow HRMS standard format with `event_id`, `event_type`, `service_source`, `timestamp`, `payload`.

---

## 🛠 Error Codes

| Status Code | Meaning | Description |
| :--- | :--- | :--- |
| `401` | Unauthorized | Missing or invalid JWT |
| `403` | Forbidden | Insufficient role permissions |
| `404` | Not Found | Employee or department not found |
| `409` | Conflict | Duplicate email or department name |
| `422` | Validation Error | Input data fails Pydantic validation |
| `503` | Service Unavailable | Dependent service unavailable |

---

## 🗄 Database Tables

### employees
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `user_id` | UUID | Unique, indexed (ref to auth-service) |
| `first_name` | String(100) | Not null |
| `last_name` | String(100) | Not null |
| `email` | String(255) | Unique, indexed |
| `phone` | String(20) | Nullable |
| `gender` | String(10) | Nullable |
| `date_of_birth` | Date | Nullable |
| `date_joined` | Date | Not null |
| `department_id` | UUID | FK → departments.id, indexed |
| `designation` | String(100) | Nullable |
| `employment_status` | String(20) | Default: active, indexed |
| `address` | String(500) | Nullable |
| `created_at` | DateTime | UTC, indexed |
| `updated_at` | DateTime | UTC |

### departments
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `name` | String(150) | Unique, indexed |
| `description` | String(500) | Nullable |
| `manager_id` | UUID | Nullable |
| `created_at` | DateTime | UTC |
| `updated_at` | DateTime | UTC |
