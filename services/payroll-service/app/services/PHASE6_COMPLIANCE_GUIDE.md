# Phase 6: Statutory Compliance & Reporting Guide

## Overview

Phase 6 provides statutory compliance and reporting capabilities for:
1. **ECR (Electronic Challan cum Return)** — EPFO filing
2. **ESIC Return** — Employee State Insurance data
3. **PT Challan** — Professional Tax per state
4. **Form 16** — Income Tax Certificate for employees
5. **Bank Advice** — Salary transfer files for banks

---

## 1. ECR (Electronic Challan cum Return) — EPFO

### What is ECR?
ECR is EPFO's return filing format containing monthly EPF contribution details.
Submitted monthly to EPFO for Form 12A/12B, ECR (monthly), and OCR (quarterly).

### ECR File Format
```
UAN #~# Name #~# Gross Wages #~# EPF Wages #~# EPS Wages #~# EDLI Wages #~#
EPF Contri #~# EPS Contri #~# EPF-EPS Diff #~# NCP Days #~# Refund of Advances
```

### Example Line
```
UAN123456789012#~#Ramesh Kumar#~#100000#~#15000#~#15000#~#15000#~#
1800#~#1250#~#550#~#0#~#0
```

### API Endpoint
```
GET /payroll/runs/{id}/ecr-file
Content-Type: text/plain
Content-Disposition: attachment; filename=ecr_april_2025.txt
```

### Field Mapping
| ECR Field | Source | Calculation |
|-----------|--------|-------------|
| UAN | Employee | From employee service |
| Name | Employee | From employee service |
| Gross Wages | Payslip | payslip.gross |
| EPF Wages | Payslip | min(basic, ₹15,000) |
| EPS Wages | Payslip | Same as EPF wages |
| EDLI Wages | Payslip | Same as EPF wages |
| EPF Contribution | Payslip | pf_deduction + pf_employer |
| EPS Contribution | Payslip | Employer EPS portion (~₹1,250) |
| EPF-EPS Diff | Payslip | Employee PF - EPS contribution |
| NCP Days | Payslip | payslip.lop_days |
| Refund of Advances | Loan Service | Outstanding loans closed (TBD) |

### Workflow
```
1. Payroll processed (COMPLETED state)
2. HR/Admin downloads ECR file
3. Import into EPFO online portal
4. EPFO validates and issues receipt
5. Portal shows monthly compliance status
```

---

## 2. ESIC Return — Employee State Insurance

### What is ESIC?
Monthly return filed with ESIC containing employee-wise contribution details.
Only applicable for gross salary ≤ ₹21,000/month.

### API Endpoint
```
GET /payroll/runs/{id}/esic-return
Content-Type: application/json
```

### Response Example
```json
{
  "return_period": "2025-04",
  "period_start": "2025-04-01",
  "period_end": "2025-04-30",
  "total_employees_covered": 150,
  "total_esi_employee_contribution": "11250.50",
  "total_esi_employer_contribution": "45802.05",
  "total_esi_contribution": "57052.55",
  "employee_details": [
    {
      "employee_id": "uuid",
      "gross_wages": "20000",
      "esi_employee": "150.00",
      "esi_employer": "650.00",
      "total_esi": "800.00"
    }
  ]
}
```

### Eligibility
- **Covered**: Employees with gross ≤ ₹21,000/month
- **Not Covered**: Above ₹21,000/month (marked as such in ESIC records)

### Coverage Tracking
ESIC tracks:
- Continuous covered period
- Contributions and benefits accrued
- Benefit eligibility (medical, cash, maternity, etc.)

---

## 3. Professional Tax (PT) Challan — State-wise

### What is PT?
State-wise employment tax levied on salary.
Collected monthly/half-yearly per state rules.

### API Endpoint
```
GET /payroll/runs/{id}/pt-challan/{state_code}
Content-Type: application/json
```

### Response Example
```json
{
  "state": "MH",
  "period": "2025-04",
  "total_employees": 200,
  "total_pt_due": "40000.00",
  "deposit_deadline": "2025-05-15",
  "employee_details": [
    {
      "employee_id": "uuid",
      "gross_wages": "100000",
      "pt_amount": "200.00"
    }
  ]
}
```

