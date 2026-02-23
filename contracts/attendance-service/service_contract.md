# 📋 Attendance Service Contract (v1)

The Attendance Service tracks employee clock-in/clock-out, work hours, overtime, and supports **geofence-based attendance validation**.

## 🚀 Base URL
- **Internal (Docker)**: `http://attendance-service:8002/api/v1`

---

## 🔑 Authentication
- JWT Bearer Token (shared `SECRET_KEY` with auth-service)
- See [SERVICE_AUTH_INTEGRATION_GUIDE.md](../SERVICE_AUTH_INTEGRATION_GUIDE.md)

---

## 📡 Endpoints

### Attendance Records

| # | Method | Path | RBAC | Description |
|---|---|---|---|---|
| 1 | `POST` | `/attendance/clock-in` | Any | Clock in (geofence validated if required) |
| 2 | `POST` | `/attendance/clock-out` | Any | Clock out (auto-calc hours & overtime) |
| 3 | `GET` | `/attendance/me/today` | Any | Today's record |
| 4 | `GET` | `/attendance/me` | Any | My history (paginated, date filters) |
| 5 | `GET` | `/attendance` | HR, Admin, Manager | All records (filters: employee, date, status) |
| 6 | `GET` | `/attendance/{id}` | HR, Admin | Specific record |
| 7 | `PATCH` | `/attendance/{id}` | HR, Admin | Manual correction |
| 8 | `POST` | `/attendance/manual` | HR, Admin | Manual/backdated entry |

### Geofence Management

| # | Method | Path | RBAC | Description |
|---|---|---|---|---|
| 9 | `POST` | `/attendance/geofences` | HR, Admin | Create office location |
| 10 | `GET` | `/attendance/geofences` | HR, Admin | List active geofences |

### Attendance Policies

| # | Method | Path | RBAC | Description |
|---|---|---|---|---|
| 11 | `POST` | `/attendance/policies` | HR, Admin | Assign method to dept/employee |
| 12 | `GET` | `/attendance/policies` | HR, Admin | List all policies |

---

## ⏰ Clock-In Request
```json
{
  "latitude": 28.6139,      // required if method=geofence/both
  "longitude": 77.2090,     // required if method=geofence/both
  "notes": "optional"
}
```

## ⏰ Clock-Out Request
```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "notes": "optional"
}
```

## 📍 Geofence Create
```json
{
  "name": "HQ Office",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "radius_meters": 200
}
```

## 📋 Policy Create
```json
{
  "department_id": "uuid",      // null for employee-level
  "employee_id": "uuid",        // null for dept-level
  "method": "geofence",         // manual | geofence | both
  "geofence_id": "uuid",        // which geofence to validate against
  "work_start_time": "09:00",   // for late detection
  "work_hours_per_day": 8.0     // for overtime calc
}
```

**Policy priority**: Employee-level > Department-level > Default (manual)

---

## 🌐 Geofence Validation Flow
```
Clock-in/out request
      │
      ▼
Resolve policy (employee → department → default)
      │
      ▼
Method = geofence or both?
      │
  Yes ──► Require lat/lng → haversine distance check
  │          │
  │     Within radius? ──► ✅ Allow
  │          │
  │     Outside radius? ──► ❌ 403 Forbidden
  │
  No ──► ✅ Allow (manual)
```

---

## 📢 Events Published (RabbitMQ)

| Event Type | Payload |
|---|---|
| `attendance.clock_in` | employee_id, method, status, timestamp |
| `attendance.clock_out` | employee_id, work_hours, overtime_hours |
| `attendance.manual_entry` | employee_id, date, created_by |

---

## 🛠 Error Codes

| Status | Reason |
|---|---|
| `401` | Missing/expired JWT |
| `403` | Role insufficient OR outside geofence |
| `404` | No record found |
| `409` | Already clocked in/out today |
| `422` | Missing lat/lng for geofence method |

---

## 🗄 Database Tables

### attendance_records
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `employee_id` | UUID | Indexed |
| `clock_in/out` | DateTime | UTC |
| `clock_in/out_lat/lng` | Float | Geofence coords |
| `work_hours` | Float | Computed on clock-out |
| `overtime_hours` | Float | Over work_hours_per_day |
| `status` | String | present, late, half_day, absent |
| `method` | String | manual, geofence |
| `date` | Date | UNIQUE with employee_id |

### geofence_locations
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `name` | String | Unique (e.g. "HQ Office") |
| `latitude/longitude` | Float | Center point |
| `radius_meters` | Int | Default 200 |
| `is_active` | Boolean | Default true |

### attendance_policies
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `department_id` | UUID | Nullable |
| `employee_id` | UUID | Nullable (overrides dept) |
| `method` | String | manual, geofence, both |
| `geofence_id` | UUID | FK → geofence_locations |
| `work_start_time` | Time | For late detection |
| `work_hours_per_day` | Float | For overtime calc |
