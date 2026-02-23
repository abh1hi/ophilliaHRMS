# HRMS API — Postman Testing Guide

**Base URL:** `http://localhost`  
**API Prefix:** `/api/v1`

---

## ⚙️ Setup: Environment Variables

Create a **Postman Environment** called `HRMS Local` with these variables:

| Variable | Initial Value |
|---|---|
| `base_url` | `http://localhost` |
| `access_token` | _(leave empty — filled automatically)_ |
| `refresh_token` | _(leave empty — filled automatically)_ |
| `user_id` | _(leave empty — filled automatically)_ |
| `employee_id` | _(leave empty — filled after creating an employee)_ |
| `geofence_id` | _(leave empty — filled after creating a geofence)_ |

### Auto-save Token Script

On the **Login** request, add this to the **Tests** tab to automatically store the token:

```javascript
const res = pm.response.json();
if (res.access_token) {
    pm.environment.set("access_token", res.access_token);
    pm.environment.set("refresh_token", res.refresh_token);
}
```

### Auth Header (for protected routes)

In any protected request, go to **Authorization** tab:
- Type: `Bearer Token`
- Token: `{{access_token}}`

---

## 🔐 Auth Service (`/api/v1/auth`)

### 1. Register a New User

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/auth/register` |
| **Body (JSON)** | see below |

```json
{
  "email": "admin@ophillia.com",
  "password": "Admin@1234",
  "role": "super_admin"
}
```

> **Valid roles:** `super_admin`, `hr`, `manager`, `employee`

**Expected:** `201 Created`
```json
{
  "id": "uuid",
  "email": "admin@ophillia.com",
  "role": "super_admin",
  "is_active": true
}
```

---

### 2. Login

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/auth/login` |
| **Body (JSON)** | see below |

```json
{
  "email": "admin@ophillia.com",
  "password": "Admin@1234"
}
```

**Expected:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

> **Run the Tests script above** to save the token automatically.

---

### 3. Get Current User (Me)

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/auth/me` |
| **Auth** | Bearer `{{access_token}}` |

**Expected:** `200 OK` — Returns the authenticated user's profile.

---

### 4. Refresh Access Token

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/auth/refresh` |
| **Body (JSON)** | see below |

```json
{
  "refresh_token": "{{refresh_token}}"
}
```

**Expected:** `200 OK` — Returns a new `access_token`.

---

### 5. Logout

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/auth/logout` |
| **Auth** | Bearer `{{access_token}}` |
| **Body (JSON)** | see below |

```json
{
  "refresh_token": "{{refresh_token}}"
}
```

**Expected:** `200 OK`

---

### 6. Change Password

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/auth/change-password` |
| **Auth** | Bearer `{{access_token}}` |
| **Body (JSON)** | see below |

```json
{
  "current_password": "Admin@1234",
  "new_password": "NewPass@5678"
}
```

**Expected:** `200 OK`

---

### 7. List All Users _(Super Admin only)_

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/auth/users` |
| **Auth** | Bearer `{{access_token}}` (must be `super_admin`) |

**Expected:** `200 OK` — Returns paginated list of users.

---

### 8. Update User Role _(Super Admin only)_

| Field | Value |
|---|---|
| **Method** | `PATCH` |
| **URL** | `{{base_url}}/api/v1/auth/users/{user_id}/role` |
| **Auth** | Bearer `{{access_token}}` (must be `super_admin`) |
| **Body (JSON)** | see below |

```json
{
  "role": "hr"
}
```

**Expected:** `200 OK`

---

### 9. Auth Health Check

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/auth/health` |

**Expected:** `200 OK` — `{"status": "healthy", "service": "auth-service"}`

---

## 👤 Employee Service (`/api/v1/employees`)

> All employee endpoints require a valid JWT. Use `Authorization: Bearer {{access_token}}`.

### 1. Create Employee Profile _(HR / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/employees` |
| **Auth** | Bearer `{{access_token}}` |

**Body (JSON):**
```json
{
  "user_id": "{{user_id}}",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+919876543210",
  "department_id": null,
  "job_title": "Software Engineer",
  "date_of_joining": "2024-01-15",
  "employment_type": "full_time"
}
```

**Tests script** to save the employee ID:
```javascript
const res = pm.response.json();
if (res.id) pm.environment.set("employee_id", res.id);
```

**Expected:** `201 Created`

---

### 2. Get My Employee Profile

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/employees/me` |
| **Auth** | Bearer `{{access_token}}` |

**Expected:** `200 OK` — Returns the requester's employee record.

---

### 3. List All Employees _(HR / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/employees?skip=0&limit=20` |
| **Auth** | Bearer `{{access_token}}` |

**Query Params (optional):** `skip`, `limit`, `department_id`, `search`

**Expected:** `200 OK`

---

### 4. Get Employee by ID _(HR / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/employees/{{employee_id}}` |
| **Auth** | Bearer `{{access_token}}` |

**Expected:** `200 OK`

---

### 5. Update Employee Profile _(HR / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `PATCH` |
| **URL** | `{{base_url}}/api/v1/employees/{{employee_id}}` |
| **Auth** | Bearer `{{access_token}}` |

**Body (JSON) — only include fields to update:**
```json
{
  "job_title": "Senior Software Engineer",
  "department_id": null
}
```

**Expected:** `200 OK`

---

### 6. Deactivate Employee _(HR / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `DELETE` |
| **URL** | `{{base_url}}/api/v1/employees/{{employee_id}}` |
| **Auth** | Bearer `{{access_token}}` |

