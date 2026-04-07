# Payroll Service API Documentation

**Service:** Payroll Management Service  
**Port:** 8003  
**Base URL:** `http://payroll-service:8003`  
**Authentication:** JWT Bearer Token  
**Database:** `payroll_db` (PostgreSQL)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Payroll Runs](#payroll-runs)
3. [Payslips](#payslips)
4. [Reports & Exports](#reports--exports)
5. [Salary Structures & Tax Profiles](#salary-structures--tax-profiles)
6. [Error Codes](#error-codes)
7. [Integration Guide](#integration-guide)

---

## Authentication

All endpoints require JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer {jwt_token}
```

**Token Claims Required:**
- `sub`: User ID
- `email`: User email
- `role`: One of `admin`, `hr_manager`, `hr`, `super_admin`
- `company_id`: Company UUID
- `exp`: Token expiration timestamp

---

## Payroll Runs

### Create Payroll Run

**Endpoint:** `POST /api/v1/payroll/runs`

**Authentication:** Required (roles: `admin`, `hr_manager`)

**Request Body:**
```json
{
  "period_start": "2025-04-01",
  "period_end": "2025-04-30",
  "run_type": "REGULAR",
  "idempotency_key": "uuid-v4"
}
```

**Query Parameters:**
- `idempotency_key` (optional): Unique key for idempotent requests. TTL: 24 hours. Returns cached response if duplicate.

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "id": "run-uuid",
    "company_id": "company-uuid",
    "period_start": "2025-04-01",
    "period_end": "2025-04-30",
    "status": "DRAFT",
    "run_type": "REGULAR",
    "total_employees": 0,
    "total_gross": 0,
    "total_deductions": 0,
    "total_net": 0,
    "created_by": "user-uuid",
    "created_at": "2025-04-07T10:00:00Z"
  },
  "error": null
}
```

**Error Responses:**

| Status | Code | Message | Cause |
|--------|------|---------|-------|
| 400 | `INVALID_PERIOD` | Period end must be after period start | period_start >= period_end |
| 409 | `DUPLICATE_RUN` | Payroll run already exists for this period | uq_payroll_run_company_period violation |
| 409 | `DUPLICATE_REQUEST` | Idempotency key already processed | Concurrent duplicate request |
| 422 | `VALIDATION_FAILED` | Period overlaps with existing run | Check for overlapping runs |

---

### List Payroll Runs

**Endpoint:** `GET /api/v1/payroll/runs`

**Authentication:** Required

**Query Parameters:**
```
?page=1&limit=20&status=DRAFT&run_type=REGULAR&sort_by=created_at&order=desc
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": "run-uuid",
      "company_id": "company-uuid",
      "period_start": "2025-04-01",
      "period_end": "2025-04-30",
      "status": "DRAFT",
      "run_type": "REGULAR",
      "total_employees": 150,
      "total_gross": 15000000,
      "total_deductions": 2500000,
      "total_net": 12500000,
      "created_at": "2025-04-07T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  },
  "error": null
}
```

---

### Get Payroll Run Details

**Endpoint:** `GET /api/v1/payroll/runs/{run_id}`

**Authentication:** Required

**Path Parameters:**
- `run_id`: UUID of payroll run

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "run-uuid",
    "company_id": "company-uuid",
    "period_start": "2025-04-01",
    "period_end": "2025-04-30",
    "status": "REVIEW",
    "run_type": "REGULAR",
    "total_employees": 150,
    "total_gross": 15000000,
    "total_deductions": 2500000,
    "total_net": 12500000,
    "approved_by": "approver-uuid",
    "approved_at": "2025-04-07T12:00:00Z",
    "locked_at": null,
    "idempotency_key": "idempotency-uuid",
    "exception_report": {
      "errors": [],
      "warnings": [
        "Employee EMP-001 has no active salary structure"
      ],
      "occurred_at": "2025-04-07T11:00:00Z"
    },
    "created_by": "creator-uuid",
    "created_at": "2025-04-07T10:00:00Z"
  },
  "error": null
}
```

---

### Compute Payroll (Draft → Review)

**Endpoint:** `POST /api/v1/payroll/runs/{run_id}/compute`

**Authentication:** Required (roles: `admin`, `hr_manager`)

**Description:** 
- Validates salary structures and employee data
- Calculates gross, deductions (PF, ESI, TDS, PT, LWF)
- Generates draft payslips (not committed to DB)
- Runs validation checks and creates exception report
- **Does NOT update YTD** (preview only)
- Transitions: DRAFT → REVIEW

**Request Body:**
```json
{
  "include_lop": true,
  "override_lop": false,
  "lop_override_days": 0
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "run-uuid",
    "status": "REVIEW",
    "total_employees": 150,
    "total_gross": 15000000,
    "total_deductions": 2500000,
    "total_net": 12500000,
    "exception_report": {
      "errors": [
        "Employee EMP-123 has missing salary structure"
      ],
      "warnings": [
        "LOP data unavailable for 5 employees (leave-service unreachable)"
      ],
      "occurred_at": "2025-04-07T11:30:00Z"
    }
  },
  "error": null
}
```

**Error Responses:**

| Status | Code | Message | Action |
|--------|------|---------|--------|
| 409 | `INVALID_STATUS_TRANSITION` | Cannot compute from LOCKED state | Only DRAFT can be computed |
| 409 | `ALREADY_IN_REVIEW` | Run already in REVIEW state | Call approve/reject instead |
| 422 | `VALIDATION_FAILED` | Critical errors found in run | Fix issues in exception_report |
| 423 | `LOCKED_FOR_EDITING` | Payroll run is locked | Cannot modify locked runs |
| 503 | `LEAVE_SERVICE_UNAVAILABLE` | Leave service timeout (5s) | Falls back to lop_days=0 |

---

### Approve Payroll (Review → Approved)

**Endpoint:** `POST /api/v1/payroll/runs/{run_id}/approve`

**Authentication:** Required (roles: `admin`, `hr_manager`)

**Description:**
- Approves payroll after review
- Validates that all critical errors are resolved
- Checks approver permissions
- Acquires Redis lock (120s TTL) + PostgreSQL advisory lock
- Transitions: REVIEW → APPROVED

**Request Body:**
```json
{
  "approval_notes": "All validations passed. Ready for processing."
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "run-uuid",
    "status": "APPROVED",
    "approved_by": "approver-uuid",
    "approved_at": "2025-04-07T12:00:00Z"
  },
  "error": null
}
```

**Error Responses:**

| Status | Code | Message | Recovery |
|--------|------|---------|----------|
| 409 | `CONCURRENCY_LOCK_FAILED` | Payroll locked by another request | Retry after 5 seconds |
| 409 | `INVALID_STATUS_TRANSITION` | Cannot approve non-REVIEW run | Only REVIEW runs can be approved |
| 422 | `VALIDATION_FAILED` | Critical errors unresolved | Run /compute again; fix errors |
| 403 | `INSUFFICIENT_PERMISSION` | User lacks approval permission | Contact admin to grant role |

---

### Reject Payroll (Review → Draft)

**Endpoint:** `POST /api/v1/payroll/runs/{run_id}/reject`

**Authentication:** Required (roles: `admin`, `hr_manager`)

**Description:**
- Rejects payroll and returns to DRAFT for revisions
- Stores rejection reason in audit log
- Transitions: REVIEW → DRAFT

**Request Body:**
```json
{
  "reason": "Salary discrepancies detected. Please recalculate."
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "run-uuid",
    "status": "DRAFT",
    "rejection_reason": "Salary discrepancies detected. Please recalculate."
  },
  "error": null
}
```

---

### Process Payroll (Approved → Completed)

**Endpoint:** `POST /api/v1/payroll/runs/{run_id}/process`

**Authentication:** Required (roles: `admin`, `hr_manager`)

**Description:**
- **CRITICAL:** Finalizes payslips and updates YTD records
- Generates payslips snapshot (JSON) for audit
- Locks payslips (prevents further edits)
- Updates YTD tables (cumulative payroll data)
- Publishes `payroll.payslips_ready` event (async PDF generation)
- If any step fails → rolls back transaction, sets FAILED state
- Transitions: APPROVED → PROCESSING → COMPLETED (or FAILED)
- **Cannot be reversed** — use FNF for corrections

**Request Body:**
```json
{
  "batch_id": "batch-uuid",
  "idempotency_key": "unique-key"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "run-uuid",
    "status": "COMPLETED",
    "locked_at": "2025-04-07T13:00:00Z",
    "payslips_generated": 150,
    "event_published": true
  },
  "error": null
}
```

**Error Responses:**

| Status | Code | Message | Recovery |
|--------|------|---------|----------|
| 409 | `INVALID_STATUS_TRANSITION` | Cannot process non-APPROVED run | Call approve endpoint first |
| 400 | `NEGATIVE_NET_PAY` | Employee has negative net pay | Adjust deductions or salary |
| 500 | `YTD_UPDATE_FAILED` | Failed to update YTD records | Manual YTD correction required |
| 500 | `TRANSACTION_ROLLBACK` | Process failed, all changes rolled back | Run is set to FAILED state |
| 503 | `PDF_GENERATION_QUEUED` | Payslips queued for async PDF generation | PDFs available after 5-10 min |

---

### Mark Payroll as Paid (Completed → Paid)

**Endpoint:** `POST /api/v1/payroll/runs/{run_id}/mark-paid`

**Authentication:** Required (roles: `admin`, `hr_manager`)

**Description:**
- Marks payroll as paid after fund transfer
- Updates payment timestamp
- Transitions: COMPLETED → PAID

**Request Body:**
```json
{
  "payment_reference": "NEFT-2025-04-07-001",
  "payment_method": "NEFT",
  "bank_description": "Monthly Salary - April 2025"
}
```

**Response:** `200 OK`

---

### Lock Payroll (Paid → Locked)

**Endpoint:** `POST /api/v1/payroll/runs/{run_id}/lock`

**Authentication:** Required (roles: `admin`)

**Description:**
- **FINAL:** Locks payroll from further modifications
- Payslips cannot be updated or deleted after lock
- Database trigger prevents any UPDATE/DELETE operations
- Transitions: PAID → LOCKED
- **Irreversible** — only HR can unlock with approval

**Request Body:**
```json
{
  "lock_reason": "Monthly payroll finalized for statutory filing"
}
```

**Response:** `200 OK`

**Note:** After locking, attempting to update payslips returns:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "PAYSLIP_LOCKED",
    "message": "Payslip is locked and cannot be modified"
  }
}
```

