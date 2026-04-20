# Ophillia HRMS — Admin & HR Setup Guide

---

## Setup Checklist (Do in This Order)

| # | Step | Section |
|---|---|---|
| 1 | HR Setup — Departments, Branches, Designations, Employment Types, Grades, Groups | HR Setup |
| 2 | Shift Locations — GPS coordinates + geofence radius per office | Shifts |
| 3 | Shift Types — named working-hours patterns | Shifts |
| 4 | Add Employees — one by one or bulk CSV | Employees |
| 5 | Shift Assignments — assign each employee a shift + location | Shifts |
| 6 | Leave Types — Annual, Sick, Casual, etc. | Leaves |
| 7 | Leave Periods — annual calendar container | Leaves |
| 8 | Holiday Lists — public + company holidays | Leaves |
| 9 | Leave Policies — rules: carry-forward, accrual, max days | Leaves |
| 10 | Policy Assignments — assign policies to employees/groups | Leaves |
| 11 | Leave Allocations — grant annual entitlement per employee | Leaves |
| 12 | Overtime Policies — thresholds + pay multipliers (if applicable) | Overtime |
| 13 | Salary Structures + Tax Profiles | Payroll |

> Attendance tracking is live after Steps 1–5. Leave and Payroll require Steps 6–13.

---

## Step 1 — HR Setup

Navigate to the **HR Setup** section. Complete all six items before adding employees.

### Departments
1. Go to **HR Setup → Departments**. Click **Add Department**.
2. Enter the name (Engineering, Finance, HR, Operations, Sales, etc.).
3. Optionally set a parent department for nested org charts.
4. Save. Repeat for all departments.

### Branches
1. Go to **HR Setup → Branches**. Click **Add Branch**.
2. Enter the branch name and city/country.
3. Add every office location, warehouse, or remote hub your company operates.

### Designations
1. Go to **HR Setup → Designations**. Click **Add Designation**.
2. Add every job title used in your organisation.
3. Examples: Software Engineer, Team Lead, Product Manager, Accounts Executive, HR Specialist.

### Employment Types
1. Go to **HR Setup → Employment Types**. Click **Add**.
2. Add all relevant types: Full-Time, Part-Time, Contract, Intern, Consultant, Freelancer.

### Employee Grades
1. Go to **HR Setup → Employee Grades**. Click **Add Grade**.
2. Define compensation bands: L1/L2/L3, or Junior/Mid/Senior/Lead, or Band A/B/C.
3. Grades link to salary structures in Payroll.

### Employee Groups
1. Go to **HR Setup → Employee Groups**. Click **Add Group**.
2. Create logical groupings used for leave policy assignment.
3. Examples: "Management", "Field Staff", "Remote Workers", "Sales Team".

---

## Step 2 — Shift Locations & Geofencing

Navigate to **Shifts → Shift Locations**.

Geofencing ensures employees can only check in from authorised physical locations. The system compares the employee's GPS location at check-in time with the defined coordinates + radius.

### Creating a Location
1. Click **Sync Hub**.
2. Enter the **Hub Designation** — a recognisable name (e.g. "Headquarters", "Mumbai Branch").
3. Enter the **Logistics Address** — full building address.
4. Enter **Latitudinal Point** and **Longitudinal Point** (decimal GPS coordinates).
   - To get coordinates: open Google Maps → right-click the building entrance → copy the lat/lng.
5. Set the **Radial Perimeter (metres)** — the check-in allowance radius.
6. Save. Create one entry per physical work site.

### Recommended Radius by Site Type
| Site Type | Radius |
|---|---|
| Small office / single floor | 50–100 m |
| Large campus / business park | 200–500 m |
| Construction site / field work | 500–2000 m |
| Work from home / remote | 50,000 m |

> **Warning:** Incorrect GPS coordinates are the most common setup mistake. Always pin the exact building entrance — not the road or car park.

---

## Step 3 — Shift Types

Navigate to **Shifts → Shift Types**.

### Creating a Shift Type
1. Click **New Shift Type**.
2. Enter a **Name** (e.g. "Morning 9–6", "Night Shift", "Flexible").
3. Set **Start Time** and **End Time** in 24-hour format.
4. Set **Break Minutes** — unpaid break deducted from work hours.
5. Set **Grace Period Minutes** — extra minutes after shift start before a Late mark is applied. Recommended: 5–15 min.
6. Toggle **Night Shift** ON if the shift crosses midnight.
7. Save.

