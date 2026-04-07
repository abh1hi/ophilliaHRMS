# Phase 8: Full & Final Settlement (FNF) Guide

## Overview

Phase 8 provides **Full & Final Settlement (FNF)** payroll processing for employee exits. When an employee separates from the company, FNF computes:

1. **Pro-rated Final Salary** — Final month salary pro-rated to last working day
2. **Gratuity** — ₹20L private sector exemption (Section 10(10)(ii)), eligibility ≥ 5 years service
3. **Leave Encashment** — Earned leave balance × (basic/26), ₹25L exemption on exit (Section 10(10)(AA))
4. **Final Tax Calculation** — Pro-rata tax for partial financial year with balance TDS adjustment
5. **Loan Recovery** — Outstanding loan EMIs recovered from FNF (flagged if net < 0)
6. **Form 16 (Partial Year)** — Tax documentation for employee's exit year

---

## Architecture

### Event Flow

```
Employee Exit Triggered (last_working_day set)
         ↓
POST /fnf/compute
         ├─ Calculate pro-rata final salary
         ├─ Compute gratuity (≥ 5 years → eligible)
         ├─ Compute leave encashment (earned days × basic/26)
         ├─ Calculate final year tax (pro-rata standard deduction)
         ├─ Deduct final TDS (balance from annual tax – YTD)
         ├─ Recover outstanding loans (min(outstanding, available))
         └─ Returns FNFSummary with all components
         ↓
HR reviews FNFSummary
         ├─ Check if net_fnf_negative (manual intervention needed)
         ├─ Verify gratuity years calculation
         └─ Approve or reject
         ↓
POST /fnf/create-payroll
         ├─ Creates PayrollRun(run_type=FNF, status=COMPLETED, locked=yes)
         ├─ Creates final Payslip (snapshot captures FNF breakdown)
         ├─ Closes all active loans (status=CLOSED)
         ├─ Locks payslip (prevents edit/delete via DB trigger)
         ├─ Publishes fnf.processed event
         └─ Returns confirmation + net FNF payable
         ↓
Notification Service
         ├─ Email FNF statement to employee
         ├─ Email Form 16 (partial year)
         └─ Attach FNF payslip PDF
```

### Database Impact

**payroll_runs:**
- `run_type = "FNF"` (not subject to unique period constraint)
- `status = "COMPLETED"` (FNF runs are processed immediately, no approval workflow)
- `locked_at` set to now (terminal state, no edits)

**payslips:**
- `snapshot` contains FNF breakdown (gratuity, encashment, loan recovery)
- `locked_at` set (DB trigger prevents UPDATE/DELETE)
- `lop_fetch_status = "SKIPPED"` (no LOP in FNF)

**payroll_loans:**
- Active loans transitioned to `status = "CLOSED"`
- `closed_at` set to last_working_day

**payroll_audit_logs:**
- Entry created: `action = "FNF_CREATED"`, captures all FNF components

---

## Components

### 1. FNFService (`fnf_service.py`)

**Class: FNFService**

```python
compute_fnf(employee_id, company_id, last_working_day, joining_date)
  → FNFSummary (Dataclass with all calculations)

_calculate_years_of_service(joining_date, last_working_day)
  → Decimal (years with 2 decimal places)

_months_worked_in_fy(joining_date, last_working_day)
  → int (1-12 months in current FY)

create_fnf_payroll_run(company_id, employee_id, last_working_day, 
                       joining_date, approved_by)
  → (PayrollRun, FNFSummary) (persisted + locked)
```

**Data Classes:**

```
GratuityComponent:
  eligible: bool                    # ≥ 5 years service
  years_of_service: Decimal
  last_basic_da: Decimal
  gratuity_amount: Decimal          # Gross (before exemption)
  exempt_amount: Decimal            # ₹20L (private), ₹10L (public)
  taxable_amount: Decimal           # Gratuity – exempt
  note: str

LeaveEncashmentComponent:
  earned_leave_balance: int         # days
  basic_per_day: Decimal
  encashment_amount: Decimal        # Gross
  exempt_amount: Decimal            # ₹25L on exit
  taxable_amount: Decimal
  note: str

LoanRecoveryComponent:
  loan_id: UUID
  loan_type: str
  principal: Decimal
  outstanding: Decimal
  recovery_amount: Decimal          # min(outstanding, available)
  note: str

FNFSummary:
  (All calculations + metadata, see usage example below)
```

