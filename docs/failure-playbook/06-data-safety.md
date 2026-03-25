# 06 — Data Safety & Consistency

## Active DB Transaction Behavior During Failures

### Normal Request Lifecycle

```python
# Typical request flow in all services:
async def create_employee(data, db: AsyncSession):
    employee = Employee(**data)
    db.add(employee)              # ← Staged in session (not yet in DB)
    await db.commit()             # ← Sent to PostgreSQL, WAL written, committed
    await db.refresh(employee)    # ← Reload from DB (get generated fields)
    return employee               # ← Response sent to client
```

### What Happens at Each Failure Point

| Failure Point | DB State | Client Response | Data Outcome |
|---------------|----------|----------------|--------------|
| Before `db.add()` | No change | 500 error | No data written |
| After `db.add()`, before `db.commit()` | Staged in memory only | 500 error | No data written |
| During `db.commit()` (network drop) | PG received but no ACK | Connection reset | **Data MAY be committed** — race condition |
| After `db.commit()`, before response | Committed to disk (WAL) | Connection reset | **Data committed, client unaware** |
| After response sent | Committed to disk | 200/201 success | Clean success |

### The "Ghost Write" Problem

When `db.commit()` succeeds but the response never reaches the client:
1. Data is permanently written to PostgreSQL
2. Client receives connection reset / timeout
3. Client retries the same request
4. Second write creates a duplicate

**Current System Exposure:**
- No idempotency keys on any endpoint
- Employee creation: duplicate employees possible
- Attendance clock-in: has UniqueConstraint on (employee_id, date) — **protected**
- Leave requests: no dedup — duplicate requests possible
- Payroll runs: has UniqueConstraint on (company_id, period_start, period_end) — **protected**

---

## PostgreSQL Write Durability

### WAL (Write-Ahead Log) Guarantees

PostgreSQL 16 defaults:
```
wal_level = replica        # Full WAL for recovery
synchronous_commit = on    # Data flushed to disk before commit returns
fsync = on                # OS-level file sync on every WAL write
full_page_writes = on     # Prevents torn page corruption
```

**What this means:**
- Every `COMMIT` → data written to WAL on disk → then returns success
- If crash occurs after COMMIT returns: data is recoverable from WAL
- If crash occurs before COMMIT returns: transaction rolled back

### Transaction Isolation Level

SQLAlchemy default: `READ COMMITTED`

```
Session A: INSERT employee "John"
Session B: SELECT employees → does NOT see "John" until A commits
```

No dirty reads, no non-repeatable reads for committed data.

---

## Cache vs Database Consistency

### JWT Token Blacklist (Redis ↔ PostgreSQL)

**Architecture:**
```
Login:    Auth-service → generates JWT → stores refresh_token in DB
Logout:   Auth-service → blacklists JWT in Redis → revokes refresh_token in DB
Validate: Any service → checks Redis blacklist → allows/denies request
```

**Consistency Scenarios:**

| Scenario | Redis State | DB State | Outcome |
|----------|-------------|----------|---------|
| Normal logout | `bl:{jti}` = "1" | refresh_token revoked | Correct: token rejected |
| Redis crash after logout | Key lost | refresh_token revoked | **VULNERABILITY**: token accepted |
| DB crash after logout | `bl:{jti}` = "1" | refresh_token intact | Redis blocks access, but refresh still works after DB recovery |
| Redis eviction (LRU) | Key evicted | refresh_token revoked | **VULNERABILITY**: token accepted until natural expiry |

**Gap:** Redis is the primary enforcement mechanism, but it's volatile (LRU eviction, 100MB limit). The DB revocation is a backup but not checked during normal token validation.

### Event Publishing (Application ↔ RabbitMQ)

**Architecture:**
```
Service performs write → commits to DB → publishes event to RabbitMQ
```

**Consistency Scenarios:**

| Scenario | DB State | RabbitMQ State | Outcome |
|----------|----------|---------------|---------|
| Normal flow | Committed | Event published | Correct |
| Crash between commit and publish | Data in DB | No event | **INCONSISTENCY**: Audit/notification miss this event |
| RabbitMQ down during publish | Data in DB | Publish fails (3 retries) | **INCONSISTENCY**: Same as above, logged as error |
| Publish succeeds, consumer crashes | Data in DB | Event in queue | OK: event redelivered on consumer restart |

