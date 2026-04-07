# Payroll System: HR Training & Operations Guide

**Version:** 1.0  
**Target Audience:** HR Managers, Payroll Administrators  
**Duration:** 4 hours (compressed) / 1 week (full)  
**Last Updated:** 2025-04-07

---

## Module 1: System Overview (30 minutes)

### What is OphilliaHRMS Payroll?

**OphilliaHRMS Payroll** is an automated monthly salary processing system for Indian companies with statutory compliance built-in.

**Key Features:**
- ✅ Automatic TDS calculation (Income Tax new regime)
- ✅ PF, ESI, Professional Tax deductions
- ✅ Multi-state compliance (PT rules vary by state)
- ✅ ECR file generation (EPFO filing)
- ✅ Form 16 generation (Tax certificates)
- ✅ Bank advice for salary transfer (NEFT/RTGS)
- ✅ Approval workflow (4-step process)
- ✅ Audit trail (complete history)

### System Architecture

```
┌─────────────────┐
│   HR Dashboard  │  ← You are here
└────────┬────────┘
         │
    ┌────▼─────────────────────┐
    │  Payroll Service (8003)  │  ← Backend processing
    ├─────────────────────────┤
    │ - TDS Calculation       │
    │ - Deduction Mgmt        │
    │ - Report Generation     │
    │ - YTD Tracking          │
    └────┬────────────┬───────┘
         │            │
    ┌────▼──┐  ┌──────▼──┐
    │ Postgres DB   Redis Cache  ← Data storage
    └─────────────────────────
```

### Key Actors & Responsibilities

| Role | Responsibility | Permissions |
|------|---------------|----|
| **HR Manager** | Create runs, compute payroll, approve, check reports | Create, Read, Update |
| **Finance Head** | Final approval before processing, audit | Approve, Lock |
| **Payroll Admin** | Monitor, troubleshoot, handle exceptions | Create, Read, Update |
| **System Admin** | Deployment, backups, disaster recovery | Full |
| **Employee** | View own payslip | Read only |

---

## Module 2: Payroll Run Workflow (45 minutes)

### The 4-Step Process

```
STEP 1: CREATE          STEP 2: COMPUTE         STEP 3: APPROVE         STEP 4: PROCESS
        │                       │                       │                       │
        ▼                       ▼                       ▼                       ▼
    [DRAFT]  ─────────►  [REVIEW]  ─────────►  [APPROVED]  ─────────►  [COMPLETED]
        │                       │
        │                       │ (with exceptions?)
        │                       ▼
        │                    Review errors
        │                       │
        │◄──────────────────────┘
        │
    Fix issues & retry
```

### Step 1: Create Payroll Run (Friday Afternoon)

**When:** Last business day of month (or custom date)

**Who:** HR Manager

**How:**
1. Go to **Payroll** → **Payroll Runs** tab
2. Click **"New Payroll Run"** button
3. Fill in:
   - **Period Start:** April 1, 2025
   - **Period End:** April 30, 2025
   - **Run Type:** REGULAR (or BONUS/FNF)
4. Click **"Create"**

**System Does:**
- ✓ Validates date range (no overlaps)
- ✓ Checks for employee salary structures
- ✓ Prepares batch processing
- ✓ Initializes status as **DRAFT**

**What You See:**
```
Created Payroll Run: APR-2025-001
Status: DRAFT (not yet computed)
Employees: 150
Gross Total: ₹0 (will calculate)
Deductions: ₹0
Net Total: ₹0
```

### Step 2: Compute Payroll (Monday Morning)

**When:** 1-2 business days after period end

**Who:** HR Manager or Payroll Admin

**What Happens:**
- System calculates each employee's salary
- Applies deductions (PF, ESI, TDS, PT, LWF)
- Generates draft payslips
- Fetches LOP (Leave of Absence) data from leave system
- Creates validation report

**⏱️ How Long:** 5-10 minutes for 500 employees

**How:**
1. Open **Payroll Runs** tab
2. Find the run in DRAFT status
3. Click **"Compute Payroll"** button
4. Wait for processing to complete

**System Calculates:**

For each employee:
```
GROSS SALARY = Basic + HRA + Allowances

Deductions:
  - PF: 12% of basic (capped at ₹15,000/month)
  - ESI: 0.75% of gross (only if gross ≤ ₹21,000)
  - Professional Tax: ₹0-₹200 (varies by state)
  - TDS: Income tax per new regime
  - LOP Deduction: Loss of Pay per worked days

NET = Gross - Deductions

EMPLOYER COST = Gross + Employer PF + Employer ESI
```

**Example Calculation:**