---

### Retry Payroll (Failed → Draft)

**Endpoint:** `POST /api/v1/payroll/runs/{run_id}/retry`

**Authentication:** Required (roles: `admin`)

**Description:**
- Resets failed payroll back to DRAFT for recalculation
- Clears error_message and exception_report
- Transitions: FAILED → DRAFT

**Request Body:**
```json
{
  "reason": "TDS calculation corrected in backend"
}
```

**Response:** `200 OK`

---

## Payslips

### Get Payslips for Run

**Endpoint:** `GET /api/v1/payroll/runs/{run_id}/payslips`

**Authentication:** Required

**Query Parameters:**
```
?page=1&limit=50&employee_id=emp-uuid&filter=net_salary_range
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": "payslip-uuid",
      "payroll_run_id": "run-uuid",
      "employee_id": "emp-uuid",
      "ctc": 1200000,
      "basic": 500000,
      "hra": 200000,
      "allowances": 150000,
      "gross": 850000,
      "pf_deduction": 60000,
      "esi_deduction": 6375,
      "professional_tax": 200,
      "tds_deduction": 15000,
      "lwf_employee": 0,
      "other_deductions": 0,
      "total_deductions": 81575,
      "net": 768425,
      "period_start": "2025-04-01",
      "period_end": "2025-04-30",
      "lop_days": 2,
      "lop_amount": 56667,
      "pro_rata_factor": 1.0,
      "tax_regime": "new",
      "employer_pf": 139500,
      "employer_esi": 27675,
      "locked_at": "2025-04-07T13:00:00Z",
      "snapshot": {
        "version": 1,
        "generated_at": "2025-04-07T13:00:00Z",
        "salary": {...},
        "components": {...},
        "deductions": {...},
        "employer": {...},
        "ytd_at_run": {...},
        "tax": {...}
      }
    }
  ],
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 150
  },
  "error": null
}
```