### 2. FNF Calculation Logic

#### Pro-rata Final Salary

```
Period: 1st to last_working_day of exit month
Pro-rata factor = days_worked / calendar_days_in_month

Final salary = (basic + DA + HRA + allowances) × pro_rata_factor
```

#### Gratuity Eligibility & Amount

```
Eligibility: Years of service ≥ 5.0 (continuous)

Gratuity Gross = Last (basic + DA) × (15/26) × years_of_service

Exemption (Section 10(10)(ii)):
  - Private sector: ₹20,00,000 (₹20 lakh)
  - Public sector: ₹10,00,000 (₹10 lakh)

Taxable Gratuity = Max(0, Gratuity Gross – Exemption)
```

**Example:**
```
Employee joined 01-Jan-2019, LWD 31-Mar-2024 (5 years exactly)
Basic: ₹50,000, DA: ₹10,000, Last basic+DA = ₹60,000

Gratuity = ₹60,000 × (15/26) × 5.0 = ₹57,692.31
Exempt = ₹20,00,000 (full exemption applies)
Taxable = ₹0 (gratuity < ₹20L)
```

#### Leave Encashment

```
Earned leave balance in days (from leave-service)
Basic per day = Basic salary / 26

Encashment Gross = Earned days × (Basic / 26)

Exemption (Section 10(10)(AA), new rule FY 2023-24):
  ₹25,00,000 (₹25 lakh) on exit or retirement

Taxable Encashment = Max(0, Encashment – Exemption)
```

**Example:**
```
Employee has 30 earned leave days
Basic = ₹50,000
Basic per day = ₹50,000 / 26 = ₹1,923.08

Encashment = 30 × ₹1,923.08 = ₹57,692.30
Exempt = ₹25,00,000 (full exemption applies)
Taxable = ₹0
```

#### Final Year Tax Calculation

```
Tax Period: April 1 (FY start) to last_working_day

Months worked = Exact months in FY (1-12)

Standard Deduction (pro-rata):
  Full year = ₹75,000
  Pro-rata = ₹75,000 / 12 × months_worked

Taxable Income for FNF:
  Final salary + Gratuity (taxable) + Encashment (taxable)
  – Pro-rata standard deduction

Annual Tax Liability:
  Apply progressive slabs (new regime FY 2025-26)
  Apply 87A rebate (₹60K if taxable ≤ ₹12L)
  Add 4% cess

Final TDS Adjustment:
  Balance to be deducted from FNF
  = Annual tax – YTD TDS deducted so far
  (Capped at ≥ 0; cannot credit back)
```

**Example:**
```
Employee, joined 01-Apr-2023, LWD 31-Mar-2024 (12 months = 1 FY)

Final salary = ₹1,00,000 (pro-rata doesn't apply, full month)
Gratuity taxable = ₹0 (< ₹20L)
Encashment taxable = ₹0 (< ₹25L)

Taxable income = ₹1,00,000 – ₹75,000 = ₹25,000
Annual tax (new regime) = ₹0 (87A rebate applies)
YTD TDS = ₹8,000 (from payroll)
Final TDS adjustment = Max(0, 0 – 8,000) = ₹0 (no additional TDS)
```

#### Loan Recovery

```
Outstanding loans for employee:
  For each active loan:
    recovery_amount = min(loan.outstanding, available_for_fnf)
    available_for_fnf = (final_salary + gratuity + encashment)
                        – (regular deductions + final TDS)

If recovery < outstanding:
  loan_recovery_shortfall = remaining amount
  Flag in warnings for post-exit follow-up
```

**Example:**
```
Employee owes 2 loans:
  Loan A: ₹50,000 outstanding
  Loan B: ₹30,000 outstanding
  Total outstanding = ₹80,000

Final FNF available = ₹95,000 (after deductions)

Recovery:
  Loan A: ₹50,000 (fully recovered)
  Loan B: ₹30,000 (fully recovered)
  Shortfall: ₹0
```

#### Net FNF Payable