### Common Shift Patterns
| Name | Start | End | Break | Grace | Night Shift |
|---|---|---|---|---|---|
| General | 09:00 | 18:00 | 60 min | 10 min | Off |
| Morning | 06:00 | 14:00 | 30 min | 5 min | Off |
| Afternoon | 14:00 | 22:00 | 30 min | 5 min | Off |
| Night | 22:00 | 06:00 | 30 min | 5 min | **On** |
| Flexible | 09:00 | 19:00 | 60 min | 30 min | Off |

---

## Step 4 — Adding Employees

Navigate to **Employees → Employee Directory**.

### One at a Time
1. Click **Add Employee**.
2. **Personal tab:** first name, last name, date of birth, gender, phone, personal email.
3. **Employment tab:** department, branch, designation, employment type, grade, joining date.
4. Save — an invitation email is sent automatically.

### Bulk Import (Recommended for 10+ employees)
1. Go to **Employees → Bulk Import**.
2. Click **Download Template** to get the CSV format.
3. Fill one employee per row. Required fields marked `*`.
4. Required columns: `first_name`, `last_name`, `email`, `department_name`, `branch_name`, `designation_name`, `employment_type_name`, `joining_date`.
5. Save as CSV and upload.
6. The system validates each row — errors are shown inline. Fix and re-upload.
7. Monitor the queue: each row goes Queued → Processing → Success / Failed.

> **Note:** Department, Branch, Designation, and Employment Type values in the CSV must match **exactly** what you created in HR Setup (Step 1). Spelling differences cause row failures.

---

## Step 5 — Shift Assignments

Navigate to **Shifts → Shift Assignments**.

Without a shift assignment, the attendance system cannot calculate work hours, late arrivals, or overtime.

### Assigning a Shift
1. Click **New Assignment**.
2. Select the **Employee**.
3. Select the **Shift Type** (from Step 3).
4. Select the **Shift Location** (geofenced site from Step 2).
5. Set the **Effective From** date.
6. Optionally set an **Effective To** date for temporary assignments.
7. Save.

> An employee can have only one active shift assignment at a time. To change a shift, create a new assignment — the old one expires when the new one starts.

### Viewing the Roster
- **Shifts → Roster** — weekly calendar view of all assignments.
- **Shifts → Shift Schedules** — timeline view by employee.

---

## Step 6 — Leave Types

Navigate to **Leaves → Leave Types**.

1. Click **Add Leave Type**.
2. Enter the name: Annual Leave, Sick Leave, Casual Leave, Maternity Leave, Paternity Leave, etc.
3. Set **Days Allowed Per Year** — the maximum annual entitlement.
4. Toggle **Requires Manager Approval** for types needing HR sign-off.
5. Save. Create one type per leave category.

---

## Step 7 — Leave Periods

Navigate to **Leaves → Leave Periods**.

1. Click **New Period**.
2. Name it (e.g. "FY 2025").
3. Set Start Date (01-Jan-2025) and End Date (31-Dec-2025).
4. Save. This is the container all leave allocations and transactions belong to.

---

## Step 8 — Holiday Lists

Navigate to **Leaves → Holiday Lists**.

1. Click **New List**.
2. Name it (e.g. "National Holidays 2025"). Set valid-from and valid-to covering the leave period.
3. Save. Then click the **+** icon on the row to add individual entries.
4. Add each holiday: select the date and enter a description (e.g. "Republic Day").
5. Add every public holiday and company-specific paid holiday.

---

## Step 9 — Leave Policies

Navigate to **Leaves → Leave Policies**.

1. Click **New Policy**.
2. Set the policy name.
3. Set maximum consecutive leave days.
4. Configure carry-forward: maximum days that roll over to the next year.
5. Link the Holiday List from Step 8.
6. Set accrual frequency: Monthly, Quarterly, or Annual.
7. Save. Create separate policies if rules differ by group (e.g. management vs field staff).

---

## Step 10 — Policy Assignments

Navigate to **Leaves → Policy Assignments**.

1. Click **New Assignment**.
2. Select the employee (or employee group).
3. Select the policy from Step 9.
4. Set the effective date.
5. Save. Every employee must have at least one active policy assignment.

---

## Step 11 — Leave Allocations

Navigate to **Leaves → Leave Allocations**.

1. Click **New Allocation**.
2. Select the employee, leave type, and leave period.
3. Enter **New Leaves Allocated** — the entitlement for this period.
4. Enter **Carry Forward Days** from the previous year (if applicable).
5. Total = New + Carry Forward.
6. Save. Repeat for every employee × every leave type.

> After completing Steps 6–11, employees can submit leave requests. Monitor balances at **Leaves → Leave Balances**.