---

### Get Single Payslip

**Endpoint:** `GET /api/v1/payroll/runs/{run_id}/payslips/{payslip_id}`

**Authentication:** Required

**Response:** `200 OK` (same as above)

---

### Download Payslip PDF

**Endpoint:** `GET /api/v1/payroll/runs/{run_id}/payslips/{payslip_id}/pdf`

**Authentication:** Required

**Response:** `200 OK` (Content-Type: application/pdf)

**Note:** PDF is generated asynchronously after /process completes. Check `pdf_data` field in payslip to see if ready.

---

## Reports & Exports

### Download ECR File (EPFO)

**Endpoint:** `GET /api/v1/payroll/runs/{run_id}/ecr-file`

**Authentication:** Required

**Response:** `200 OK` (Content-Type: text/plain)

**Format:** 11-field pipe-separated values (`#~#` delimiter)

```
UAN#~#Name#~#Gross Wages#~#EPF Wages#~#EPS Wages#~#EDLI Wages#~#EPF Contri#~#EPS Contri#~#EPF-EPS Diff#~#NCP Days#~#Refund of Advances
0AB1234567890#~#John Doe#~#850000#~#500000#~#500000#~#850000#~#60000#~#41667#~#18333#~#2#~#0
```

---

### Download Bank Advice (CSV)

