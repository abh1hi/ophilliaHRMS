# Payroll Compliance Verification Checklist

**Scope:** India statutory compliance for payroll systems  
**Frequency:** Monthly (per payroll run) + Quarterly + Annual reviews  
**Owner:** HR + Finance + Legal team  
**Last Updated:** 2025-04-07

---

## Pre-Payroll Verification (Before Computing)

### Employee & Salary Data Validation

- [ ] All active employees have salary structures assigned
  - **Check:** `SELECT COUNT(*) FROM employees WHERE salary_structure_id IS NULL`
  - **Expected:** 0 employees

- [ ] No duplicate salary structures for same employee
  - **Check:** `SELECT employee_id, COUNT(*) FROM employee_salaries GROUP BY employee_id HAVING COUNT(*) > 1`
  - **Expected:** Empty result

- [ ] Salary components align with CTC
  - **Check:** Verify Basic + HRA + Allowances ≈ CTC/12
  - **Tolerance:** ±₹1,000

- [ ] CTC amounts reasonable (no zero or negative)
  - **Check:** `SELECT * FROM employee_salaries WHERE ctc <= 0`
  - **Expected:** Empty result

- [ ] Tax profile set for all employees (at least 1x per FY)
  - **Check:** `SELECT COUNT(*) FROM employees e LEFT JOIN employee_tax_profiles t ON e.id = t.employee_id AND t.financial_year = 2026 WHERE t.id IS NULL`
  - **Expected:** 0 employees without tax profile

---

### Statutory Limit Verification

- [ ] No employee's salary < minimum wage (₹10,000/month in most states)
  - **Check:** Verify gross salary meets state minimum wage
  - **Expected:** All salaries ≥ ₹10,000

- [ ] PF applies correctly (wage ceiling: ₹15,000/month basic)
  - **Check:** Employees with basic > ₹15,000 should have capped PF
  - **Rule:** PF = min(basic, 15000) × 12%

- [ ] ESI applies only if gross ≤ ₹21,000/month
  - **Check:** `SELECT employee_id, gross, esi FROM payslips WHERE gross > 21000 AND esi > 0`
  - **Expected:** Empty result (0 ESI for high-salary employees)

- [ ] Provident Fund employee % = 12% (fixed by law)
  - **Check:** Verify all PF calculations use 12%
  - **Expected:** 12% (not 10%, 13%, etc.)

- [ ] Professional Tax within state limits
  - **Check:** Verify PT ≤ ₹200/month (most states)
  - **Expected:** PT between ₹0-₹200

- [ ] LWF (Labour Welfare Fund) if applicable to state
  - **Check:** Maharashtra, Karnataka, etc. require LWF
  - **For Maharashtra:** ₹25/month (half-yearly)
  - **For Karnataka:** ₹50/month (annual)

---

## Payroll Computation Verification

### TDS Calculation Verification

- [ ] TDS follows current financial year slabs
  - **FY 2025-26 New Regime:**
    - Income ≤ ₹12,00,000 → TDS = ₹0
    - Income ₹12,00,001-₹16,00,000 → TDS = 5% of (Income - 12,00,000)
    - Income > ₹16,00,000 → Progressive slab

- [ ] Standard Deduction applied correctly
  - **New Regime:** ₹75,000 (fixed)
  - **Old Regime:** ₹50,000 (fixed)

- [ ] Section 87A rebate applied (if eligible)
  - **Criteria:** Taxable income ≤ ₹12,00,000 (new regime)
  - **Rebate:** Full tax (≤ ₹12,50,000 gross)

- [ ] Health & Education Cess 4% applied
  - **Check:** TDS should include 4% cess on tax amount

- [ ] TDS rounding correct (to nearest ₹10)
  - **Rule:** Section 288B: Round to nearest ₹10
  - **Example:** ₹13,541.50 → ₹13,540 (or ₹13,550)

- [ ] YTD TDS reasonable (progression check)
  - **Check:** Verify TDS increases as YTD income increases
  - **Red Flag:** YTD TDS decreasing month-over-month

- [ ] Pro-rata TDS for mid-month joins
  - **Rule:** TDS = (Annual Tax × Pro-rata Factor) / Remaining months
  - **Check:** Employee joining April 20 should have reduced TDS

---

### PF & ESI Compliance

- [ ] PF contribution split correctly
  - **Employee:** 12% of basic (capped at ₹15,000/month)
  - **Employer EPF:** 3.67% of basic (capped at ₹15,000)
  - **Employer EPS:** 8.33% of basic (capped at ₹1,250/month)
  - **Formula Check:** EPF + EPS + 1% fixed = Total ~13%

- [ ] ESI applies/not-applies consistently
  - **Rule:** If gross ≤ ₹21,000 → Apply ESI; else → No ESI
  - **Employees to check:** High-salary employees (should have 0 ESI)

- [ ] ESI split correct
  - **Employee:** 0.75% of gross (only if gross ≤ ₹21,000)
  - **Employer:** 3.25% of gross (only if employee ESI is being deducted)

---

### Pro-Ration & Loss of Pay (LOP)