### State-wise Rules (Implemented in Phase 2)
| State | Collection | Slab | Female Exemption |
|-------|-----------|------|-----------------|
| MH | Monthly | ₹0-₹7.5K: ₹0; ₹7.5K-₹10K: ₹175; >₹10K: ₹200 | ≤₹25K exempt |
| KA | Monthly | ≤₹25K: ₹0; >₹25K: ₹200 | None |
| TN | Half-yearly | Slab-based (₹0-₹6,570) | None |
| AP | Monthly | Variable slabs | None |
| TS | Monthly | Similar to AP | None |

### Payment Deadlines
- Monthly States: 15th of next month
- Half-yearly States: June 15 (Apr-Sep), December 15 (Oct-Mar)

---

## 4. Form 16 — Income Tax Certificate

### What is Form 16?
Statutory certificate issued by employer showing:
- Salary received
- TDS deducted
- Eligible deductions
- Tax computation for the financial year

### API Endpoint
```
GET /payroll/ytd/{employee_id}/form16?financial_year=2026
Content-Type: application/json
```

### Form 16 Structure

#### Part A: Employer & Employee Details
```json
{
  "deductor": {
    "name": "Company Name",
    "pan": "AACRP5055K",
    "address": "Company Address"
  },
  "deductee": {
    "name": "Employee Name",
    "pan": "AAAAB1234C",
    "aadhaar": "1234 5678 9012",
    "address": "Employee Address"
  }
}
```

#### Part B: Salary & Tax Details
```json
{
  "salaries": {
    "gross_salary": "1200000",
    "basic": "600000",
    "hra": "240000",
    "allowances": "360000"
  },
  "deductions": {
    "section_80_c": "100000",
    "section_80_d": "25000",
    "standard_deduction": "75000",
    "taxable_income": "1000000"
  },
  "tax_calculation": {
    "tax_before_rebate": "162500",
    "rebate_87a": "0",
    "tax_after_rebate": "162500",
    "cess_4_percent": "6500",
    "total_tax_liability": "169000"
  },
  "tds_deducted": {
    "monthly_tds": "162000",
    "total_tds_deposited": "162000"
  },
  "reconciliation": {
    "total_tax_liability": "169000",
    "tds_deducted": "162000",
    "balance_due": "7000"
  }
}
```

### Issue Timeline
- **Issue by**: June 15 of next financial year
- **Period**: April 1 - March 31
- **Uses**: Filing ITR, verifying income, loans, visas, etc.

### YTD Data Requirements
Form 16 requires complete YTD for all 12 months:
- April → March (full calendar)
- All payslips locked (from Phase 4 PROCESS)
- Tax profile with regime choice
- Investment declarations (80C, 80D, NPS)

---

## 5. Bank Advice — Salary Transfer Files

### What is Bank Advice?
File containing employee banking details for bulk salary transfers.
Used by treasury/finance to process salary via NEFT/RTGS.

### API Endpoints

#### CSV Format (Simple)
```
GET /payroll/runs/{id}/bank-advice.csv
Content-Type: text/csv
```

**Output**:
```
Employee ID,Employee Name,Account Number,IFSC Code,Net Salary
emp-001,Ramesh Kumar,1234567890123456,AXIS0000001,95000.00
emp-002,Priya Sharma,9876543210987654,HDFC0000002,87500.00
```

#### NEFT Format (Bank-specific)
```
GET /payroll/runs/{id}/bank-advice.neft
Content-Type: text/plain
```

**Output**:
```
HDR|07042025|SALARY|INR|2|182500.00
000001|emp-001|AXIS0000001|1234567890123456|95000.00|Ramesh Kumar
000002|emp-002|HDFC0000002|9876543210987654|87500.00|Priya Sharma
```

#### Payment Schedule Summary
```
GET /payroll/runs/{id}/payment-schedule
Content-Type: application/json
```