**Endpoint:** `GET /api/v1/payroll/runs/{run_id}/bank-advice`

**Authentication:** Required

**Response:** `200 OK` (Content-Type: text/csv)

**Columns:**
```
Employee ID, Name, Bank Name, IFSC Code, Account Number, Account Type, Net Pay
EMP-001, John Doe, HDFC Bank, HDFC0001234, 1234567890123, Savings, 768425
```

---

### Get ESIC Return Data

**Endpoint:** `GET /api/v1/payroll/runs/{run_id}/esic-return`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "month": 4,
    "year": 2025,
    "total_employees": 150,
    "total_wages": 12750000,
    "employee_contribution": 95625,
    "employer_contribution": 414375,
    "total_due": 510000,
    "due_date": "2025-05-07",
    "challan_number": "CHN-2025-04-001"
  },
  "error": null
}
```

---

### Download Form 16 (PDF)

**Endpoint:** `GET /api/v1/payroll/employees/{employee_id}/form16?fy={financial_year}`

**Authentication:** Required

**Query Parameters:**
- `fy`: Financial year (e.g., 2026 for FY 2025-26)

**Response:** `200 OK` (Content-Type: application/pdf)

**Includes:**
- Part A: Personal details, PAN, income
- Part B: Deductions breakdown, TDS withheld monthly, annual summary

---

## Salary Structures & Tax Profiles

### Create Salary Structure

**Endpoint:** `POST /api/v1/payroll/salary-structures`

**Authentication:** Required (roles: `admin`)

**Request Body:**
```json
{
  "name": "Senior Engineer",
  "description": "Senior Software Engineer salary structure",
  "basic_pct": 50,
  "hra_pct": 20,
  "allowances_pct": 30,
  "pf_pct": 12,
  "esi_pct": 0.75,
  "professional_tax": 200
}
```

**Response:** `201 Created`

**Important:** Structure is NOT versioned. Editing affects only new payroll runs, not historical data (protected by payslip snapshot).

---

### Get/Update Tax Profile

**Endpoint:** `GET/PATCH /api/v1/payroll/tax-profiles/{employee_id}?fy={financial_year}`

**Authentication:** Required

**PATCH Request Body:**
```json
{
  "tax_regime": "new",
  "investment_80c": 150000,
  "investment_80d": 50000,
  "hra_rent_paid": 240000,
  "is_metro_city": true,
  "nps_voluntary": 50000
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "employee_id": "emp-uuid",
    "financial_year": 2026,
    "tax_regime": "new",
    "investment_80c": 150000,
    "investment_80d": 50000,
    "hra_rent_paid": 240000,
    "is_metro_city": true,
    "nps_voluntary": 50000,
    "declared_at": "2025-04-07T10:00:00Z",
    "updated_at": "2025-04-07T10:00:00Z"
  },
  "error": null
}
```

---

## Error Codes

### HTTP Status Codes

| Status | Usage |
|--------|-------|
| 200 | Success |
| 201 | Resource created |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient role permission) |
| 404 | Resource not found |
| 409 | Conflict (state transition invalid, duplicate, lock contention) |
| 422 | Unprocessable entity (business logic validation failed) |
| 423 | Locked (resource locked for editing) |
| 500 | Internal server error |
| 503 | Service unavailable (dependency timeout) |

### Common Error Codes

| Code | Meaning | Recovery |
|------|---------|----------|
| `INVALID_PERIOD` | period_start >= period_end | Correct date range |
| `DUPLICATE_RUN` | Run exists for this period | Use existing run or adjust dates |
| `DUPLICATE_REQUEST` | Idempotency key already processed | No action needed; request is safe |
| `INVALID_STATUS_TRANSITION` | Cannot transition from current state | Check run status and allowed transitions |
| `VALIDATION_FAILED` | Business logic validation failed | Review exception_report for details |
| `LOCKED_FOR_EDITING` | Resource is locked | Cannot modify; contact admin to unlock |
| `CONCURRENCY_LOCK_FAILED` | Cannot acquire distributed lock | Retry after 5-10 seconds |
| `LEAVE_SERVICE_UNAVAILABLE` | Leave service not responding | Falls back to lop_days=0 with warning |
| `NEGATIVE_NET_PAY` | Net salary is negative | Adjust salary or deductions |
| `YTD_UPDATE_FAILED` | Cannot update YTD records | Manual correction may be needed |

---

## Integration Guide

### Service-to-Service Authentication

Use internal token (set in `INTERNAL_SERVICE_TOKEN` env var) for service-to-service calls:

```
GET /api/v1/internal/lop-summary HTTP/1.1
Host: leave-service:8002
Authorization: Bearer {INTERNAL_SERVICE_TOKEN}
x-internal-token: {INTERNAL_SERVICE_TOKEN}