- [ ] Mid-month joins pro-rated correctly
  - **Formula:** Pro-rata = Days worked / Calendar days in month
  - **Example:** Joined April 15 in 30-day month = 16 days / 30 = 0.5333
  - **Apply:** Monthly salary × 0.5333 = pro-rated salary

- [ ] Separations pro-rated correctly
  - **Last working day:** April 25 in 30-day month = 25/30 = 0.8333
  - **Salary:** Base × 0.8333

- [ ] LOP (Loss of Pay) deducted correctly
  - **Method 1 (Calendar):** LOP Amount = Gross / Days in month × LOP days
  - **Method 2 (Working Days):** LOP Amount = Gross / 26 × LOP days
  - **Check:** Ensure consistent method applied

- [ ] LOP not double-deducted
  - **Check:** If using working-days method, don't also deduct as calendar
  - **Expected:** One method only

- [ ] No negative gross due to LOP
  - **Check:** Gross - LOP should be ≥ 0
  - **Expected:** Positive gross after LOP

---

### Deduction Limits

- [ ] Total deductions don't exceed gross
  - **Check:** Total deductions < Gross (always)
  - **Red Flag:** If total deductions > gross → ERROR

- [ ] Net salary is positive
  - **Check:** Net = Gross - Deductions > 0
  - **Exception:** FNF settlements (handled separately with HR approval)

- [ ] No unreasonable deductions
  - **Check for:** Loan EMIs, advances, unions, medical, etc.
  - **Limit:** All deductions combined < 50% of gross (guideline)

---

## Post-Computation Verification

### Exception Report Review

- [ ] All ERRORS resolved before approval
  - **Do not approve with errors present**
  - **Errors block:** Missing structure, negative pay, invalid dates

- [ ] All WARNINGS documented
  - **Warnings don't block:** LOP unavailable, variance, etc.
  - **Document:** Why warning appeared & if acceptable

- [ ] Exception report signed off by HR Manager
  - **Initial:** _________________________ Date: _______

---

### Data Sanity Checks