**This is the "dual write" problem.** The system lacks:
- Outbox pattern (write event to DB, then relay to RabbitMQ)
- Transactional outbox (event and data in same DB transaction)
- Change Data Capture (CDC) from DB WAL to event stream

---

## Data Loss Risk Assessment

### Risk 1: RabbitMQ tmpfs — Event Loss

**Probability:** HIGH (any RabbitMQ restart)
**Impact:** Audit trail gaps, missed notifications
**Data lost:** All events in queues at time of restart
**Permanent:** Yes — events cannot be reconstructed

### Risk 2: Redis Eviction — Blacklist Gaps

**Probability:** MEDIUM (depends on traffic volume)
**Impact:** Revoked tokens temporarily re-accepted
**Data lost:** Blacklist entries for evicted tokens
**Duration:** Until token naturally expires (15min access, 7 days refresh)

### Risk 3: Crash Between Commit and Response

**Probability:** LOW (narrow time window)
**Impact:** Duplicate data if client retries
**Affected:** Employee creation, leave requests (no dedup)
**Protected:** Attendance (unique per day), payroll runs (unique per period)

### Risk 4: No Automated Backups

**Probability:** N/A (when disaster strikes, backup either exists or doesn't)
**Impact:** CATASTROPHIC — total data loss if disk fails
**Data lost:** Everything
**Recovery:** Impossible without backup

### Risk 5: Bulk Import — No Transaction Wrapper

**Current implementation** (employee bulk import):
```python
# Each row committed independently — no all-or-nothing
for row in import_data:
    try:
        employee = Employee(**row)
        db.add(employee)
        await db.commit()       # ← Individual commit per row
        results.append({"status": "success"})
    except IntegrityError:
        await db.rollback()
        results.append({"status": "error"})
```

**Risk:** If system crashes mid-import (row 50 of 100):
- Rows 1-50: committed (permanent)
- Rows 51-100: never processed
- No way to know where import stopped without checking results
- Re-running import: duplicates for rows 1-50 (no dedup)

---

## Partial Write Scenarios

### Scenario: Multi-Table Write (Payroll Run)

```python
# Payroll processing involves:
1. Create payroll_run record
2. For each employee:
   a. Calculate salary
   b. Create payslip record
3. Update payroll_run status to COMPLETED
```

**If crash occurs at step 2c (mid-employee-loop):**
- payroll_run: EXISTS (status = PROCESSING)
- payslips for employees 1-N: EXIST
- payslips for employees N+1-end: DON'T EXIST
- payroll_run status: still PROCESSING (never updated to COMPLETED)

**Recovery:** Must detect incomplete payroll runs and re-process missing employees. The `UniqueConstraint(payroll_run_id, employee_id)` on payslips prevents duplicate payslips on re-run.

### Scenario: Leave Request Approval Chain

```python
# Leave approval involves:
1. Create leave_approval record (level: PROJECT_IN_CHARGE)
2. Update leave_request status
3. Publish leave.approved event
```

**If crash between step 1 and 2:**
- Approval record exists but request status not updated
- Frontend shows outdated status
- Manual fix required: update leave_request.status to match approval chain

---

## Data Consistency Recommendations

| Issue | Current State | Recommended Fix | Priority |
|-------|--------------|-----------------|----------|
| RabbitMQ event loss | tmpfs (volatile) | Persistent volume | CRITICAL |
| No idempotency keys | Duplicate writes possible | Add idempotency_key header + table | HIGH |
| Dual write problem | DB commit + MQ publish separate | Outbox pattern or CDC | HIGH |
| Redis blacklist eviction | LRU evicts security data | Separate Redis instance for blacklist, noeviction policy | HIGH |
| Bulk import no transaction | Partial import on crash | Add batch transaction or idempotent import | MEDIUM |
| Multi-step operations | Partial state on crash | Saga pattern or status-based recovery | MEDIUM |
| No backup strategy | Total loss on disk failure | Automated pg_dump + WAL archiving | CRITICAL |