```
Gross FNF = Final salary + Gratuity + Encashment
Total Deductions = Regular deductions + Final TDS + Loan recovery
Net FNF = Gross FNF – Total Deductions

If Net FNF < 0:
  ⚠ Employee owes company money
  Requires manual HR intervention
  Cannot auto-deduct beyond net salary (labour law constraint)
```

---

## Usage Examples

### Example 1: Compute FNF

```python
from app.services.fnf_service import FNFService
from datetime import date
from uuid import UUID

service = FNFService(db_session)

summary = await service.compute_fnf(
    employee_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
    company_id=UUID("550e8400-e29b-41d4-a716-446655440001"),
    last_working_day=date(2025, 3, 31),
    joining_date=date(2020, 1, 15),
)

print(f"Net FNF: ₹{summary.net_fnf}")
print(f"Gratuity: ₹{summary.gratuity.gratuity_amount} (taxable: ₹{summary.gratuity.taxable_amount})")
print(f"Leave Encashment: ₹{summary.leave_encashment.encashment_amount}")
print(f"Final TDS: ₹{summary.final_tds_adjustment}")
print(f"Loan Recovery: ₹{summary.total_loan_recovery}")
print(f"Warnings: {summary.warnings}")
```

**Output:**
```
Net FNF: ₹98,500.00
Gratuity: ₹1,38,461.54 (taxable: ₹0.00)
Leave Encashment: ₹57,692.31 (taxable: ₹0.00)
Final TDS: ₹2,345.67
Loan Recovery: ₹25,000.00
Warnings: []
```

### Example 2: Create FNF Payroll Run

```python
payroll_run, summary = await service.create_fnf_payroll_run(
    company_id=UUID("550e8400-e29b-41d4-a716-446655440001"),
    employee_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
    last_working_day=date(2025, 3, 31),
    joining_date=date(2020, 1, 15),
    approved_by=UUID("550e8400-e29b-41d4-a716-446655440002"),
)

print(f"FNF Run ID: {payroll_run.id}")
print(f"Status: {payroll_run.status}")  # COMPLETED
print(f"Locked: {payroll_run.locked_at is not None}")  # True
print(f"Net Payable: ₹{summary.net_fnf}")
```

### Example 3: API Call - Compute FNF

```bash
POST /api/v1/payroll/fnf/compute
  ?employee_id=550e8400-e29b-41d4-a716-446655440000
  &last_working_day=2025-03-31
  &joining_date=2020-01-15

Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "employee_id": "550e8400-e29b-41d4-a716-446655440000",
  "employee_name": "Ramesh Kumar",
  "last_working_day": "2025-03-31",
  "years_of_service": "5.23",
  "final_salary_pro_rata": "95000.00",
  "gratuity": {
    "eligible": true,
    "gratuity_amount": "138461.54",
    "exempt_amount": "138461.54",
    "taxable_amount": "0.00",
    "note": "Gratuity for 5.23 years of service; ₹20L exemption applied"
  },
  "leave_encashment": {
    "earned_leave_balance": 30,
    "encashment_amount": "57692.31",
    "exempt_amount": "57692.31",
    "taxable_amount": "0.00",
    "note": "Leave encashment for 30 earned days @ ₹1923.08/day; ₹25L exemption applied"
  },
  "final_tds_adjustment": "2345.67",
  "total_loan_recovery": "25000.00",
  "gross_fnf": "291153.85",
  "total_deductions_fnf": "27345.67",
  "net_fnf": "263808.18",
  "net_fnf_negative": false,
  "loan_recovery_shortfall": "0.00",
  "warnings": []
}
```

### Example 4: API Call - Create FNF Payroll

```bash
POST /api/v1/payroll/fnf/create-payroll
  ?employee_id=550e8400-e29b-41d4-a716-446655440000
  &last_working_day=2025-03-31
  &joining_date=2020-01-15

Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "run_id": "770e8400-e29b-41d4-a716-446655440003",
  "status": "COMPLETED",
  "net_fnf": "263808.18",
  "gratuity": "138461.54",
  "leave_encashment": "57692.31",
  "message": "FNF payroll processed. Payslip is locked."
}
```

---

## FNF Payslip Snapshot

The `payslips.snapshot JSONB` for FNF contains:

