# Attendance Service Contract (v3)

The Attendance Service tracks employee clock-in/clock-out, work hours, overtime, tasks, daily ratings, productivity reports, and supports geofence-based attendance validation.

## Base URL
- **Internal (Docker)**: `http://attendance-service:8002/api/v1`
- **Gateway**: `/api/v1/attendance/*`

---

## Authentication
- JWT Bearer Token (shared public key with auth-service)
- **JWT Blacklist**: Redis-based JWT blacklist check on every authenticated request (fail-open — if Redis is unavailable, the token is accepted)
- See [SERVICE_AUTH_INTEGRATION_GUIDE.md](../SERVICE_AUTH_INTEGRATION_GUIDE.md)

---

## Cross-Service Employee Validation

The following endpoints validate that the target `employee_id` belongs to the same `company_id` as the authenticated user by calling the employee-service internal endpoint (`GET /api/v1/internal/employees/{employee_id}`):

- `POST /attendance/clock-in`
- `POST /attendance/manual`
- `POST /attendance/school-mode`
- `POST /attendance/school-mode/bulk`

If the employee is not found or belongs to a different company, the request is rejected with `403 Forbidden`.

---

## Endpoints

### Attendance Records

| # | Method | Path | RBAC | Description |
|---|---|---|---|---|
| 1 | `POST` | `/attendance/clock-in` | Any | Clock in (geofence validated if required). **Rate limit: 5/min per IP** |
| 2 | `POST` | `/attendance/clock-out` | Any | Clock out with optional day rating and task completions. **Rate limit: 5/min per IP** |
| 3 | `GET` | `/attendance/me/today` | Any | Today's record for authenticated user |
| 4 | `GET` | `/attendance/me` | Any | My history (paginated, date filters) |
| 5 | `GET` | `/attendance` | HR, Admin, Manager | All records (filters: employee, date, status) |
| 6 | `GET` | `/attendance/{id}` | HR, Admin | Specific record |
| 7 | `PATCH` | `/attendance/{id}` | HR, Admin | Manual correction |
| 8 | `POST` | `/attendance/manual` | HR, Admin | Manual/backdated entry |
| 9 | `POST` | `/attendance/school-mode` | HR, Admin | Mark attendance on employee's behalf |
| 10 | `POST` | `/attendance/school-mode/bulk` | HR, Super Admin | Mark attendance for multiple employees at once |

### Tasks

| # | Method | Path | RBAC | Description |
|---|---|---|---|---|
| 11 | `POST` | `/attendance/tasks?record_id=uuid` | Any | Add task to attendance record |
| 12 | `GET` | `/attendance/tasks/today` | Any | Get today's tasks |
| 13 | `PATCH` | `/attendance/tasks/{task_id}` | Any | Update task before completion |
| 14 | `DELETE` | `/attendance/tasks/{task_id}` | Any | Delete task (204 No Content) |
| 15 | `PATCH` | `/attendance/tasks/{task_id}/complete` | Any | Mark task complete at punch-out |
| 16 | `POST` | `/attendance/tasks/assign` | Any | Assign task to another employee |

### Reports

| # | Method | Path | RBAC | Description |
|---|---|---|---|---|
| 17 | `GET` | `/attendance/reports/productivity` | HR, Admin, Manager | Monthly productivity report |

**Query Parameters**: `year` (required), `month` (1-12, required), `employee_id` (optional)

### Alerts

| # | Method | Path | RBAC | Description |
|---|---|---|---|---|
| 18 | `GET` | `/attendance/alerts` | HR, Admin, Manager | Today's attendance alerts |

### Geofence Management

| # | Method | Path | RBAC | Description |
|---|---|---|---|---|
| 19 | `POST` | `/attendance/geofences` | HR, Admin | Create office location |
| 20 | `GET` | `/attendance/geofences` | HR, Admin | List geofences (with pagination and inactive filter) |
| 21 | `PATCH` | `/attendance/geofences/{id}` | HR, Super Admin | Update geofence name/coords/radius |
| 22 | `DELETE` | `/attendance/geofences/{id}` | HR, Super Admin | Soft delete geofence (sets is_active=false) |