```
Employee: John Doe (Senior Engineer)
CTC: ₹12,00,000/year (₹1,00,000/month)

EARNINGS:
  Basic:       ₹50,000
  HRA:         ₹20,000
  Allowances:  ₹15,000
  ─────────────────────
  Gross:       ₹85,000

DEDUCTIONS:
  PF (12% of basic):           ₹6,000
  ESI (0.75% of gross):        ₹637
  Professional Tax (MH):       ₹200
  TDS (new regime, based on YTD): ₹13,541
  ─────────────────────────────
  Total Deductions:           ₹20,378

NET PAY:                        ₹64,622

EMPLOYER COST:
  Salary:                      ₹85,000
  Employer PF (13%):           ₹6,500
  Employer ESI (3.25%):        ₹2,763
  ─────────────────────────────
  Total Cost:                  ₹94,263
```

**After Compute:**

You'll see a **Review Report** with:
- ✓ 150 employees processed successfully
- ⚠️ 3 warnings: "LOP data unavailable (leave service timeout)"
- ✗ 0 errors

**If Errors Appear:**

```
ERRORS (blocks approval):
  ✗ Employee EMP-456: No salary structure assigned
  ✗ Employee EMP-789: Negative net pay (TDS > gross)

WARNINGS (info only):
  ⚠️ Employee EMP-123: Month-over-month salary variance > 20%
  ⚠️ LOP data unavailable for 2 employees (using 0 days)
```

**What to Do:**
1. Fix ERRORS (assign salary structure, adjust deductions)
2. Click **"Compute Payroll"** again
3. When no errors remain → proceed to Step 3

### Step 3: Approve Payroll (Monday Afternoon)

**When:** Same day or next day after compute

**Who:** Finance Head or HR Director

**What It Means:**
- Final review before salary transfer
- Legal approval for statutory deductions
- Acknowledgment that data is correct

**How:**
1. **Finance Head** opens Payroll Runs tab
2. Finds run in **REVIEW** status
3. Reads the **Validation Report** carefully
4. Asks: "Are all amounts correct? Are warnings acceptable?"
5. Clicks **"Approve Payroll"** button
6. Status changes to **APPROVED**

**Critical Review Checklist:**

Before approving, verify:

- [ ] Total gross matches expected monthly payroll
- [ ] No employees missing from run
- [ ] TDS amounts seem reasonable (check YTD doesn't exceed annual tax)
- [ ] All warnings documented and explained
- [ ] Pro-rata calculations correct (if mid-month joins)
- [ ] Deductions within statutory limits
- [ ] YTD balances reasonable (no anomalies)

**If Issues Found:**

1. Click **"Reject Payroll"**
2. Enter reason: "TDS calculation seems high for Q3"
3. Status returns to **DRAFT**
4. HR Manager fixes issue and recomputes
5. Finance Head reviews again

### Step 4: Process Payroll (Tuesday Morning)

**When:** 1-2 days before salary transfer date

**Who:** HR Manager (with Finance Head oversight)

**⚠️ CRITICAL:** This is the FINAL step. Locks all payslips permanently.

**What Happens:**
- System finalizes all payslips
- Locks records (cannot be edited)
- Updates YTD (Year-To-Date) cumulative records
- Generates statutory documents:
  - ECR file (for EPFO)
  - Bank advice (for salary transfer)
  - Payslip PDFs
- Publishes event for PDF generation
- Status changes to **COMPLETED**

**How:**
1. Ensure run is in **APPROVED** status
2. Click **"Process Payroll"** button
3. Confirm: "Ready to lock payslips?"
4. System processes (2-5 minutes for 500 employees)
5. Check for errors

**After Processing:**

You can now:
- ✓ Download ECR file (for EPFO submission by 15th)
- ✓ Download Bank Advice (for salary transfer)
- ✓ Download payslip PDFs (for employee distribution)
- ✓ View YTD summaries

**Cannot:**
- ✗ Edit payslips
- ✗ Change amounts
- ✗ Delete records
- ✗ Undo processing

### Optional Step 5: Mark as Paid & Lock

**When:** After salary transferred (within 7 days of transfer)

**Who:** Finance Head or HR Manager

**How:**
1. Confirm salary transferred to all bank accounts
2. Click **"Mark as Paid"**
3. Enter payment reference: "NEFT-APR-2025"
4. Status changes to **PAID**

**Final Lock:**
1. Click **"Lock Payroll"**
2. Status becomes **LOCKED**
3. All records permanently read-only
4. Archived for compliance

---

## Module 3: Understanding Payslips (20 minutes)

### Payslip Structure

Every employee gets a payslip showing:

```
═══════════════════════════════════════════
              PAYSLIP
      April 1 - 30, 2025
═══════════════════════════════════════════

Employee: John Doe (EMP-001)
Department: Engineering
Designation: Senior Software Engineer

EARNINGS:                      AMOUNT
─────────────────────────────────────
Basic Salary          ₹50,000
House Rent Allowance  ₹20,000
Special Allowance     ₹15,000
─────────────────────────────────────
Gross Salary          ₹85,000


DEDUCTIONS:                    AMOUNT
─────────────────────────────────────
Provident Fund (PF)   ₹6,000
Employee State Ins.   ₹637
Professional Tax      ₹200
Income Tax (TDS)      ₹13,541
─────────────────────────────────────
Total Deductions      ₹20,378


═══════════════════════════════════════════
NET PAY:                      ₹64,622
═════════════════════════════════════════════
```

### Key Numbers Explained

**What is TDS (Tax Deducted at Source)?**
- Income tax withheld from salary each month
- Based on government tax slabs
- New Regime (2025): ₹0 if annual income ≤ ₹12,00,000
- Old Regime: Different slabs and exemptions
- Adjusted if Year-To-Date (YTD) income changes

**What is PF (Provident Fund)?**
- Retirement savings (12% of basic salary)
- Capped at ₹15,000/month
- Locked until age 55 or special withdrawal
- Can be claimed at retirement or job change

**What is ESI (Employee State Insurance)?**
- Health insurance contribution (0.75% of gross)
- Only if gross salary ≤ ₹21,000/month
- Covers medical expenses, disability, unemployment

**What is Professional Tax (PT)?**
- State-wise tax on profession/employment
- Varies: ₹0-₹200/month depending on state
- Collected by employer, submitted to state govt

---

## Module 4: Reports & Downloads (20 minutes)

### ECR File (EPFO Filing)

**What:** Electronic Contribution Return file

**When to Download:** By 15th of next month

**How:**
1. Open Payroll Runs tab
2. Find completed run (status = COMPLETED, PAID, or LOCKED)
3. Click menu (⋮) → "Download ECR"
4. File: `ecr_APR-2025-001.txt`

**What's Inside:**
```
UAN#~#Name#~#Gross Wages#~#EPF Wages#~#EPS Wages#~#EDLI Wages#~#EPF Contri#~#EPS Contri#~#EPF-EPS Diff#~#NCP Days#~#Refund of Advances
0AB1234567890#~#John Doe#~#850000#~#500000#~#500000#~#850000#~#60000#~#41667#~#18333#~#2#~#0
```

**Steps to File:**
1. Download ECR file
2. Log into EPFO website (www.epfindia.gov.in)
3. Navigate to "Employers" → "ECR Filing"
4. Upload file before 15th
5. Take screenshot for records

### Bank Advice (Salary Transfer)

**What:** CSV file with employee bank details for fund transfer

**When to Download:** Day before salary transfer

**How:**
1. Open Payroll Runs tab
2. Click "Download Bank Advice"
3. File: `bank_advice_APR-2025-001.csv`

**What's Inside:**
```
Employee ID, Name, Bank Name, IFSC Code, Account Number, Account Type, Net Pay
EMP-001, John Doe, HDFC Bank, HDFC0001234, 1234567890123, Savings, 646220
EMP-002, Jane Smith, ICICI Bank, ICIC0002345, 2345678901234, Current, 758945
```

**Steps to Process:**
1. Send to Finance/Treasury team
2. They upload to bank's salary transfer system
3. Bank processes transfer on specified date
4. Confirm receipt in bank portal

### Payslip PDFs (Employee Distribution)

**What:** Individual payslips for each employee

**When Available:** 1-2 hours after processing (PDFs generated in background)

**How:**
1. Open specific payroll run → Payslips tab
2. Find employee payslip
3. Click "Download PDF"
4. File: `payslip_EMP-001_APR-2025.pdf`

**Distribution Methods:**
- Email to employee email (via email service)
- Download and print for distribution
- Portal access (employee self-service)

### Form 16 (Tax Certificate)

**What:** Tax Deduction Certificate (required for income tax filing)

**When to Generate:** By June 15 each year

**How:**
1. Go to Reports & Exports tab
2. Click "Generate Form 16"
3. Select Employee
4. Select Financial Year: 2026 (for FY 2025-26)
5. Download PDF

**What's Inside:**
```
FORM 16
Tax Deduction Certificate

Employee: John Doe
PAN: ABCDE1234F
FY: 2025-26

Gross Salary:         ₹12,00,000
Less: Standard Deduction: ₹75,000
Taxable Income:       ₹11,25,000

TDS Deducted:         ₹1,62,500

(Part A: Personal Details)
(Part B: Monthly TDS breakup)
```

---

## Module 5: Troubleshooting (25 minutes)

### Common Issues & Fixes

**Issue 1: "Negative Net Pay" Error**

**Symptom:**
```
Cannot process payroll. 
Error: Negative net pay for EMP-456: ₹-50,000
```

**Reason:** Deductions exceed gross (usually TDS error)

**Fix:**
1. Check employee's salary structure is assigned
2. Check for manual deductions (loans, arrears)
3. Verify tax profile (old vs new regime)
4. Adjust TDS in tax profile if needed
5. Recompute payroll

---

**Issue 2: "Employee has no salary structure"**

**Symptom:**
```
Error: Employee EMP-789 has no active salary structure
```

**Reason:** HR department forgot to assign salary structure

**Fix:**
1. Go to **Payroll** → **Settings** → **Salary Structures**
2. Click employee's salary structure
3. Assign to the employee
4. Recompute payroll

---

**Issue 3: "LOP data unavailable" Warning**

**Symptom:**
```
Warning: LOP data unavailable for 5 employees 
(leave service timeout). Using 0 days.
```

**Reason:** Leave system is slow but not critical

**What System Does:** Automatically uses 0 Leave of Absence days

**Fix:**
- No action needed. Warning is expected if leave system slow.
- Optional: HR can manually override LOP if known.

---

**Issue 4: Payroll stuck in APPROVED state**

**Symptom:**
```
Cannot click "Process Payroll" button
Status: APPROVED (but Process button disabled)
```

**Reason:** Another user is processing simultaneously (rare)

**Fix:**
1. Wait 2-3 minutes
2. Refresh page
3. Try again
4. If persists, contact system admin

---

**Issue 5: Cannot download PDF (says "generating")**

**Symptom:**
```
PDF not ready yet. Generation in progress.
Check back in 5-10 minutes.
```

**Reason:** Background worker is still generating PDFs

**Fix:**
1. This is normal after Process step
2. Wait 5-10 minutes
3. Refresh and try again
4. If > 30 min, contact admin

---

## Module 6: Month-End Checklist (10 minutes)

**Use this before approving each month's payroll:**

```
□ BEFORE Compute:
  □ Confirm period dates (e.g., April 1-30)
  □ Confirm all employees have salary structures
  □ Verify no duplicate/overlapping runs
  □ Check for employees with multiple designations

□ AFTER Compute:
  □ Read validation report
  □ Fix all ERRORS (blocks approval)
  □ Document all WARNINGS
  □ Review TDS for reasonableness (compare to last month)
  □ Spot-check pro-rata if any mid-month joins
  □ Confirm total gross matches budget

□ BEFORE Approve:
  □ Finance head reviews report
  □ Asks: "Does everything look right?"
  □ Approves (or asks to revise)

□ BEFORE Process:
  □ Confirm approved
  □ Prepare ECR file upload (by 15th)
  □ Prepare bank transfer file
  □ Notify employees (payslips coming)

□ AFTER Process:
  □ Download ECR file
  □ Download Bank Advice
  □ Initiate salary transfer
  □ Monitor for any bounces
  □ Mark as Paid (after transfer confirmed)
  □ Lock payroll (after 7 days)

□ END OF MONTH:
  □ Archive ECR uploaded proof
  □ Archive bank transfer confirmations
  □ Verify all payslips accessible to employees
  □ Prepare audit file
```

---

## Quick Reference Card

**Print this and keep at desk:**

| Step | Status | Action | Owner | Time |
|------|--------|--------|-------|------|
| 1 | DRAFT | Create run | HR Manager | 2 min |
| 2 | REVIEW | Compute payroll | HR Manager | 10 min |
| - | REVIEW | Review errors | HR Manager | 5 min |
| 3 | APPROVED | Approve | Finance Head | 5 min |
| 4 | COMPLETED | Process & download files | HR Manager | 10 min |
| 5 | PAID | After transfer confirmed | Finance | - |
| 6 | LOCKED | Final archive | HR Manager | - |

---

## FAQs

**Q: Can I edit a payslip after it's been created?**
A: Only before processing. After Process step → locked permanently.

**Q: What if I discover an error in the locked payslip?**
A: Create a supplementary payroll run (FNF) to correct it.

**Q: Can two people compute the same payroll simultaneously?**
A: No. System locks it. Second person gets error "Payroll locked." Retry after 5s.

**Q: Is TDS final?**
A: Not exactly. It's an estimate based on expected annual income. Final tax is calculated at year-end. Any excess is refunded; shortfall is paid by employee.

**Q: What if salary transfer fails for some employees?**
A: Contact Finance. They'll retry or reconcile. Payslip is locked; no manual adjustment needed.

**Q: How long do I keep records?**
A: India requires 7 years. System archives all payslips + ECR files.

---

## Training Completion

✓ You've learned:
- 4-step payroll workflow
- Calculation logic
- Report generation
- Troubleshooting
- Compliance steps

**Next:** Practice with a test run, then handle your first production payroll with a mentor.

**Questions?** Contact payroll-support@ophillia.com or Slack #payroll-help
