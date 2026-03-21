# Leave Service Contract (v3)

The Leave Service manages leave requests, leave types, leave balances, holidays, and a leave calendar for the HRMS platform.

## Base URL
- **Internal (Docker)**: `http://leave-service:8005/api/v1`
- **Gateway**: `/api/v1/leave/*`

---

## Authentication
- JWT Bearer Token (shared public key with auth-service)
- **JWT Blacklist**: Redis-based JWT blacklist check is performed on every authenticated request. The blacklist operates in fail-open mode — if Redis is unavailable, the token is assumed valid to avoid blocking legitimate requests.
- See [SERVICE_AUTH_INTEGRATION_GUIDE.md](../SERVICE_AUTH_INTEGRATION_GUIDE.md)

---

## Endpoints

### Leave Requests

#### 1. Apply for Leave

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/leave/` | Bearer Token | Any Authenticated |

Employees can only apply for themselves.

**Rate Limit**: 10 requests per minute per IP.

**Cross-Service Validation**: The `employee_id` is validated against the employee-service internal endpoint to confirm the employee belongs to the same `company_id` as the authenticated user.

**Request Body**
```json
{
  "employee_id": "uuid",
  "leave_type_id": "uuid",
  "start_date": "2026-04-01",
  "end_date": "2026-04-03",
  "duration_type": "full_day",
  "is_emergency": false,
  "reason": "Family function",
  "supporting_document": "https://storage.example.com/doc.pdf"
}
```

**Response (201 Created)**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "employee_id": "uuid",
    "leave_type_id": "uuid",
    "company_id": "uuid | null",
    "start_date": "2026-04-01",
    "end_date": "2026-04-03",
    "duration_type": "full_day",
    "total_days": 3.0,
    "status": "pending",
    "is_emergency": false,
    "reason": "Family function",
    "created_at": "ISO-8601"
  }
}
```

---

#### 2. List Leave Requests

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/leave/` | Bearer Token | Any Authenticated |

Employees see only their own requests. HR/Manager/Admin see all.

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Records per page |

**Response (200 OK)**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "employee_id": "uuid",
      "company_id": "uuid | null",
      "...": "..."
    }
  ],
  "meta": {
    "total": 45,
    "page": 1,
    "page_size": 20
  }
}
```

---

#### 3. Update Leave Request Status

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PUT` | `/leave/{request_id}/status` | Bearer Token | HR, Manager, Super Admin |

**Request Body**
```json
{
  "status": "approved",
  "manager_notes": "Approved. Enjoy your leave."
}
```

Valid statuses: `approved`, `rejected`, `cancelled`

---

### Leave Types

#### 4. List Leave Types

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/leave/leave-types/` | Bearer Token | Any Authenticated |

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `include_inactive` | bool | false | When true, includes leave types where `is_active=false` |

**Response (200 OK)**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "company_id": "uuid | null",
      "name": "Casual Leave",
      "description": "For personal reasons",
      "days_allowed": 12,
      "requires_approval": true,
      "is_active": true
    }
  ]
}
```

---

#### 5. Create Leave Type

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/leave/leave-types/` | Bearer Token | HR, Super Admin |

**Request Body**
```json
{
  "name": "Casual Leave",
  "description": "For personal reasons",
  "days_allowed": 12,
  "requires_approval": true,
  "is_active": true
}
```

**Response (201 Created)**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "company_id": "uuid | null",
    "name": "Casual Leave",
    "description": "For personal reasons",
    "days_allowed": 12,
    "requires_approval": true,
    "is_active": true
  }
}
```

---

#### 6. Update Leave Type

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PATCH` | `/leave/leave-types/{id}` | Bearer Token | HR, Super Admin |

All fields are optional. If `name` is provided, a duplicate-name check is performed within the same company scope.

**Request Body**
```json
{
  "name": "Sick Leave",
  "description": "Updated description",
  "days_allowed": 15,
  "requires_approval": false,
  "is_active": true
}
```

**Response (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "company_id": "uuid | null",
    "name": "Sick Leave",
    "description": "Updated description",
    "days_allowed": 15,
    "requires_approval": false,
    "is_active": true
  }
}
```

---

#### 7. Delete Leave Type (Soft Delete)

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `DELETE` | `/leave/leave-types/{id}` | Bearer Token | HR, Super Admin |

Soft deletes the leave type by setting `is_active=false`.

**Response (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "company_id": "uuid | null",
    "name": "Casual Leave",
    "description": "For personal reasons",
    "days_allowed": 12,
    "requires_approval": true,
    "is_active": false
  }
}
```

---

### Leave Balances

#### 8. Get Leave Balances

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/leave/leave-balances/{employee_id}` | Bearer Token | Any Authenticated |

Employees can only access their own balances.

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `year` | int | Current year | Year to fetch balances for |

**Response (200 OK)**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "employee_id": "uuid",
      "leave_type_id": "uuid",
      "company_id": "uuid | null",
      "total_days": 12.0,
      "used_days": 3.0,
      "pending_days": 1.0,
      "remaining_days": 8.0,
      "year": 2026
    }
  ]
}
```

---

#### 9. Create Leave Balance

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/leave/leave-balances/` | Bearer Token | HR, Super Admin |

**Request Body**
```json
{
  "employee_id": "uuid",
  "leave_type_id": "uuid",
  "total_days": 12.0,
  "used_days": 0.0,
  "pending_days": 0.0,
  "year": 2026
}
```

**Response (201 Created)**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "employee_id": "uuid",
    "leave_type_id": "uuid",
    "company_id": "uuid | null",
    "total_days": 12.0,
    "used_days": 0.0,
    "pending_days": 0.0,
    "remaining_days": 12.0,
    "year": 2026
  }
}
```

