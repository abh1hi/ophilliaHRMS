# Gaps in Existing Services

This document identifies missing features, APIs, validations, and production gaps within each currently implemented service.

---

## 1. Auth Service — Gaps

### Missing Features
| Gap | Severity | Impact |
|-----|----------|--------|
| No 2FA/MFA (TOTP, SMS) | HIGH | Enterprise clients require MFA for compliance |
| No OAuth/OIDC social login | MEDIUM | No Google/Microsoft SSO support |
| No SAML support | MEDIUM | Enterprise identity federation not possible |
| Email delivery is a stub | HIGH | Magic links and password resets don't actually send emails |
| No login attempt tracking | HIGH | No account lockout after N failures; brute-force risk |
| No device/session management | MEDIUM | Can't view or revoke individual device sessions |
| No token introspection endpoint | LOW | Other services can't verify token status via API |
| Rate limiting is in-memory only | MEDIUM | Resets on restart; not distributed across instances |

### Missing APIs
- `GET /api/v1/auth/sessions` — List active sessions per user
- `DELETE /api/v1/auth/sessions/{id}` — Revoke specific session
- `POST /api/v1/auth/2fa/enable` — Enable TOTP
- `POST /api/v1/auth/2fa/verify` — Verify TOTP code
- `POST /api/v1/auth/introspect` — Token validity check for services
- `GET /api/v1/auth/users` — List users in company (for admin panel)

### Missing Validations
- No password history check (can reuse old passwords)
- No password expiry enforcement
- No email verification on registration
- No user status lifecycle (only is_active boolean; no suspended/pending states)

### Production Gaps
- Email service returns success without sending
- No audit event publishing (authentication events not sent to audit service)
- No Prometheus metrics endpoint
- Service-to-service token is a shared static string (not per-service)

---

## 2. Employee Service — Gaps

### Missing Features
| Gap | Severity | Impact |
|-----|----------|--------|
| No audit trail / change history | HIGH | Can't track who changed what fields |
| No file upload handling | MEDIUM | `staff_photo_url` is just a string, no S3 integration |
| No department hierarchy | MEDIUM | Flat department list; no parent-child org structure |
| No employment status transition validation | MEDIUM | Can go from terminated → active without checks |
| No manager → team relationship | MEDIUM | Managers can't filter by their own team |
| No optimistic locking | MEDIUM | Race conditions on concurrent updates |
| No CSV/Excel export | LOW | No report generation capability |
| No caching layer | LOW | Every request hits database |

### Missing APIs
- `GET /employees/export` — CSV/Excel export
- `GET /employees/{id}/history` — Change audit trail
- `POST /employees/{id}/documents` — Upload documents
- `GET /departments/tree` — Department hierarchy
- `POST /employees/bulk-deactivate` — Bulk termination
- `GET /employees/reports/headcount` — Headcount by department/status

### Missing Validations
- Department `manager_id` not validated (could be non-existent UUID)
- No validation that `department_id` exists before assigning to employee
- Bulk import has no size limit (DoS risk with 100K+ records)
- Department name uniqueness enforced only in app logic, not DB constraint

### Production Gaps
- Soft-delete inconsistency: departments use `is_active`, employees use `employment_status`
- Department deletion doesn't cascade behavior to employees
- No pagination metadata (`has_next`, `total_pages`)
- Swagger UI disabled in production with no alternative docs

---

## 3. Attendance Service — Gaps

### Missing Features
| Gap | Severity | Impact |
|-----|----------|--------|
| No shift management | HIGH | No rotating shifts, night shifts, or multiple shifts/day |
| No grace periods | MEDIUM | Any clock-in after start time is marked "late" |
| No overtime caps or rate multipliers | MEDIUM | No 1.5x/2x overtime rules, no weekly/monthly caps |
| No leave integration | HIGH | Leave days not reflected in attendance |
| No biometric integration | MEDIUM | Only GPS geofence; no fingerprint/face recognition |
| No correction approval workflow | MEDIUM | HR can directly edit records without approval chain |
| No attendance dispute mechanism | LOW | Employees can't appeal incorrect records |
| No offline mode | LOW | Requires connectivity for clock-in |