### Attendance Policies

| # | Method | Path | RBAC | Description |
|---|---|---|---|---|
| 23 | `POST` | `/attendance/policies` | HR, Admin | Assign method to dept/employee |
| 24 | `GET` | `/attendance/policies` | HR, Admin | List all policies (paginated) |
| 25 | `PATCH` | `/attendance/policies/{id}` | HR, Super Admin | Update policy method/times/scope |
| 26 | `DELETE` | `/attendance/policies/{id}` | HR, Super Admin | Hard delete policy (204 No Content) |

### Health Check

| # | Method | Path | RBAC | Description |
|---|---|---|---|---|
| 27 | `GET` | `/health` | None | Service health check |

---

## Request/Response Bodies

### Clock-In Request
```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "location_name": "HQ Office",
  "notes": "optional"
}
```

### Clock-Out Request
```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "location_name": "HQ Office",
  "notes": "optional",
  "day_rating": 4,
  "task_completions": [
    {
      "task_id": "uuid",
      "status": "completed",
      "completion_notes": "Done",
      "actual_expenses": 150.00
    }
  ]
}
```

### Manual Attendance Create
```json
{
  "employee_id": "uuid",
  "date": "2026-03-15",
  "clock_in": "2026-03-15T09:00:00",
  "clock_out": "2026-03-15T18:00:00",
  "status": "present",
  "notes": "Backdated entry"
}
```

### School-Mode Attendance Create
```json
{
  "employee_id": "uuid",
  "status": "present",
  "notes": "Marked by HR"
}
```

### School-Mode Bulk Attendance Request
```json
{
  "items": [
    {
      "employee_id": "uuid",
      "status": "present",
      "notes": "Marked by HR"
    },
    {
      "employee_id": "uuid",
      "status": "late",
      "notes": "Arrived after 10am"
    }
  ]
}
```

### School-Mode Bulk Attendance Response
```json
{
  "total": 2,
  "succeeded": 1,
  "failed": 1,
  "results": [
    {
      "index": 0,
      "employee_id": "uuid",
      "success": true
    },
    {
      "index": 1,
      "employee_id": "uuid",
      "success": false,
      "error": "Employee already has attendance record for today"
    }
  ]
}
```

### Task Create
```json
{
  "title": "Complete report",
  "details": "Monthly sales report",
  "estimated_finish_time": "2026-03-15T17:00:00",
  "expected_expenses": 100.00
}
```

### Task Complete Update
```json
{
  "status": "completed",
  "completion_notes": "Report submitted",
  "actual_expenses": 80.00
}
```

### Task Assign Request
```json
{
  "target_employee_id": "uuid",
  "title": "Review PR",
  "details": "Review pull request #42",
  "estimated_finish_time": "2026-03-15T17:00:00",
  "expected_expenses": 0.00
}
```

### Geofence Create
```json
{
  "name": "HQ Office",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "radius_meters": 200
}
```

### Geofence Update (PATCH)
```json
{
  "name": "HQ Office - Main Building",
  "latitude": 28.6140,
  "longitude": 77.2091,
  "radius_meters": 250
}
```
All fields are optional. Returns `409 Conflict` if the updated name conflicts with an existing geofence.

### List Geofences Query Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `include_inactive` | boolean | `false` | Include soft-deleted geofences |
| `skip` | integer | `0` | Pagination offset |
| `limit` | integer | `100` | Pagination page size |

### Policy Create
```json
{
  "department_id": "uuid",
  "employee_id": "uuid",
  "method": "geofence",
  "geofence_id": "uuid",
  "work_start_time": "09:00",
  "work_hours_per_day": 8.0
}
```

**Policy priority**: Employee-level > Department-level > Default (manual)

### Policy Update (PATCH)
```json
{
  "department_id": "uuid",
  "employee_id": "uuid",
  "method": "both",
  "geofence_id": "uuid",
  "work_start_time": "08:30",
  "work_hours_per_day": 9.0
}
```
All fields are optional.

### List Policies Query Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `skip` | integer | `0` | Pagination offset |
| `limit` | integer | `100` | Pagination page size |