```json
{
  "fnf_type": "full_and_final",
  "final_salary_pro_rata": "95000.00",
  "gratuity": "138461.54",
  "gratuity_taxable": "0.00",
  "leave_encashment": "57692.31",
  "leave_encashment_taxable": "0.00",
  "gross_fnf": "291153.85",
  "final_tds_adjustment": "2345.67",
  "loan_recovery_total": "25000.00",
  "total_deductions_fnf": "27345.67",
  "net_fnf": "263808.18",
  "years_of_service": "5.23",
  "standard_deduction_prorata": "75000.00",
  "final_year_tax_liability": "2345.67"
}
```

---

## Integration Points

### With Employee Service

- Fetch joining_date (used for gratuity eligibility)
- Fetch current designation, department (for Form 16)
- Fetch bank account details for payment

### With Leave Service

- Fetch earned_leave_balance (for encashment calculation)
- Soft fallback: If unavailable, use earned_leave_balance = 0 with warning

### With Loan Service

- Fetch active loans for employee
- Calculate outstanding principal amounts
- Mark loans CLOSED after FNF processing

### With Form16 Service

- Generate Form 16 (Part A + B) for partial financial year
- Include FNF components (gratuity, encashment) in taxable income
- Include final TDS deducted in Part B

### With Notification Service

- Publish `fnf.processed` event
- Email FNF statement + Form 16 to employee
- Attach FNF payslip PDF

---

## Error Handling & Validation

### Errors (Block FNF)

- Employee not found
- No active salary structure
- Invalid dates (LWD < joining_date)
- No YTD data for financial year

### Warnings (Allow FNF, Show to HR)

- Net FNF negative (employee owes company money)
- Loan recovery shortfall (unrecovered loans after FNF)
- Earned leave balance zero (but encashment calculated as ₹0)
- Gratuity eligibility marginal (e.g., 5.01 years)
- Leave-service unavailable (using fallback earned_leave_balance = 0)

---

## Statutory Compliance

### Gratuity (Payment of Gratuity Act, 1972)

| Sector | Eligibility | Exemption | Formula |
|--------|-------------|-----------|---------|
| Private | ≥ 5 years continuous | ₹20 lakh | (Basic+DA) × (15/26) × years |
| Public | ≥ 5 years continuous | ₹10 lakh | Similar |
| Continuous | Must be unbroken service | — | Part-year is <5 years → ₹0 |

### Leave Encashment (Section 10(10)(AA), Budget 2023)

- New rule: ₹25 lakh exemption on **exit** or **retirement**
- Previous limit: ₹3 lakh (phased out for exits from 01-Apr-2023)
- Encashable leave: Earned leave, casual leave (policy-dependent); not LOP or comp-off

### TDS on Gratuity & Encashment (Section 192)

- Gratuity (taxable part): Included in taxable income, standard TDS rates apply
- Encashment (taxable part): Included in taxable income, standard TDS rates apply
- Benefit of exemption: Computed first, then remainder taxed

### Pro-rata Taxation

- Standard deduction ₹75,000 is pro-rated by months worked
- Example: 6 months of FY = ₹75,000 / 12 × 6 = ₹37,500

---

## Verification Checklist

✅ Gratuity calculated correctly (years × basic+DA × 15/26)  
✅ Gratuity exemption applied (₹20L private sector)  
✅ Leave encashment calculated (earned days × basic/26)  
✅ Leave encashment exemption applied (₹25L on exit)  
✅ Years of service ≥ 5.0 for gratuity eligibility  
✅ Pro-rata final salary for partial month  
✅ Pro-rata standard deduction for tax calculation  
✅ Final TDS adjustment non-negative  
✅ All loans marked CLOSED  
✅ Payslip locked (DB trigger prevents edits)  
✅ Form 16 (partial year) generated with FNF components  
✅ Warnings displayed for negative net or loan shortfall  
✅ Event published: `fnf.processed`  

---

## Testing

### Unit Test Example