### Missing APIs
- `GET /attendance/reports/monthly-summary` — Monthly aggregation per employee
- `GET /attendance/reports/export` — Excel/PDF export
- `POST /attendance/corrections/{id}/request` — Employee correction request
- `PUT /attendance/corrections/{id}/approve` — Manager approval for correction
- `GET /attendance/overtime/summary` — Overtime tracking dashboard
- `POST /attendance/shifts` — Shift template CRUD

### Missing Validations
- No idempotency key for clock-in (double-tap risk on slow networks)
- Clock-in/out have no IP-based validation option
- No validation for impossible work hours (e.g., 25+ hours in a day)

### Production Gaps
- No reverse-geocoding for GPS coordinates (stores lat/lng but no address)
- Policy cache missing (hits DB on every clock-in for policy lookup)
- No GDPR data retention/deletion for GPS data

---

## 4. Leave Service — Gaps

### Missing Features
| Gap | Severity | Impact |
|-----|----------|--------|
| Department leave limit not enforced | HIGH | `_check_department_leave_limit()` is a mock function |
| Manager/approver auto-assignment missing | HIGH | Placeholder logic; doesn't fetch real manager |
| No leave carryover | MEDIUM | Unused leave doesn't carry to next year |
| No leave encashment | MEDIUM | No monetary settlement for unused leave |
| No compensatory leave | MEDIUM | No comp-off for working on holidays |
| No Leave Without Pay (LWP) | MEDIUM | Not modeled as a leave type |
| No maternity/paternity special handling | LOW | Treated as regular leave types |
| No leave lockdown/blackout periods | LOW | Can't block leave during critical periods |
| No employee self-cancellation | MEDIUM | Only HR can cancel approved leave |
| No accrual automation | HIGH | `scripts/accrual_cron.py` not implemented |

### Missing APIs
- `POST /leave-requests/{id}/cancel` — Employee self-cancellation
- `GET /leave-balances/summary` — Company-wide leave balance summary
- `POST /leave-types/{id}/carryover` — Year-end carryover processing
- `GET /leave-calendar/export` — Calendar export (iCal/PDF)
- `POST /leave-balances/accrual` — Monthly/quarterly accrual trigger

### Missing Validations
- No retroactive leave application restriction (past dates allowed/blocked inconsistently)
- Holiday date uniqueness not enforced per-tenant at DB level
- Leave type `days_allowed` not validated against balance allocation
- PATCH balance endpoint allows arbitrary updates without business rules

### Production Gaps
- Holiday cache is in-memory dict (no distributed invalidation for multi-instance)
- Migration 0002 is a no-op (company_id already in 0001)
- Approval chain can get stuck if approver is incorrectly assigned

---

## 5. Payroll Service — Gaps

### Missing Features
| Gap | Severity | Impact |
|-----|----------|--------|
| No Income Tax calculation | CRITICAL | No IT slab computation or TDS |
| No statutory compliance reports | CRITICAL | No Form 16, 26AS, PF returns |
| No approval workflow for payroll runs | HIGH | Any HR can execute payroll without approval |
| No leave deduction (LOP) | HIGH | Leave without pay not reflected in salary |
| No attendance-based pro-rata | HIGH | Mid-month joins/exits not calculated |
| No loan/advance EMI deduction | MEDIUM | No employee loan tracking |
| No reimbursement framework | MEDIUM | No flexible allowance/deduction additions |
| No PDF payslip generation | MEDIUM | No printable/downloadable payslips |
| No payslip email distribution | MEDIUM | No automatic payslip delivery |
| No reversal/correction runs | MEDIUM | Can't fix past payroll errors |
| No GL/accounting integration | LOW | No journal entries to accounting system |
| No multi-currency support | LOW | India-only currently |