---

#### 10. Update Leave Balance

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PATCH` | `/leave/leave-balances/{id}` | Bearer Token | HR, Super Admin |

Manual HR adjustment of leave balance fields. All fields are optional.

**Request Body**
```json
{
  "total_days": 15.0,
  "used_days": 2.0,
  "pending_days": 1.0
}
```

**Response (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "employee_id": "uuid",
    "leave_type_id": "uuid",
    "company_id": "uuid | null",
    "total_days": 15.0,
    "used_days": 2.0,
    "pending_days": 1.0,
    "remaining_days": 12.0,
    "year": 2026
  }
}
```

---

#### 11. Bulk Allocate Leave Balances

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/leave/leave-balances/bulk` | Bearer Token | HR, Super Admin |

Allocates leave balances for multiple employees at once. Rows where a balance already exists for the given employee + leave type + year are skipped and reported as failed.

**Request Body**
```json
{
  "leave_type_id": "uuid",
  "year": 2026,
  "items": [
    { "employee_id": "uuid", "total_days": 12.0 },
    { "employee_id": "uuid", "total_days": 10.0 }
  ]
}
```

**Response (200 OK)**
```json
{
  "success": true,
  "data": {
    "total": 2,
    "succeeded": 1,
    "failed": 1,
    "results": [
      { "index": 0, "employee_id": "uuid", "success": true },
      { "index": 1, "employee_id": "uuid", "success": false, "error": "Balance already exists" }
    ]
  }
}
```

---

### Holidays

#### 12. Create Holiday

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/leave/holidays/` | Bearer Token | HR, Super Admin |

**Request Body**
```json
{
  "name": "Republic Day",
  "date": "2026-01-26",
  "description": "National holiday"
}
```

---

#### 13. List Holidays

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/leave/holidays/` | Bearer Token | Any Authenticated |

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `include_inactive` | bool | false | When true, includes holidays where `is_active=false` |
| `skip` | int | 0 | Number of records to skip (pagination offset) |
| `limit` | int | 100 | Maximum number of records to return |

---

#### 14. Delete Holiday (Soft Delete)

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `DELETE` | `/leave/holidays/{holiday_id}` | Bearer Token | HR, Super Admin |

**Response**: `204 No Content`

---

### Leave Calendar

#### 15. Get Leave Calendar

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/leave/leave-calendar/` | Bearer Token | HR, Manager, Super Admin |

**Query Parameters**
| Param | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `start_date` | date | Yes | Calendar start |
| `end_date` | date | Yes | Calendar end |

**Response (200 OK)**
```json
{
  "success": true,
  "data": [
    {
      "date": "2026-04-01",
      "employees_on_leave": [
        {
          "employee_id": "uuid",
          "leave_type": "Casual Leave",
          "status": "approved"
        }
      ],
      "is_holiday": false
    }
  ]
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
  "service": "leave-service",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

---

## Events Published (RabbitMQ)

All event payloads include `company_id` to support multi-tenant routing and filtering.

| Event Type | When | Payload |
| :--- | :--- | :--- |
| `leave.requested` | New leave request created | company_id, employee_id, leave_type, start_date, end_date, total_days |
| `leave.approved` | Leave request approved | company_id, request_id, employee_id, approved_by |
| `leave.rejected` | Leave request rejected | company_id, request_id, employee_id, rejected_by, reason |

---

## Error Codes

| Status Code | Meaning | Description |
| :--- | :--- | :--- |
| `401` | Unauthorized | Missing or invalid JWT |
| `403` | Forbidden | Insufficient role or accessing another user's data |
| `404` | Not Found | Leave request, type, or balance not found |
| `409` | Conflict | Overlapping leave dates or duplicate holiday |
| `422` | Validation Error | Invalid input data |
| `429` | Too Many Requests | Rate limit exceeded (e.g., leave apply endpoint) |

---

## Response Schemas

All response data objects include a `company_id` field for multi-tenant support:

```
company_id: Optional[UUID]
```

This field is present in `LeaveRequestResponse`, `LeaveTypeResponse`, `LeaveBalanceResponse`, and `HolidayResponse` schemas.

---

## Database Tables

### leave_requests
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `employee_id` | UUID | Not null, indexed |
| `leave_type_id` | UUID | FK -> leave_types.id |
| `company_id` | UUID | Nullable, indexed |
| `start_date` | Date | Not null |
| `end_date` | Date | Not null |
| `duration_type` | String | full_day, half_day, short_leave |
| `total_days` | Float | Computed |
| `status` | String | pending, approved, rejected, cancelled |
| `is_emergency` | Boolean | Default: false |
| `reason` | Text | Not null |
| `manager_notes` | Text | Nullable |
| `supporting_document` | String | Nullable |
| `created_at` | DateTime | UTC |
| `updated_at` | DateTime | UTC |

### leave_types
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Nullable, indexed |
| `name` | String | Not null, unique per company |
| `description` | Text | Nullable |
| `days_allowed` | Integer | Not null |
| `requires_approval` | Boolean | Default: true |
| `is_active` | Boolean | Default: true |

### leave_balances
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `employee_id` | UUID | Not null, indexed |
| `leave_type_id` | UUID | FK -> leave_types.id |
| `company_id` | UUID | Nullable, indexed |
| `total_days` | Float | Not null |
| `used_days` | Float | Default: 0 |
| `pending_days` | Float | Default: 0 |
| `year` | Integer | Not null |

### holidays
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Nullable, indexed |
| `name` | String | Not null |
| `date` | Date | Not null |
| `description` | Text | Nullable |
| `is_active` | Boolean | Default: true |
