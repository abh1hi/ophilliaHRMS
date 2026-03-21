# Students Service Contract (v3)

The Students Service manages student enrollment, class/grade management, and guardian records for educational institutions using the HRMS platform.

## Base URL
- **Internal (Docker)**: `http://students-service:8003/api/v1`
- **Gateway**: `/api/v1/students/*`, `/api/v1/classes/*`, `/api/v1/guardians/*`

---

## Authentication
- JWT Bearer Token (shared public key with auth-service)
- **JWT Blacklist**: On every request, the service checks a Redis-based JWT blacklist (token `jti` claim). If the token is blacklisted, the request is rejected with `401`. If Redis is unavailable, the check **fails open** (request proceeds with normal JWT validation only).
- See [SERVICE_AUTH_INTEGRATION_GUIDE.md](../SERVICE_AUTH_INTEGRATION_GUIDE.md)

---

## Multi-Tenancy

All data in the Students Service is isolated by `company_id` (tenant isolation).

- The `company_id` is extracted from the authenticated user's JWT claims.
- Every database query is automatically scoped to the caller's `company_id`.
- Students, classes, and guardians belong to a single company and are never visible across tenants.
- All write operations (create, update, delete) enforce `company_id` matching — a user cannot modify resources belonging to another company.
- All response schemas include `company_id: Optional[UUID]`.

---

## Endpoints

### Students

#### 1. Enroll Student

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/students/` | Bearer Token | Admin, HR |

**Request Body**
```json
{
  "first_name": "Rahul",
  "last_name": "Sharma",
  "date_of_birth": "2015-05-10",
  "gender": "male",
  "class_id": "uuid",
  "admission_number": "ADM-2026-001",
  "admission_date": "2026-04-01",
  "address": "123 School Lane",
  "phone": "+91-9876543210",
  "email": "parent@example.com",
  "blood_group": "B+",
  "medical_notes": "None"
}
```

**Response (201 Created)**: StudentResponse object (includes `company_id`)

---

#### 2. List Students

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/students/` | Bearer Token | Admin, HR, Teacher |

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `page` | int | 1 | Page number (min 1) |
| `page_size` | int | 20 | Records per page (max 100) |
| `status` | string | — | Filter by enrollment status |
| `class_id` | UUID | — | Filter by class |

Results are automatically scoped to the caller's `company_id`.

**Response (200 OK)**
```json
{
  "total": 200,
  "page": 1,
  "page_size": 20,
  "items": [...]
}
```

---

#### 3. Get Student Profile

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/students/{student_id}` | Bearer Token | Admin, HR, Teacher |

---

#### 4. Update Student

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PUT` | `/students/{student_id}` | Bearer Token | Admin, HR |

---

#### 5. Change Student Enrollment Status

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PATCH` | `/students/{student_id}/status` | Bearer Token | Admin |

**Request Body**
```json
{
  "status": "graduated"
}
```

Valid statuses: `active`, `inactive`, `graduated`, `transferred`, `expelled`

---

#### 6. Delete Student

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `DELETE` | `/students/{student_id}` | Bearer Token | Admin |

**Response**: `204 No Content`

---

### Classes

#### 7. Create Class

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/classes/` | Bearer Token | Admin |

**Request Body**
```json
{
  "name": "Class 10-A",
  "grade_level": 10,
  "academic_year": "2026-2027",
  "description": "Science stream"
}
```

---

#### 8. List Classes

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/classes/` | Bearer Token | Admin, HR, Teacher |

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Records per page (max 100) |
| `academic_year` | string | — | Filter by academic year |
| `grade_level` | int | — | Filter by grade |

---

#### 9. Get Class Details

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/classes/{class_id}` | Bearer Token | Admin, HR, Teacher |

---

#### 10. Update Class

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PUT` | `/classes/{class_id}` | Bearer Token | Admin |

---

#### 11. Delete Class

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `DELETE` | `/classes/{class_id}` | Bearer Token | Admin |

**Response**: `204 No Content`

---

### Guardians

#### 12. Add Guardian

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/guardians/` | Bearer Token | Admin, HR |

**Request Body**
```json
{
  "student_id": "uuid",
  "name": "Mr. Sharma",
  "relationship": "Father",
  "email": "parent@example.com",
  "phone": "+91-9876543210"
}
```

---

#### 13. Get Guardian

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/guardians/{guardian_id}` | Bearer Token | Admin, HR |

---

#### 14. Get Guardians for Student

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/guardians/student/{student_id}` | Bearer Token | Admin, HR |

**Response (200 OK)**: List of GuardianResponse objects

---

#### 15. Update Guardian

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PUT` | `/guardians/{guardian_id}` | Bearer Token | Admin, HR |

---

#### 16. Delete Guardian

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `DELETE` | `/guardians/{guardian_id}` | Bearer Token | Admin |

**Response**: `204 No Content`

---

### Health Check

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/health` | None |

**Response (200 OK)**
```json
{
  "status": "healthy",
  "service": "students-service",
  "version": "1.0.0",
  "checks": {
    "database": "connected",
    "rabbitmq": "connected",
    "redis": "connected"
  }
}
```

---

## Events Published (RabbitMQ)

All event payloads include `company_id` to support tenant-scoped audit logging and downstream processing.

| Event Type | When | Payload |
| :--- | :--- | :--- |
| `student.enrolled` | New student created | company_id, student_id, name, class_id |
| `student.status_changed` | Enrollment status updated | company_id, student_id, old_status, new_status |

---

## Error Codes

| Status Code | Meaning | Description |
| :--- | :--- | :--- |
| `401` | Unauthorized | Missing or invalid JWT, or token blacklisted |
| `403` | Forbidden | Insufficient role permissions |
| `404` | Not Found | Student, class, or guardian not found |
| `409` | Conflict | Duplicate admission number |
| `422` | Validation Error | Invalid input data |

---

## Database Tables

### students
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Not null, indexed |
| `first_name` | String | Not null |
| `last_name` | String | Not null |
| `date_of_birth` | Date | Nullable |
| `gender` | String | Nullable |
| `class_id` | UUID | FK -> classes.id, nullable |
| `admission_number` | String | Unique |
| `admission_date` | Date | Nullable |
| `status` | String | Default: active |
| `address` | Text | Nullable |
| `phone` | String | Nullable |
| `email` | String | Nullable |
| `blood_group` | String | Nullable |
| `medical_notes` | Text | Nullable |
| `created_at` | DateTime | UTC |
| `updated_at` | DateTime | UTC |

### classes
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Not null, indexed |
| `name` | String | Not null |
| `grade_level` | Integer | Not null |
| `academic_year` | String | Nullable |
| `description` | Text | Nullable |
| `created_at` | DateTime | UTC |
| `updated_at` | DateTime | UTC |

### guardians
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `student_id` | UUID | FK -> students.id, indexed |
| `name` | String | Not null |
| `relationship` | String | Not null |
| `email` | String | Nullable |
| `phone` | String | Nullable |
| `created_at` | DateTime | UTC |
| `updated_at` | DateTime | UTC |