{
  "employee_id": "emp-uuid",
  "period_start": "2025-04-01",
  "period_end": "2025-04-30"
}
```

---

### Event Publishing

Payroll service publishes events via RabbitMQ (no auth required for internal subscribers):

**Event: `payroll.run.created`**
```json
{
  "event_id": "evt-uuid",
  "event_type": "payroll.run.created",
  "timestamp": "2025-04-07T10:00:00Z",
  "data": {
    "run_id": "run-uuid",
    "company_id": "company-uuid",
    "period_start": "2025-04-01",
    "period_end": "2025-04-30"
  }
}
```

**Event: `payroll.payslips_ready`**
```json
{
  "event_id": "evt-uuid",
  "event_type": "payroll.payslips_ready",
  "timestamp": "2025-04-07T13:00:00Z",
  "data": {
    "run_id": "run-uuid",
    "payslips_generated": 150,
    "pdf_ready": true,
    "download_url": "/api/v1/payroll/runs/{run_id}/payslips/{payslip_id}/pdf"
  }
}
```

---

### Webhook/Callback Integration

For external systems (accounting, HRMS):

```
POST /webhook/payroll-event HTTP/1.1
Host: external-system.com
Content-Type: application/json
X-Webhook-Signature: sha256=...

{
  "event": "payroll.completed",
  "run_id": "run-uuid",
  "company_id": "company-uuid",
  "total_net": 12500000,
  "timestamp": "2025-04-07T13:00:00Z"
}
```

Configure webhook endpoints in admin panel → Payroll → Integrations.

---

## Rate Limiting

All endpoints are rate limited:
- **Authenticated users:** 1000 requests/hour
- **Internal service tokens:** 10000 requests/hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1712496000
```

---

## Changelog

### v1.0.0 (2025-04-07)
- Initial API release
- DRAFT → REVIEW → APPROVED → PROCESSING → COMPLETED → PAID → LOCKED lifecycle
- TDS calculation (new regime only)
- PF, ESI, PT, LWF deductions
- YTD tracking
- Idempotency support (24h cache)
- Distributed locking (Redis + PostgreSQL advisory)
- Event publishing via RabbitMQ
