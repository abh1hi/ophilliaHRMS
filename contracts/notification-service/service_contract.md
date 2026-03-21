# Notification Service Contract (v3)

The Notification Service consumes HRMS events from RabbitMQ and dispatches notifications (email, SMS) to users. It also exposes endpoints for notification logs and user preferences. All data is tenant-isolated by `company_id`.

## Base URL
- **Internal (Docker)**: `http://notification-service:8007/api/v1`
- **Gateway**: `/api/v1/notifications/*`

---

## Authentication
- JWT Bearer Token (shared public key with auth-service)
- **Tenant Isolation**: `company_id` is extracted from the JWT and automatically applied to all queries
- See [SERVICE_AUTH_INTEGRATION_GUIDE.md](../SERVICE_AUTH_INTEGRATION_GUIDE.md)

---

## JWT Blacklist

Before accepting any JWT, the notification-service checks Redis for a `bl:{jti}` key (written by auth-service on logout). If the key exists, the token is considered revoked and the request is rejected with `401 Unauthorized`.

- **Fail-open**: If Redis is unavailable, the blacklist check is skipped and the token is accepted. This ensures that a Redis outage does not block all authenticated requests.
- See the [Auth Service Contract](../auth-service/service_contract.md) for full blacklist details.

---

## Endpoints

### 1. Get Notification Logs
Returns notification history for the authenticated user. Employees see only their own notifications.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/notifications/logs/` | Bearer Token | Any Authenticated |

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `skip` | int | 0 | Records to skip |
| `limit` | int | 20 | Max records (1-100) |

**Response (200 OK)**
```json
[
  {
    "id": "uuid",
    "company_id": "uuid",
    "user_id": "uuid",
    "channel": "email",
    "event_type": "leave.approved",
    "subject": "Leave Request Approved",
    "body": "Your leave from Apr 1-3 has been approved.",
    "status": "sent",
    "created_at": "ISO-8601"
  }
]
```

---

### 2. Get Notification Preferences
Returns the authenticated user's notification channel preferences.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/notifications/preferences/` | Bearer Token | Any Authenticated |

**Response (200 OK)**
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "user_id": "uuid",
  "email_enabled": true,
  "sms_enabled": false,
  "updated_at": "ISO-8601"
}
```

---

### 3. Update Notification Preferences
Updates the authenticated user's notification channel preferences.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PUT` | `/notifications/preferences/` | Bearer Token | Any Authenticated |

**Request Body**
```json
{
  "email_enabled": true,
  "sms_enabled": true
}
```

**Response (200 OK)**: Updated PreferenceResponse object (includes `company_id`)

---

### 4. Health Check

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/health` | None |

**Response (200 OK)**
```json
{
  "status": "healthy",
  "service": "notification-service",
  "version": "1.0.0",
  "checks": {
    "database": "connected",
    "redis": "connected"
  }
}
```

---

## Events Consumed (RabbitMQ)

The notification service subscribes to HRMS events and dispatches notifications based on user preferences. All consumed events are expected to include `company_id` in their payload for tenant-scoped processing.

| Event Type | Notification Sent |
| :--- | :--- |
| `employee.created` | Welcome email to new employee |
| `leave.requested` | Email to manager for approval |
| `leave.approved` | Email to employee |
| `leave.rejected` | Email to employee with reason |
| `attendance.clock_in` | Optional SMS/push notification |
| `payroll.payslip_generated` | Payslip email to employee |

---

## Error Codes

| Status Code | Meaning | Description |
| :--- | :--- | :--- |
| `401` | Unauthorized | Missing or invalid JWT, or token blacklisted |
| `403` | Forbidden | Accessing another user's data |
| `404` | Not Found | Preference not found |
| `422` | Validation Error | Invalid input data |

---

## Database Tables

### notification_logs
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Not null, indexed |
| `user_id` | UUID | Not null, indexed |
| `channel` | String | email, sms |
| `event_type` | String | Not null |
| `subject` | String | Nullable |
| `body` | Text | Not null |
| `status` | String | sent, failed, pending |
| `error_message` | Text | Nullable |
| `created_at` | DateTime | UTC, indexed |

### notification_preferences
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | Not null, indexed |
| `user_id` | UUID | Unique, not null |
| `email_enabled` | Boolean | Default: true |
| `sms_enabled` | Boolean | Default: false |
| `created_at` | DateTime | UTC |
| `updated_at` | DateTime | UTC |
