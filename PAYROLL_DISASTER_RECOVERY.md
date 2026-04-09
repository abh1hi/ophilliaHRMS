# Payroll Service Disaster Recovery & Error Recovery Playbooks

**Version:** 1.0  
**Last Updated:** 2025-04-07  
**Severity Levels:** P0 (Critical), P1 (High), P2 (Medium), P3 (Low)

---

## Table of Contents

1. [Disaster Scenarios](#disaster-scenarios)
2. [Locked Payroll Recovery](#locked-payroll-recovery)
3. [Negative FNF Handling](#negative-fnf-handling)
4. [Data Corruption Recovery](#data-corruption-recovery)
5. [Concurrency Issues](#concurrency-issues)
6. [Third-Party Service Failures](#third-party-service-failures)

---

## Disaster Scenarios

### Overview Matrix

| Scenario | Severity | MTTR | Detection |
|----------|----------|------|-----------|
| Locked payroll needs unlock | P1 | 30 min | Manual request |
| Negative FNF net salary | P0 | 60 min | System validation |
| Database corruption | P0 | 120 min | Automated alert |
| Redis memory full | P1 | 15 min | Monitoring alert |
| RabbitMQ queue stuck | P1 | 30 min | Manual check + alert |
| TDS calculation error | P1 | 45 min | Audit/validation |
| Idempotency cache overflow | P2 | 30 min | Disk usage alert |
| Leave service unavailable | P2 | 5 min | Graceful fallback |

---

## Locked Payroll Recovery

**Scenario:** Payroll was locked in error and needs to be corrected

**Severity:** P1 (High) — affects salary transfers

**Time to Resolve:** 30–60 minutes

### Step 1: Assessment (5 minutes)

```sql
-- Check payroll status
SELECT id, status, period_start, period_end, total_employees, locked_at
FROM payroll_runs
WHERE id = '{{RUN_ID}}'
LIMIT 1;

-- Check if payslips are locked
SELECT COUNT(*) as locked_count
FROM payslips
WHERE payroll_run_id = '{{RUN_ID}}' AND locked_at IS NOT NULL;
```

**Questions to answer:**
- How many employees are affected?
- What was locked incorrectly?
- Can this be fixed without unlocking (e.g., by creating new FNF run)?

### Step 2: Prevent Further Damage

**Immediately:**

1. **Disable auto-lock in code** (if applicable)
   ```python
   # In payroll_service.py, add guard
   if run.period == "2025-04-01 to 2025-04-30":
       raise Exception("Locked run detected. Manual unlock required.")
   ```

2. **Notify affected employees** (via Slack/Email)
   ```
   Subject: Payroll Processing Delay

   Due to a system issue, your April salary may be delayed by 24 hours.
   We're working to resolve this. No action needed from you.
   ```

### Step 3: Unlock Payroll (if truly necessary)

**WARNING:** Unlocking is rare. Consider alternatives first:
- Create FNF run for corrections
- Process supplementary payroll instead

**To unlock** (admin-only, requires 2 approvals):

```python
# Manual unlock script (run by DevOps)
from app.db import get_session
from app.models import PayrollRun

def unlock_payroll(run_id: str, reason: str, approved_by: list[str]):
    """
    Unlock a locked payroll run.
    Requires 2 admin approvals.
    """
    if len(approved_by) < 2:
        raise ValueError("Requires 2 admin approvals")
    
    session = get_session()
    run = session.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    
    if not run:
        raise ValueError(f"Run {run_id} not found")
    
    # Remove locked_at to unlock
    run.locked_at = None
    
    # Remove locks on payslips
    session.execute(
        "UPDATE payslips SET locked_at = NULL WHERE payroll_run_id = %s",
        (run_id,)
    )
    
    # Log unlock event
    session.execute(
        """INSERT INTO payroll_audit_logs 
           (run_id, action, performed_by, before_state, after_state)
           VALUES (%s, 'UNLOCKED', %s, 'LOCKED', 'PAID')""",
        (run_id, approved_by[0])
    )
    
    session.commit()
    print(f"✓ Payroll {run_id} unlocked by {approved_by[0]}")

unlock_payroll(
    run_id='{{RUN_ID}}',
    reason='Incorrect lock, revert to PAID state',
    approved_by=['admin1@ophillia.com', 'admin2@ophillia.com']
)
```

### Step 4: Correct the Data

**Option A: Update specific payslips** (if minor errors)

```sql
-- Update single employee's net pay
UPDATE payslips
SET net = 768425,  -- Corrected amount
    updated_at = NOW()
WHERE payroll_run_id = '{{RUN_ID}}'
  AND employee_id = 'EMP-001';

-- Create audit log entry
INSERT INTO payroll_audit_logs 
  (payroll_run_id, payslip_id, action, performed_by, after_state)
VALUES 
  ('{{RUN_ID}}', '{{PAYSLIP_ID}}', 'CORRECTED', 'admin@ophillia.com', 
   jsonb_build_object('net', 768425, 'reason', 'TDS recalculation'));
```

**Option B: Create corrective FNF run** (if major errors)

```python
# Create a supplementary payroll run
from app.services.payroll_service import create_payroll_run

correction_run = create_payroll_run(
    company_id='company-uuid',
    period_start='2025-04-30',
    period_end='2025-04-30',
    run_type='FNF',  # Use FNF for corrections
    description='Correction run for April 2025 - TDS recalculation'
)

# Add only affected employees
# This run will handle salary adjustments
```

### Step 5: Re-lock Payroll

```sql
-- Re-lock after corrections
UPDATE payroll_runs
SET locked_at = NOW()
WHERE id = '{{RUN_ID}}';

UPDATE payslips
SET locked_at = NOW()
WHERE payroll_run_id = '{{RUN_ID}}' AND locked_at IS NULL;
```

### Step 6: Verification & Notification

```python
# Verify all payslips are locked
from app.db import get_session
from app.models import Payslip

session = get_session()
unlocked_count = session.query(Payslip).filter(
    Payslip.payroll_run_id == '{{RUN_ID}}',
    Payslip.locked_at.isnot(None)  # NOT locked (NULL)
).count()

assert unlocked_count == 0, "Some payslips not locked!"
print("✓ All payslips locked successfully")

# Notify HR
send_notification(
    to='hr@ophillia.com',
    subject='Payroll Correction Complete',
    body=f'Payroll {RUN_ID} corrected and re-locked. {total_employees} employees affected.'
)
```

---

## Negative FNF Handling

**Scenario:** Employee's Full & Final settlement results in negative net (employer owes employee money)

**Severity:** P0 (Critical) — labor law violation risk

**Time to Resolve:** 60–90 minutes

**Root Causes:**
- Outstanding loans > final salary
- Large leave encashment
- Gratuity calculation error
- Deduction miscalculation

### Step 1: Detect Negative FNF

**System should flag automatically:**

```python
# In process_payroll()
for payslip in payslips:
    if payslip.net < 0:
        raise ValueError(
            f"Negative net pay detected for {payslip.employee_id}: ₹{payslip.net}. "
            f"Cannot process FNF. Requires manual intervention."
        )
```

### Step 2: Investigation

```sql
-- Get FNF details
SELECT 
    ps.employee_id,
    ps.gross,
    ps.basic, ps.hra, ps.allowances,
    ps.pf_deduction, ps.esi_deduction, ps.tds_deduction, ps.professional_tax,
    ps.total_deductions,
    ps.net,
    fnf.gratuity,
    fnf.leave_encashment,
    fnf.pro_rata_salary,
    fnf.total_deductions as fnf_deductions,
    fnf.net_payable
FROM fnf_settlements fnf
JOIN payslips ps ON ps.id = fnf.payslip_id
WHERE fnf.net_payable < 0;

-- Check for outstanding loans
SELECT 
    employee_id,
    loan_type,
    outstanding,
    emi_amount
FROM payroll_loans
WHERE status = 'ACTIVE'
  AND employee_id = '{{EMP_ID}}';

-- Check leave encashment
SELECT 
    employee_id,
    earned_leave_days,
    earned_leave_rate,
    earned_leave_days * earned_leave_rate as earned_leave_value
FROM leave_ledger
WHERE employee_id = '{{EMP_ID}}'
  AND status = 'ACTIVE';
```

### Step 3: Determine Handling Method

**Method 1: Adjust deductions (if negative due to over-deduction)**

```python
# Reduce or eliminate problematic deductions
adjustments = {
    'tds_deduction': 0,  # Remove TDS for final month
    'professional_tax': 0,  # Remove PT
    'pf_deduction': min(existing_pf, max_allowed),  # Cap PF
}

recalculated_net = gross - sum(adjustments.values())
```

**Method 2: Split payment (if negative due to gratuity)**

```python
# Pay in two installments
payment_plan = {
    'regular_salary': 500000,  # Monthly salary portion
    'gratuity_advance': 100000,  # Advance on gratuity
    'leave_encashment': 250000,  # Leave payout
    # Remaining gratuity: 400000 (to be paid separately)
}

# Create two payslips instead of one
```

**Method 3: Defer gratuity (if labor law permits)**

```python
# Defer gratuity to next month
payslip.net = monthly_salary - deductions  # Positive
gratuity_defer = {
    'original_amount': 400000,
    'deferral_reason': 'Negative FNF prevention',
    'payment_date': '2025-05-07'
}
```

**Method 4: Loan waiver (HR discretion)**

```sql
-- If employee qualifies for loan waiver
UPDATE payroll_loans
SET status = 'WAIVED',
    waived_at = NOW(),
    waived_by = 'hr_admin@ophillia.com'
WHERE employee_id = '{{EMP_ID}}'
  AND status = 'ACTIVE';

-- Recalculate FNF without loan deduction
recalculated_net = fnf_net + waived_loan_amount
```

### Step 4: Get HR Approval

```python
# Create approval request
approval_req = {
    'employee_id': 'EMP-001',
    'settlement_type': 'FNF',
    'negative_amount': abs(net),  # e.g., ₹50,000
    'proposed_solution': 'Method 1: Reduce TDS',
    'requested_by': 'system@ophillia.com',
    'requires_approval': True,
    'approvers': ['hr_manager@ophillia.com', 'finance_head@ophillia.com']
}

# Send notification
send_approval_notification(approval_req)
```

### Step 5: Process Approved Solution

```python
# After HR approval received
fnf = FNFSettlement.get(employee_id='EMP-001')

# Apply approved method
if approved_method == 'split_payment':
    payslips = split_fnf_into_installments(fnf)
    for ps in payslips:
        assert ps.net >= 0, "Payslip still negative!"
        process_payslip(ps)
```

### Step 6: Document & Monitor

```python
# Create incident record
incident = {
    'employee_id': 'EMP-001',
    'incident_type': 'NEGATIVE_FNF',
    'detection_date': datetime.now(),
    'resolution_method': 'split_payment',
    'approval_chain': ['hr_manager', 'finance_head'],
    'resolution_date': datetime.now(),
    'final_net_payable': 750000,
    'notes': 'Gratuity deferred to May 2025'
}

store_incident_record(incident)

# Monitor for similar cases
similar_cases = query_negative_fnf_cases()
if len(similar_cases) > 2:
    alert('HIGH_INCIDENT_RATE', severity='P1')
```

---

## Data Corruption Recovery

**Scenario:** Database records are corrupted or inconsistent

**Severity:** P0 (Critical)

**Common corruptions:**
- Duplicate payslips
- Mismatched YTD records
- Orphaned payslip records (run deleted)
- Negative gross/net (invalid state)

### Detection

```sql
-- Find duplicate payslips (same run + employee)
SELECT payroll_run_id, employee_id, COUNT(*) as count
FROM payslips
GROUP BY payroll_run_id, employee_id
HAVING COUNT(*) > 1;

-- Find inconsistent YTD (YTD < payslip amounts)
SELECT e.id, e.ytd_gross, SUM(p.gross) as payslip_gross
FROM employee_ytd e
JOIN payslips p ON p.employee_id = e.employee_id
GROUP BY e.id
HAVING e.ytd_gross < SUM(p.gross);

-- Find negative amounts
SELECT * FROM payslips
WHERE gross < 0 OR net < 0 OR total_deductions < 0;

-- Find orphaned payslips
SELECT p.* FROM payslips p
LEFT JOIN payroll_runs r ON r.id = p.payroll_run_id
WHERE r.id IS NULL;
```

### Recovery Steps

1. **STOP all processing immediately**
   ```bash
   kubectl scale deployment payroll-service --replicas=0
   ```

2. **Restore from backup**
   ```bash
   # Use backup from before corruption was introduced
   psql -h payroll-db -U postgres payroll_db < /backups/payroll_2025-04-06_clean.sql
   ```

3. **Run validation script**
   ```bash
   python scripts/validate_and_repair.py --mode=strict
   
   # Output should be:
   # ✓ 0 duplicates found
   # ✓ 0 inconsistencies found
   # ✓ 0 negative amounts found
   # ✓ 0 orphaned records found
   ```

4. **Restart service**
   ```bash
   kubectl scale deployment payroll-service --replicas=3
   ```

---

## Concurrency Issues

**Scenario:** Multiple requests trying to compute/approve same payroll simultaneously

**Severity:** P1 (High)

**Symptoms:**
- "CONCURRENCY_LOCK_FAILED" errors
- Duplicate operations
- Race condition side effects

### Prevention (Best Practice)

**Distributed lock with timeout:**

```python
# In payroll_service.py
from redis import Redis

async def compute_payroll_with_lock(run_id: str):
    lock_key = f"payroll:lock:{run_id}"
    redis = Redis(host='payroll-redis')
    
    # Acquire lock with 120s timeout
    acquired = redis.set(
        lock_key,
        value=str(uuid4()),
        ex=120,  # 120 seconds
        nx=True  # Only if not exists
    )
    
    if not acquired:
        raise HTTPException(
            status_code=409,
            detail="Payroll locked by another operation. Retry in 5s."
        )
    
    try:
        # Compute payroll
        result = await _compute_payroll(run_id)
        return result
    finally:
        redis.delete(lock_key)
```

### Recovery from Lock Contention

**If lock expires and operation is in progress:**

```python
# Check if operation actually completed
def check_operation_status(run_id: str) -> str:
    run = PayrollRun.query.get(run_id)
    return run.status  # DRAFT = not started, REVIEW = completed

# If lock expired but operation didn't finish
def cleanup_stuck_lock(run_id: str, admin_approval: bool):
    if not admin_approval:
        raise ValueError("Requires admin approval")
    
    # Force delete lock
    redis.delete(f"payroll:lock:{run_id}")
    
    # Restart operation
    return compute_payroll(run_id)
```

---

## Third-Party Service Failures

### Leave Service Unavailable

**Graceful Fallback:** Already implemented

```python
# In payroll_service.py
async def fetch_lop_days(employee_id: str, period) -> dict:
    try:
        response = await leave_service.get_lop_summary(
            employee_id=employee_id,
            period_start=period.start,
            period_end=period.end,
            timeout=5  # 5 second timeout
        )
        return {'lop_days': response.lop_days, 'status': 'OK'}
    except TimeoutError:
        # Fall back to 0 LOP with warning
        return {'lop_days': 0, 'status': 'UNAVAILABLE'}
    except Exception as e:
        # Log and fall back
        logger.warning(f"Leave service error: {e}")
        return {'lop_days': 0, 'status': 'ERROR'}

# In exception report
if lop_status != 'OK':
    exception_report['warnings'].append(
        f"LOP data unavailable for {affected_employees} employees. "
        f"Using 0 days. HR can override before approval."
    )
```

**No action needed** — system designed to handle this gracefully.

### Employee Service Unavailable

**Payroll requires valid employee data.** If employee-service is down:

1. **Block new payroll runs**
   ```python
   async def create_payroll_run(...):
       # Verify employee service is available
       health = await employee_service.health()
       if not health:
           raise ServiceUnavailableError("Employee service not responding")
   ```

2. **Notify admins**
   ```
   ALERT: Employee service unavailable. Cannot create new payroll runs.
   Affected: New run creation
   Workaround: None. Requires external service recovery.
   ```

3. **Continue with existing runs** (compute/process already-created runs)

### Database Connection Loss

**With connection pooling and retries:**

```python
# SQLAlchemy handles connection pooling automatically
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,  # Recycle connections every hour
    echo_pool=True
)

# Automatic retry with exponential backoff
@retry(max_attempts=3, backoff=ExponentialBackoff())
async def query_payroll_runs():
    return await session.query(PayrollRun).all()
```

**If database is down:**

1. **All operations fail with 503**
2. **Automatic failover** (if replicas configured)
3. **Manual recovery:**
   ```bash
   # Check database status
   kubectl get pod payroll-db
   kubectl logs payroll-db
   
   # Restart database
   kubectl delete pod payroll-db
   # (StatefulSet will restart)
   
   # Wait for recovery
   kubectl wait --for=condition=ready pod -l app=payroll-db
   ```

---

## Escalation Matrix

| Issue | L1 (5 min) | L2 (15 min) | L3 (30 min) |
|-------|-----------|-----------|-----------|
| API down | Check pod status | Restart deployment | Rollback version |
| Database down | Check connections | Restart database | Restore from backup |
| High error rate | Check logs | Review code | Rollback + investigate |
| Data corruption | Stop processing | Restore backup | Manual audit + fix |
| Lock timeout | Retry operation | Force unlock (2 approvals) | Manual investigation |

---

## Incident Response Checklist

When disaster strikes:

- [ ] Identify severity (P0/P1/P2/P3)
- [ ] Declare incident in Slack #incidents channel
- [ ] Notify on-call engineer and manager
- [ ] Document start time and affected systems
- [ ] Execute appropriate playbook from above
- [ ] Monitor recovery metrics
- [ ] Test critical workflows post-recovery
- [ ] Notify stakeholders of resolution
- [ ] Schedule post-mortem within 48 hours
- [ ] Update playbooks with lessons learned
