# Audit Service Contract (v3)

The Audit Service consumes all HRMS events from RabbitMQ and stores an immutable audit trail. It exposes query and export endpoints for compliance and investigation.

## Base URL
- **Internal (Docker)**: `http://audit-service:8006/api/v1`
- **Gateway**: `/api/v1/audit/*`

---

## Authentication
- JWT Bearer Token (shared public key with auth-service)
- See [SERVICE_AUTH_INTEGRATION_GUIDE.md](../SERVICE_AUTH_INTEGRATION_GUIDE.md)

---

## Multi-Tenancy

All audit log data is isolated by `company_id` (tenant isolation).

- The `company_id` is extracted from the authenticated user's JWT claims.
- Every query endpoint automatically scopes results to the caller's `company_id`.
- Super Admins with platform-level access may optionally filter by `company_id` to view logs across tenants.
- All ingested events are indexed by `company_id` for efficient per-tenant querying and compliance reporting.
- Audit logs belonging to one company are never visible to users of another company.

---

## Endpoints

### 1. List Audit Logs
Returns paginated, filterable audit log entries.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/audit/logs` | Bearer Token | HR, Super Admin |

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `event_type` | string | — | Filter by event type (e.g. `employee.created`) |
| `service_source` | string | — | Filter by originating service |
| `user_id` | UUID | — | Filter by acting user |
| `company_id` | UUID | — | Filter by company (Super Admin only; others auto-scoped) |
| `correlation_id` | string | — | Filter by request correlation ID |
| `date_from` | ISO-8601 | — | Start date filter |
| `date_to` | ISO-8601 | — | End date filter |
| `skip` | int | 0 | Records to skip |
| `limit` | int | 50 | Max records (max 500) |

**Response (200 OK)**
```json
{
  "items": [
    {
      "id": "uuid",
      "event_type": "employee.created",
      "service_source": "employee-service",
      "user_id": "uuid",
      "company_id": "uuid",
      "correlation_id": "uuid",
      "payload": { "...": "..." },
      "created_at": "ISO-8601"
    }
  ],
  "total": 1250,
  "skip": 0,
  "limit": 50
}
```

---

### 2. Get Audit Log Entry

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/audit/logs/{log_id}` | Bearer Token | HR, Super Admin |

**Response (200 OK)**: Single AuditLogResponse object (includes `company_id`)

---

### 3. Export Audit Logs as CSV
Downloads audit logs as a CSV file for compliance reporting.

| Method | Path | Auth | RBAC Role | Rate Limit |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/audit/logs/export/csv` | Bearer Token | Super Admin | 5/min |

**Query Parameters**
| Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `event_type` | string | — | Filter by event type |
| `service_source` | string | — | Filter by originating service |
| `user_id` | UUID | — | Filter by acting user |
| `company_id` | UUID | — | Filter by company (auto-scoped for non-platform admins) |
| `date_from` | ISO-8601 | — | Start date |
| `date_to` | ISO-8601 | — | End date |
| `limit` | int | 1000 | Max rows (max 10000) |

**Response**: `text/csv` file download

---

### 4. Health Check

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/health` | None |

**Response (200 OK)**
```json
{
  "status": "healthy",
  "service": "audit-service",
  "version": "1.0.0",
  "checks": {
    "database": "connected",
    "rabbitmq": "connected"
  }
}
```

---

## Events Consumed (RabbitMQ)

The audit service subscribes to **all** HRMS events and persists them. It does not publish events.

All consumed event envelopes now include `company_id`. The audit service extracts `company_id` from the event envelope and stores it alongside the audit log entry. This enables per-tenant audit log isolation, querying, and compliance reporting.

| Source Service | Events Consumed |
| :--- | :--- |
| employee-service | `employee.created`, `employee.updated`, `employee.deactivated` |
| attendance-service | `attendance.clock_in`, `attendance.clock_out`, `attendance.manual_entry` |
| leave-service | `leave.requested`, `leave.approved`, `leave.rejected` |
| payroll-service | `payroll.run_completed`, `payroll.payslip_generated` |
| students-service | `student.enrolled`, `student.status_changed` |
| auth-service | Any auth-related events |

---

## Error Codes

| Status Code | Meaning | Description |
| :--- | :--- | :--- |
| `401` | Unauthorized | Missing or invalid JWT |
| `403` | Forbidden | Insufficient role permissions |
| `404` | Not Found | Audit log entry not found |
| `422` | Validation Error | Invalid query parameters |
| `429` | Too Many Requests | CSV export rate limit exceeded |

---

## Database Tables

### audit_logs
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `event_type` | String | Not null, indexed |
| `service_source` | String | Not null, indexed |
| `user_id` | UUID | Nullable, indexed |
| `company_id` | UUID | Nullable, indexed (tenant isolation) |
| `correlation_id` | String | Nullable, indexed |
| `payload` | JSONB | Event data |
| `created_at` | DateTime | UTC, indexed |