### Missing APIs
- `POST /api/v1/payroll/runs/{id}/approve` — Multi-level approval
- `POST /api/v1/payroll/runs/{id}/reverse` — Reversal run
- `GET /api/v1/payroll/reports/salary-register` — Salary register report
- `GET /api/v1/payroll/reports/ctc-summary` — CTC analysis
- `GET /api/v1/payslips/{id}/pdf` — PDF generation
- `POST /api/v1/salary/bulk-update` — Bulk salary revision
- `GET /api/v1/payroll/compliance/form16` — Form 16 generation

### Missing Validations
- No CTC validation against industry/role benchmarks
- No salary raise percentage limits
- No duplicate salary overlap check (same date ranges)
- Tax rules are hardcoded (should be configurable per state/year)

### Production Gaps
- Employee validation is fail-open (allows payroll even if employee service is down)
- No caching of salary structures
- Rate limiting not active on endpoints (configured but not applied)
- Unit tests cover only calculator; no integration or E2E tests

---

## 6. Notification Service — Gaps

### Missing Features
| Gap | Severity | Impact |
|-----|----------|--------|
| SMS not implemented | MEDIUM | Only logged, not sent |
| Push notifications not implemented | MEDIUM | Only logged, not sent |
| No user email resolution | HIGH | Uses placeholder `user-{id}@ophillia.com` |
| No notification read/archive endpoint | LOW | No way to mark as read |
| No bulk notification sending | LOW | No announcement-type notifications |
| No template management API | LOW | Templates are hardcoded files |

### Missing APIs
- `POST /notifications/send` — Direct notification trigger
- `PATCH /notifications/logs/{id}/read` — Mark as read
- `GET /notifications/unread-count` — Badge count
- `POST /notifications/bulk` — Bulk/announcement send

### Production Gaps
- SMTP credentials are placeholders in config
- No email address lookup from employee/auth service
- No webhook delivery option
- No notification scheduling (send-later)

---

## 7. Audit Service — Gaps

### Missing Features
| Gap | Severity | Impact |
|-----|----------|--------|
| No event replay capability | LOW | Can't reprocess events |
| No full-text search on payloads | MEDIUM | Can only filter by top-level fields |
| No archival strategy | MEDIUM | Old logs deleted, not archived to cold storage |
| No real-time alerting on critical events | MEDIUM | No webhook/PagerDuty integration |
| No Elasticsearch integration | LOW | Queries limited to PostgreSQL |

### Production Gaps
- CSV export uses mock objects instead of ORM models (bug)
- Retention policy only runs at startup (not scheduled)
- No archival to S3/cold storage before deletion

---

## 8. Students Service — Gaps

### Missing Features
| Gap | Severity | Impact |
|-----|----------|--------|
| No class capacity enforcement | MEDIUM | Can assign unlimited students to a class |
| No academic records/grades | HIGH | No transcript or grade tracking |
| No attendance tracking integration | MEDIUM | Student attendance not linked |
| No academic calendar/term management | MEDIUM | No term/semester structure |
| No bulk student import | MEDIUM | No CSV upload |
| No parent portal endpoints | LOW | No guardian-facing APIs |
| No document attachments | LOW | No file upload for student records |

### Missing APIs
- `POST /students/bulk-import` — CSV import
- `GET /students/search` — Name/email search
- `GET /classes/{id}/students` — Students in class
- `GET /students/{id}/academic-record` — Grades/transcripts
- `GET /guardians/` — List all guardians (currently only by student)

### Production Gaps
- `student.enrolled` event publishes to `students_events` exchange (different from `hrms_events`)
- No `company_id` in guardian model (relies on student's company_id via JOIN)
- `transferred` status mentioned in contract but not in code enum