---

## Step 12 — Overtime Policies (Optional)

Navigate to **Overtime → Overtime Policies**.

Skip if your organisation does not pay overtime.

1. Click **New Policy**.
2. Select a compliance template (India Factories Act: 2× after 9h; EU WTD: 1.25× after 10h) or configure manually.
3. Set **Daily OT After (h)** — hours after which overtime pay begins (e.g. 9).
4. Set **Weekly OT After (h)** — total weekly hours threshold (e.g. 48).
5. Set **Daily OT Rate (×)** — pay multiplier (e.g. 1.5 or 2.0).
6. Set **Grace Minutes** — buffer after shift end before OT counting starts (e.g. 15).
7. Set scope: Company-wide, Department, or specific Employee.
8. Save.

### Overtime Approval Flow
1. Employees submit requests → HR reviews at **Overtime → Overtime Requests**.
2. Approved overtime is aggregated in **Overtime → Overtime Records**.
3. View monthly reports at **Overtime → Overtime Reports**.

---

## Step 13 — Payroll Setup

Navigate to **Payroll → Settings**.

### Salary Structures
1. Go to **Salary Structures** tab. Click **New Structure**.
2. Name it (e.g. "Standard CTC", "Senior Band").
3. Set component percentages:
   - **Basic %** — % of CTC as basic salary (typically 40–50%). Drives PF and HRA calculations.
   - **HRA %** — House Rent Allowance as % of basic (typically 40–50%).
   - **Allowances %** — special/ad-hoc allowances.
   - **PF %** — Provident Fund (India: 12% each for employer + employee).
   - **ESI %** — Employee State Insurance (India: 3.25% employer, 0.75% employee).
4. Save. Assign a structure to each employee from their employment profile.

### Tax Profiles
1. Go to the **Tax Profile** tab. Create a profile per tax regime.
2. Set TDS slab rates, standard deduction, and applicable exemptions.
3. Assign profiles to employees from their profile page.

### Running Payroll
1. Click **New Payroll Run**. Select the month and confirm employees in scope.
2. The system auto-calculates: gross, deductions (PF, ESI, TDS), and net pay.
3. Review the run. Click **Finalise** to lock.
4. Payslips are available for download as PDFs.

> Every employee needs both a Salary Structure and a Tax Profile before running payroll. Those without are excluded.

---

## Day-to-Day Operations

### Attendance
| Task | Where |
|---|---|
| View daily records | Attendance → Attendance Records |
| Approve adjustment requests | Attendance → Attendance Adjustments |
| Bulk approve pending requests | Tick checkboxes → Approve All |
| Import biometric data | Attendance → Import from Biometric |
| Manage holiday calendars | Attendance → Holiday Calendars |

### Leave
| Task | Where |
|---|---|
| View all employee balances | Leaves → Leave Balances |
| Block leave during critical periods | Leaves → Leave Block Lists |
| Process comp-off grants | Leaves → Compensatory Leave |
| Process leave encashment | Leaves → Leave Encashment |
| Full leave audit trail | Leaves → Leave Ledger |

---

## Role Permissions

| Feature | Admin | HR | Employee |
|---|:---:|:---:|:---:|
| HR Setup (Depts, Branches…) | ✓ | ✓ | — |
| Add / Edit Employees | ✓ | ✓ | — |
| Delete Employees | ✓ | — | — |
| Bulk Import Employees | ✓ | ✓ | — |
| Manage Shift Types / Locations | ✓ | ✓ | — |
| Assign Shifts | ✓ | ✓ | — |
| View Attendance Records | ✓ | ✓ | — |
| Approve Attendance Requests | ✓ | ✓ | — |
| Submit Attendance Request | ✓ | ✓ | ✓ |
| Manage Leave Policies | ✓ | ✓ | — |
| Approve Leave Requests | ✓ | ✓ | — |
| View Own Leave Balance | ✓ | ✓ | ✓ |
| Manage Overtime Policies | ✓ | — | — |
| Approve Overtime Requests | ✓ | ✓ | — |
| View Payroll | ✓ | ✓ | — |
| Run Payroll | ✓ | — | — |
| Manage Salary Structures | ✓ | — | — |
| View Own Payslips | ✓ | ✓ | ✓ |

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `⌘K` / `Ctrl+K` | Open command palette — search or jump to any section |
| `↑` / `↓` | Navigate command palette results |
| `Enter` | Select highlighted result |
| `Esc` | Close command palette or any open drawer |

---

*Ophillia HRMS — Last updated April 2026*