**Expected:** `200 OK` or `204 No Content`

---

### 7. Create Department _(HR / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/departments` |
| **Auth** | Bearer `{{access_token}}` |

**Body (JSON):**
```json
{
  "name": "Engineering",
  "description": "Product and platform engineering"
}
```

**Expected:** `201 Created`

---

### 8. List Departments

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/departments` |
| **Auth** | Bearer `{{access_token}}` |

**Expected:** `200 OK`

---

### 9. Employee Health Check

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/employees/health` |

**Expected:** `200 OK`

---

## 📅 Attendance Service (`/api/v1/attendance`)

> All attendance endpoints require a valid JWT.

### 1. Clock In

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/attendance/clock-in` |
| **Auth** | Bearer `{{access_token}}` |

**Body (JSON):**
```json
{
  "latitude": 12.9716,
  "longitude": 77.5946,
  "notes": "On-site"
}
```

> If geofence is not required by policy, omit `latitude`/`longitude`.

**Expected:** `201 Created`

---

### 2. Clock Out

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/attendance/clock-out` |
| **Auth** | Bearer `{{access_token}}` |

**Body (JSON):**
```json
{
  "latitude": 12.9716,
  "longitude": 77.5946,
  "notes": "Leaving for the day"
}
```

**Expected:** `200 OK` — Returns updated record with work hours.

---

### 3. Get Today's Record

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/attendance/me/today` |
| **Auth** | Bearer `{{access_token}}` |

**Expected:** `200 OK` or `null` (if not clocked in yet).

---

### 4. Get My Attendance History

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/attendance/me?skip=0&limit=30` |
| **Auth** | Bearer `{{access_token}}` |

**Optional query params:** `date_from=2024-01-01`, `date_to=2024-12-31`

**Expected:** `200 OK`

---

### 5. List All Attendance Records _(HR / Manager / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/attendance?skip=0&limit=20` |
| **Auth** | Bearer `{{access_token}}` |

**Optional filters:** `employee_id`, `date_from`, `date_to`, `status` (`present`, `late`, `half_day`, `absent`)

**Expected:** `200 OK`

---

### 6. Get Specific Attendance Record _(HR / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/attendance/{record_id}` |
| **Auth** | Bearer `{{access_token}}` |

**Expected:** `200 OK`

---

### 7. Manual Attendance Entry _(HR / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/attendance/manual` |
| **Auth** | Bearer `{{access_token}}` |

**Body (JSON):**
```json
{
  "employee_id": "{{employee_id}}",
  "work_date": "2024-01-20",
  "clock_in": "09:00:00",
  "clock_out": "17:00:00",
  "status": "present",
  "notes": "Backdated entry"
}
```

**Expected:** `201 Created`

---

### 8. Create Geofence _(HR / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/attendance/geofences` |
| **Auth** | Bearer `{{access_token}}` |

**Body (JSON):**
```json
{
  "name": "Ophillia HQ",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "radius_meters": 200,
  "is_active": true
}
```

**Tests script:**
```javascript
const res = pm.response.json();
if (res.id) pm.environment.set("geofence_id", res.id);
```

**Expected:** `201 Created`

---

### 9. List Geofences _(HR / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/attendance/geofences` |
| **Auth** | Bearer `{{access_token}}` |

**Expected:** `200 OK`

---

### 10. Create Attendance Policy _(HR / Super Admin)_

| Field | Value |
|---|---|
| **Method** | `POST` |
| **URL** | `{{base_url}}/api/v1/attendance/policies` |
| **Auth** | Bearer `{{access_token}}` |

**Body (JSON):**
```json
{
  "name": "Default Policy",
  "attendance_method": "manual",
  "geofence_id": null,
  "department_id": null,
  "work_hours_per_day": 8.0,
  "work_start_time": "09:00",
  "is_active": true
}
```

> `attendance_method` options: `manual`, `geofence`, `both`

**Expected:** `201 Created`

---

### 11. Attendance Health Check

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL** | `{{base_url}}/api/v1/attendance/health` |

**Expected:** `200 OK`

---

## 🧪 Recommended Test Sequence

Run these in order for a complete end-to-end flow:

```
1. POST /auth/register          → Create super_admin user
2. POST /auth/login             → Get access_token (auto-saved by script)
3. GET  /auth/me                → Verify token works
4. POST /api/v1/employees       → Create employee profile
5. GET  /api/v1/employees/me    → Verify employee profile
6. POST /attendance/geofences   → Create a geofence
7. POST /attendance/policies    → Assign attendance policy
8. POST /attendance/clock-in    → Clock in for today
9. GET  /attendance/me/today    → Check current record
10. POST /attendance/clock-out  → Clock out
11. GET  /attendance            → Admin view of all records (HR role)
```

---

## 🚨 Common Error Codes

| HTTP Code | Meaning | Fix |
|---|---|---|
| `401 Unauthorized` | Missing or invalid/expired token | Re-login to get fresh `access_token` |
| `403 Forbidden` | Token is valid but role lacks permission | Use a higher-privilege account (e.g. `super_admin`) |
| `404 Not Found` | Route or record doesn't exist | Check the ID being passed in the URL |
| `409 Conflict` | Duplicate record (e.g. already clocked in) | Clock out first before clocking in again |
| `422 Unprocessable Entity` | Request body validation failed | Check all required fields and types |
| `503 Service Unavailable` | Downstream service is down | Run `docker compose ps` to check container health |