**Output**:
```json
{
  "payroll_run_id": "uuid",
  "period": "2025-04-01 to 2025-04-30",
  "summary": {
    "total_employees": 500,
    "total_gross_salary": "50000000.00",
    "total_deductions": "8500000.00",
    "total_net_payable": "41500000.00"
  },
  "payment_modes": {
    "bank_transfer": {
      "count": 495,
      "amount": "41400000.00",
      "method": "NEFT/RTGS"
    },
    "cash": {
      "count": 5,
      "amount": "100000.00"
    }
  }
}
```

### Bank Details Verification
```
GET /payroll/runs/{id}/verify-bank-details
```

**Response**:
```json
{
  "total_employees": 500,
  "ready_for_transfer": 498,
  "incomplete_details": 2,
  "missing_details": [
    {
      "employee_id": "emp-xxx",
      "missing_fields": ["account_number"]
    }
  ],
  "can_process": false
}
```

---

## Compliance Workflow Example

### April 2025 Payroll Processing → Compliance Filing

```
Timeline:
├─ April 7: Payroll locked (COMPLETED)
│
├─ April 10: Finance downloads
│  ├─ Bank advice CSV → Treasury for salary transfer
│  ├─ Payment schedule → Finance approval
│  └─ Bank details verification
│
├─ April 15: Finance processes
│  ├─ Salary transferred (PAID)
│  ├─ Payroll locked (LOCKED)
│  └─ Mark receipts in system
│
├─ May 7: EPFO Compliance
│  ├─ Download ECR file
│  ├─ Upload to EPFO portal
│  └─ Deposit EPF + EPS (by May 15)
│
├─ May 10: ESIC Compliance
│  ├─ Download ESIC return
│  ├─ Upload to ESIC portal
│  └─ Deposit ESIC (by May 15)
│
├─ May 15: PT Compliance (per state)
│  ├─ Download PT challan (all states)
│  ├─ Deposit with state authorities
│  └─ Upload receipts
│
└─ June 15: Form 16 Issuance
   ├─ Generate Form 16 for all employees
   ├─ Send via email to employees
   └─ Maintain copies for audit
```

---

## Integration Points

### With Payroll Computation (Phase 3-5)
- **Gross Salary**: Used in all compliance reports
- **LOP Days**: Reported in ECR as NCP (No Contribution Period)
- **Tax Regime**: Affects Form 16 tax calculation
- **Adjustments**: Bonus/arrears included in taxable income
- **Loans**: EMI deductions shown in employee statement

### With Employee Service (TBD)
- Employee UAN, name, email
- Bank account number, IFSC
- Aadhaar number (for Form 16)
- PAN number
- Address

### With Tax Profiles (Phase 1A)
- Tax regime choice (old/new)
- Investment declarations (80C, 80D, NPS)
- HRA details for exemption calculation
- Metro city status for HRA calculation

---

## Security & Audit

### Data Privacy
- Form 16 contains sensitive tax information → Encrypted transmission
- Bank details never logged in audit trails
- ECR files downloaded by authorized users only

### Compliance Audit
- All report downloads logged in `payroll_audit_logs`
- Date/time/user captured for regulatory audits
- Immutable once payroll LOCKED

### Corrections
- After LOCKED, no corrections possible in that payroll
- Corrections via arrears in next month or off-cycle run
- Amended Form 16 issued if adjustments > threshold

---

## Testing Checklist

✅ ECR file generates with correct format (11 fields, #~# separator)  
✅ EPF wages capped at ₹15,000  
✅ ESIC covers only ≤₹21,000 salary employees  
✅ PT rules per state applied correctly (female exemptions, surcharges)  
✅ Form 16 tax calculation matches annual TDS deducted  
✅ Bank advice includes all employees with net > ₹0  
✅ Payment schedule totals match payroll run summary  
✅ Missing bank details flagged before file generation  
✅ Compliance files can be downloaded after payroll LOCKED  

---

## Regulatory References

- **ECR**: EPFO Form 12A/12B, ECR (Monthly), ECR (Quarterly)
- **ESIC**: ESI Code, ESIC Returns (Forms 5, 6)
- **PT**: State PT Acts (varies by state)
- **Form 16**: Income Tax Rules 1962, Section 203AA
- **Bank Transfers**: RBI NEFT/RTGS guidelines, ECCS standards