```python
async def test_fnf_gratuity_eligible():
    """Test gratuity calculation for eligible employee."""
    service = FNFService(db)
    
    joining_date = date(2020, 1, 15)
    last_working_day = date(2025, 3, 31)
    
    summary = await service.compute_fnf(
        employee_id=test_employee_id,
        company_id=test_company_id,
        last_working_day=last_working_day,
        joining_date=joining_date,
    )
    
    assert summary.gratuity.eligible == True
    assert summary.gratuity.gratuity_amount > Decimal("0")
    assert summary.gratuity.taxable_amount == Decimal("0")  # ₹20L exemption

async def test_fnf_pro_rata_salary():
    """Test pro-rated salary for partial month."""
    service = FNFService(db)
    
    joining_date = date(2020, 1, 1)
    last_working_day = date(2025, 3, 15)  # Half month
    
    summary = await service.compute_fnf(...)
    
    # Final salary should be roughly 50% of monthly (15/30 days)
    assert summary.final_salary_pro_rata < monthly_salary
    assert summary.final_salary_pro_rata > Decimal("0")

async def test_fnf_loan_recovery():
    """Test loan recovery from FNF."""
    # Create loans totaling ₹1,00,000
    # Create FNF with net = ₹80,000
    # Expect ₹80,000 recovered, ₹20,000 shortfall
    
    summary = await service.compute_fnf(...)
    
    assert summary.total_loan_recovery == Decimal("80000")
    assert summary.loan_recovery_shortfall == Decimal("20000")
    assert len(summary.warnings) > 0  # Shortfall warning
```

---

## Deployment Considerations

### Database Triggers

Ensure `prevent_locked_payslip_update()` trigger exists (created in Phase 1A migration). This prevents accidental edits to locked FNF payslips.

### Leave Service Integration

FNF calls `fetch_lop_summary()` from leave-service to get earned_leave_balance. Timeout handling:
```python
try:
    earned_days = await fetch_lop_summary(employee_id, ...)
except TimeoutError:
    earned_days = 0
    warnings.append("⚠ Leave-service unreachable; using earned_leave = 0")
```

### Event Publishing

On FNF completion, publish `fnf.processed` event:
```python
await publish_event("fnf.processed", {
    "company_id": str(company_id),
    "employee_id": str(employee_id),
    "run_id": str(payroll_run.id),
    "net_fnf": str(summary.net_fnf),
    "gratuity": str(summary.gratuity.gratuity_amount),
    "user_id": user.sub,
})
```

### Form 16 Generation

After FNF payroll is locked, generate Form 16 (partial year):
```python
form16 = await form16_service.generate_form16(
    employee_id=employee_id,
    financial_year=fy,
    include_fnf=True,  # Flag to include gratuity + encashment
)
```

---

## Future Enhancements

- [ ] Gratuity variants (private/public sector, state-specific rules)
- [ ] Statutory Bonus payment on exit (if eligibility met)
- [ ] Unfunded gratuity reconciliation (if company uses external gratuity fund)
- [ ] Leave surrender (employee keeps unused leave, company pays later)
- [ ] Post-exit recovery workflow (unrecovered loans, outstanding amounts)
- [ ] Multi-currency FNF (foreign workers)
- [ ] Exit clearance checklist integration (asset recovery, notice period)

---

## Troubleshooting

**Q: Why is net_fnf negative?**  
A: Total deductions (PF, ESI, PT, TDS, loans) exceed gross FNF. Common if employee owes large loans. HR must intervene; labour law prevents auto-deduction beyond net salary.

**Q: Gratuity shows ₹0 even though years ≥ 5?**  
A: Check if gratuity is within ₹20L exemption limit. If gratuity < ₹20L, entire amount is exempt, so taxable = ₹0 (correct).

**Q: Leave encashment is ₹0. Did it calculate wrong?**  
A: Check earned_leave_balance from leave-service. If leave-service is down, fallback = 0. Verify leave service is reachable and employee has earned leave balance.

**Q: Can I edit FNF payslip after creation?**  
A: No. FNF payslip is locked immediately (`locked_at` set, DB trigger prevents UPDATE/DELETE). If error found, create a new FNF run or contact senior admin.

---

## Code Locations

| File | Purpose |
|------|---------|
| `app/services/fnf_service.py` | FNFService class with all FNF logic |
| `app/api/v1/endpoints/payroll.py` | `/fnf/compute` and `/fnf/create-payroll` endpoints |
| `app/services/form16_service.py` | Form 16 generation (uses FNF components) |
| `app/services/loan_service.py` | Active loan queries and status updates |
| `app/db/migrations/versions/003_*.py` | DB trigger: `prevent_locked_payslip_update()` |