- [ ] Total gross reasonable
  - **Compare:** Previous month total gross
  - **Variance:** ±10% acceptable (unless changes known)
  - **Formula:** Expected ≈ (# Employees × Avg Salary)

- [ ] Total deductions reasonable
  - **Expected:** ~18-25% of gross (TDS + PF + ESI + PT)
  - **Check:** Compare to previous months

- [ ] Net payable matches expectations
  - **Formula:** Net ≈ Gross × 0.75-0.80
  - **Sanity:** Similar ratio month-to-month

- [ ] No duplicate payslips
  - **Check:** `SELECT payroll_run_id, employee_id, COUNT(*) FROM payslips GROUP BY payroll_run_id, employee_id HAVING COUNT(*) > 1`
  - **Expected:** Empty result

- [ ] YTD accumulation correct
  - **Check:** Payslip gross + previous months' gross = YTD gross
  - **Formula:** YTD = Sum of 1-Apr to 30-Apr payslips

---

## Pre-Approval Checklist

### Finance Head Review

- [ ] Reviewed exception report
  - **Sign-off:** _________________________

- [ ] Verified TDS calculations
  - **Sample:** Checked 5 employees across salary ranges
  - **Result:** ✓ PASS / ✗ FAIL

- [ ] Confirmed total payroll within budget
  - **Budget:** ₹₹₹₹₹ (from Finance)
  - **Actual:** ₹₹₹₹₹ (from run)
  - **Variance:** ±₹₹₹₹₹ acceptable?

- [ ] No retroactive changes allowed
  - **Rule:** Once approved, payslips locked. No edits.

- [ ] Statutory deadlines noted
  - [ ] ECR filing: By 15th of next month
  - [ ] Bank transfer: Within 7 days of month-end
  - [ ] TDS payment: By 7th of next month (15th for March)
  - [ ] Form 16: By June 15 (annual)

---

## Processing & Finalization

### Before Clicking "Process"

- [ ] Payroll status = APPROVED
  - **Check:** System shows "APPROVED" badge

- [ ] Backup of current database taken
  - **Command:** `pg_dump payroll_db | gzip > backup_apr_2025.sql.gz`

- [ ] YTD recalculation ready
  - **System will:** Update YTD tables on process

- [ ] Payslips will be locked
  - **Confirmation:** Understood locked = permanent?

### After Processing Completes

- [ ] All payslips locked successfully
  - **Check:** `SELECT COUNT(*) FROM payslips WHERE payroll_run_id = '{{RUN_ID}}' AND locked_at IS NOT NULL`
  - **Expected:** = Total employees

- [ ] YTD updated for all employees
  - **Check:** `SELECT COUNT(*) FROM employee_ytd WHERE month_of_payroll = 4 AND year = 2025`
  - **Expected:** = Total employees

- [ ] ECR file generated and valid
  - **Check:** Download ECR file, verify format
  - **Expected:** 11 fields per line, all employees listed

- [ ] Bank advice generated
  - **Check:** Download CSV, verify all employees have IFSC, account numbers
  - **Expected:** No blank account numbers

---

## Statutory Filing & Payment

### EPFO (PF) Compliance

- [ ] ECR uploaded by 15th of next month
  - **Deadline:** Must upload before 15th
  - **System:** Auto-generates ECR file

- [ ] PF balance accurate
  - **Check:** `SELECT employee_id, SUM(pf_deduction) FROM payslips WHERE payroll_run_id IN (...) GROUP BY employee_id`
  - **Compare:** Employee's EPFO statement

- [ ] PF deposited to EPFO
  - **Deadline:** 15th of next month
  - **Responsible:** Finance/Treasury

- [ ] No pending PF dues
  - **Check:** Finance should zero out this month's PF liability

---

### ESI Compliance

- [ ] ESIC challans filed (if applicable)
  - **Check:** Get proof of filing from Finance
  - **Deadline:** Before month-end or per state rules

- [ ] ESI balance matches payroll
  - **Formula:** Employee ESI + Employer ESI

---

### TDS Compliance

- [ ] TDS deposited to Income Tax
  - **Deadline:** 7th of next month (March → 30th April)
  - **Responsible:** Finance/Accounts

- [ ] TDS certificate issued (Form 16)
  - **Deadline:** By June 15 each year
  - **System:** Auto-generates from payroll records

- [ ] Form 24Q filed (quarterly)
  - **Deadline:** By 31st of quarter month + 15 days
  - **Data source:** Sum of TDS from payroll

---

### Professional Tax & LWF

- [ ] PT filed with state authorities
  - **Deadline:** Varies by state
  - **System:** Generates PT summary by state

- [ ] LWF deposited (if applicable state)
  - **Check:** Maharashtra, Karnataka, etc.
  - **Deadline:** Varies by state

---

## Annual Compliance (FY-End)

### June Reconciliation

- [ ] Form 16 generated for all employees
  - **Deadline:** By June 15
  - **System:** Auto-generates from YTD

- [ ] Form 16 values reconcile with TDS paid
  - **Formula:** Sum of monthly TDS ≈ Form 16 total TDS

- [ ] Part B (Monthly breakup) matches payroll records
  - **Check:** Sample 5 employees, verify each month

---

### Year-End Audit

- [ ] All 12 months' payroll runs locked
  - **Check:** `SELECT COUNT(DISTINCT payroll_run_id) FROM payslips WHERE YEAR(created_at) = 2025`
  - **Expected:** 12 (or 13 if supplementary)

- [ ] YTD balances finalized
  - **Check:** March YTD = Full-year totals
  - **Verify:** No changes after March 31

- [ ] Audit trail complete
  - **Check:** `SELECT COUNT(*) FROM payroll_audit_logs WHERE YEAR(performed_at) = 2025`
  - **Expected:** > 100 entries (all operations logged)

- [ ] No orphaned payslips
  - **Check:** All payslips linked to valid payroll_runs

- [ ] Data backed up for 7 years
  - **Check:** Archive location has previous years' exports
  - **Storage:** Minimum 7 years (Indian law requirement)

---

## Monthly Sign-Off

**Monthly Payroll Reconciliation Certificate**

```
Date: ________________
Payroll Run: April 2025 (APR-2025-001)

I hereby certify that:

1. All employees' salary structures verified
2. TDS calculations comply with current tax slabs
3. All statutory deductions (PF, ESI, PT, LWF) correct
4. Pro-ration & LOP calculated accurately
5. No duplicate payslips or orphaned records
6. Exception report reviewed and all errors resolved
7. Total payroll within budget
8. Payslips locked after processing
9. YTD records updated correctly
10. ECR file generated and will be filed by 15th

HR Manager: _________________________ Date: _______

Finance Head: ________________________ Date: _______

Payroll Admin: ______________________ Date: _______
```

---

## Key Compliance References

**Indian Statutory Requirements:**

| Act/Rule | Requirement | System Compliance |
|----------|-------------|-------------------|
| **Income Tax Act, 1961** | TDS on salary (Section 192) | ✓ Automated calculation |
| **PF Act, 1952** | 12% + 13% (employee + employer) | ✓ Capped at ₹15K |
| **ESI Act, 1948** | 0.75% + 3.25% (if gross ≤ ₹21K) | ✓ Threshold checks |
| **Professional Tax Act (varies)** | State-wise 0-200/month | ✓ State-specific rules |
| **Labour Welfare Fund (varies)** | LWF deduction (16 states) | ✓ Configurable |
| **Form 16** | Annual tax certificate (TDS Act) | ✓ Generated by system |
| **Form 24Q** | Quarterly TDS return | ✓ Data ready for filing |
| **Bonus Act, 1965** | 8.33% bonus (eligible employees) | ⚠️ Manual processing |
| **Gratuity Act, 1972** | 15 days salary per year (≥5 years) | ⚠️ FNF module |
| **Minimum Wages** | State-specific minimum (₹10K+) | ⚠️ HR enforcement |

---

## Escalation Path

If compliance issue detected:

1. **Flag immediately** in Slack #payroll-compliance
2. **Document** the issue with evidence
3. **Contact:** HR Manager → Finance Head → Legal
4. **Don't approve** until resolved
5. **Record** resolution in compliance log