### Health Check Response
```json
{
  "status": "healthy",
  "service": "attendance-service",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "rabbitmq": "ok",
    "redis": "ok"
  }
}
```

### Geofence Response
All geofence responses include `company_id`:
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "name": "HQ Office",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "radius_meters": 200,
  "is_active": true
}
```

### Policy Response
All policy responses include `company_id`:
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "department_id": "uuid",
  "employee_id": "uuid",
  "method": "geofence",
  "geofence_id": "uuid",
  "work_start_time": "09:00",
  "work_hours_per_day": 8.0
}
```

### Attendance Record Response
All attendance record responses include `company_id`:
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "employee_id": "uuid",
  "date": "2026-03-15",
  "clock_in": "2026-03-15T09:00:00",
  "clock_out": "2026-03-15T18:00:00",
  "work_hours": 8.0,
  "overtime_hours": 0.0,
  "status": "present",
  "method": "geofence",
  "notes": null,
  "day_rating": 4
}
```

---

## Geofence Validation Flow
```
Clock-in/out request
      |
      v
Resolve policy (employee -> department -> default)
      |
      v
Method = geofence or both?
      |
  Yes --> Require lat/lng -> haversine distance check
  |          |
  |     Within radius? --> Allow
  |          |
  |     Outside radius? --> 403 Forbidden
  |
  No --> Allow (manual)
```

---

## Events Published (RabbitMQ)

All event payloads include `company_id` for tenant-aware consumers.

| Event Type | Payload |
|---|---|
| `attendance.clock_in` | company_id, employee_id, method, status, timestamp |
| `attendance.clock_out` | company_id, employee_id, work_hours, overtime_hours |
| `attendance.manual_entry` | company_id, employee_id, date, created_by |

---

## Error Codes

| Status | Reason |
|---|---|
| `401` | Missing/expired/blacklisted JWT |
| `403` | Role insufficient OR outside geofence OR employee belongs to different company |
| `404` | No record found |
| `409` | Already clocked in/out today OR geofence name conflict |
| `422` | Missing lat/lng for geofence method |
| `429` | Rate limit exceeded (clock-in/clock-out: 5/min per IP) |

---

## Database Tables

### attendance_records
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `company_id` | UUID | Tenant isolation, indexed |
| `employee_id` | UUID | Indexed |
| `clock_in` / `clock_out` | DateTime | UTC |
| `clock_in_lat` / `clock_in_lng` | Float | Geofence coords |
| `clock_out_lat` / `clock_out_lng` | Float | Geofence coords |
| `clock_in_location` / `clock_out_location` | String | Location name |
| `work_hours` | Float | Computed on clock-out |
| `overtime_hours` | Float | Over work_hours_per_day |
| `status` | String | present, late, half_day, absent |
| `method` | String | manual, geofence |
| `notes` | Text | Nullable |
| `day_rating` | Integer | 1-5, nullable |
| `date` | Date | UNIQUE with employee_id |

### attendance_tasks
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `attendance_record_id` | UUID | FK -> attendance_records.id |
| `assigned_by` | UUID | Employee who assigned |
| `title` | String | Not null |
| `details` | Text | Nullable |
| `estimated_finish_time` | DateTime | Nullable |
| `expected_expenses` | Numeric | Nullable |
| `status` | String | pending, completed, incomplete |
| `completion_notes` | Text | Nullable |
| `actual_expenses` | Numeric | Nullable |
| `created_at` | DateTime | UTC |

### geofence_locations
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `company_id` | UUID | Tenant isolation, indexed |
| `name` | String | Unique per company |
| `latitude` / `longitude` | Float | Center point |
| `radius_meters` | Int | Default 200 |
| `is_active` | Boolean | Default true |

### attendance_policies
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `company_id` | UUID | Tenant isolation, indexed |
| `department_id` | UUID | Nullable |
| `employee_id` | UUID | Nullable (overrides dept) |
| `method` | String | manual, geofence, both |
| `geofence_id` | UUID | FK -> geofence_locations |
| `work_start_time` | Time | For late detection |
| `work_hours_per_day` | Float | For overtime calc |
