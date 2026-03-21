# OphilliaHRMS — Admin Panel Gap Analysis

> **Audit Date:** 2026-03-21
> **Auditor:** Senior Full-Stack Architect
> **Scope:** Backend services vs. Admin Panel UI coverage
> **Backend:** 8 microservices (Auth, Employee, Attendance, Leave, Payroll, Notification, Students, Audit)
> **Frontend:** Vue 3 + Vuetify 3 admin panel (15 pages, 10 Pinia stores)

---

## Table of Contents

1. [Covered Features](#-covered-features)
2. [Partially Covered Features](#️-partially-covered-features)
3. [Missing UI — High Priority](#-missing-ui--high-priority)
4. [Missing UI — Medium Priority](#-missing-ui--medium-priority)
5. [Missing UI — Low Priority](#-missing-ui--low-priority)
6. [Role-Based Access Gaps](#-role-based-access-gaps)
7. [UX Improvements](#-ux-improvements)
8. [Missing Reusable Components](#-missing-reusable-components)
9. [Summary Matrix](#-summary-matrix)

---

## ✅ Covered Features

These backend features have corresponding, functional UI implementations.

| # | Domain | Feature | Backend Endpoint | UI Page | CRUD Coverage |
|---|--------|---------|-----------------|---------|---------------|
| 1 | Auth | Login | `POST /auth/login` | `Login.vue` | ✅ Full |
| 2 | Auth | Logout | `POST /auth/logout` | Sidebar + AppBar | ✅ Full |
| 3 | Auth | Fetch current user | `GET /auth/me` | `auth.store.ts` | ✅ Full |
| 4 | Auth | Post-login context | `GET /auth/post-login-context` | `Login.vue` routing | ✅ Full |
| 5 | Auth | Company selection | `POST /auth/select-company` | `SelectCompany.vue` | ✅ Full |
| 6 | Auth | Company creation | `POST /auth/companies` | `CreateCompany.vue` | ✅ Full |
| 7 | Employee | List employees | `GET /employees` | `Employees.vue` | ✅ Full (paginated, searchable) |
| 8 | Employee | Create employee | `POST /employees` | `Employees.vue` → `EmployeeForm.vue` | ✅ Full (8-tab form) |
| 9 | Employee | Update employee | `PATCH /employees/{id}` | `Employees.vue` → `EmployeeForm.vue` | ✅ Full |
| 10 | Employee | Deactivate employee | `DELETE /employees/{id}` | `Employees.vue` confirm dialog | ✅ Full |
| 11 | Employee | View employee detail | `GET /employees/{id}` | `EmployeeDetailDrawer.vue` | ✅ Full |
| 12 | Department | Full CRUD | All department endpoints | `Departments.vue` | ✅ Full (C/R/U/D) |
| 13 | Attendance | Clock in/out | `POST /attendance/clock-in`, `clock-out` | `Attendance.vue` punch card | ✅ Full |
| 14 | Attendance | Today's record | `GET /attendance/me/today` | `Attendance.vue` | ✅ Full |
| 15 | Attendance | History list | `GET /attendance` | `Attendance.vue` DataTable | ✅ Full (paginated) |
| 16 | Attendance | Alerts | `GET /attendance/alerts` | `Attendance.vue` banners | ✅ Full |
| 17 | Leave | List requests | `GET /leave-requests` | `LeaveManagement.vue` | ✅ Full (paginated) |
| 18 | Leave | Submit request | `POST /leave-requests` | `LeaveManagement.vue` modal | ✅ Full |
| 19 | Leave | Approve/Reject | `PUT /leave-requests/{id}/status` | `LeaveManagement.vue` action buttons | ✅ Full |
| 20 | Leave | View balances | `GET /leave-balances/{employee_id}` | `LeaveManagement.vue` cards | ✅ Full |
| 21 | Leave | List leave types | `GET /leave-types` | `LeaveManagement.vue` select | ✅ Read only |
| 22 | Payroll | List payroll runs | `GET /payroll/runs` | `Payroll.vue` DataTable | ✅ Full |
| 23 | Payroll | Initiate payroll run | `POST /payroll/run` | `Payroll.vue` modal | ✅ Full |
| 24 | Payroll | List salary structures | `GET /salary/structures` | `Payroll.vue` side card | ✅ Read only |
| 25 | Student | List students | `GET /students` | `Students.vue` | ✅ Full (paginated) |
| 26 | Student | Enroll student | `POST /students` | `Students.vue` modal | ✅ Full |
| 27 | Student | List classes | `GET /classes` | `Classes.vue` | ✅ Full |
| 28 | Notification | List logs | `GET /logs` | `Notifications.vue` | ✅ Full (detail dialog) |
| 29 | Audit | List logs | `GET /audit/logs` | `AuditLogs.vue` | ✅ Full (payload viewer) |
| 30 | Company | List companies | `GET /auth/companies` | `Companies.vue` | ✅ Full (super_admin) |
| 31 | Company | Create company | `POST /auth/companies` | `Companies.vue` modal | ✅ Full |

---

## ⚠️ Partially Covered Features

These have some UI but are missing important operations that the backend already supports.

### 1. Company Management (Auth Service)
- **What exists:** List + Create
- **Missing:**
  - `PATCH /auth/companies/{id}` — **Edit company** (name, domain) — no edit button or modal
  - `DELETE /auth/companies/{id}` — **Soft-delete company** — no delete/deactivate action
- **Suggested UI:** Add edit icon + confirm-delete dialog to `Companies.vue` table rows (same pattern as `Departments.vue`)

### 2. Salary Structures (Payroll Service)
- **What exists:** Read-only list in sidebar card
- **Missing:**
  - `POST /salary/structures` — **Create salary structure** — no create form
  - `PATCH /salary/structures/{id}` — **Edit structure** — edit button exists but has no handler
  - `DELETE /salary/structures/{id}` — **Delete structure** — no delete action
- **Suggested UI:** Dedicated `SalaryStructures.vue` page or expand the `Payroll.vue` sidebar card into a full CRUD modal with fields: `name, description, basic_pct, hra_pct, allowances_pct, pf_pct, esi_pct, professional_tax`

### 3. Leave Type Management (Leave Service)
- **What exists:** Types listed in select dropdown only
- **Missing:**
  - `POST /leave-types` — **Create leave type** — no create UI
  - `PATCH /leave-types/{id}` — **Edit leave type** — no edit UI
  - `DELETE /leave-types/{id}` — **Delete leave type** — no delete UI
- **Suggested UI:** "Leave Types" tab or section within `LeaveManagement.vue` with CRUD table. Fields: `name, description, days_allowed, requires_approval`

### 4. Leave Balance Management (Leave Service)
- **What exists:** Read-only balance cards for current user
- **Missing:**
  - `POST /leave-balances` — **Create/allocate balance** — no allocation form
  - `PATCH /leave-balances/{id}` — **Update balance** — no edit UI
  - `POST /leave-balances/bulk` — **Bulk allocate** — no bulk allocation wizard
- **Suggested UI:** "Balance Allocation" tab in `LeaveManagement.vue`. Include: employee selector, leave type, year, total days. Bulk allocation dialog for batch year-start provisioning.

### 5. Student Management (Students Service)
- **What exists:** List + Create
- **Missing:**
  - `PUT /students/{id}` — **Edit student** — no edit button or modal
  - `PATCH /students/{id}/status` — **Change enrollment status** — no status change action
  - `DELETE /students/{id}` — **Delete student** — no delete action
- **Suggested UI:** Add row action buttons (edit, change status dropdown, delete) to `Students.vue` table. Status change should be a quick-action chip dropdown (active → graduated/expelled/inactive).

### 6. Class Management (Students Service)
- **What exists:** Read-only list display
- **Missing:**
  - `POST /classes` — **Create class** — button exists but no modal/handler connected
  - `PUT /classes/{id}` — **Edit class** — edit button exists but no handler
  - `DELETE /classes/{id}` — **Delete class** — no delete action
- **Suggested UI:** Wire up create/edit modal with fields: `name, grade_level, academic_year, section`. Add delete confirm dialog.

### 7. Attendance Records Management (Attendance Service)
- **What exists:** View list + Clock in/out + Alerts
- **Missing:**
  - `POST /attendance/manual` — **Manual attendance entry** — store has `createManualEntry()` but no UI trigger
  - `PATCH /attendance/{id}` — **Edit attendance record** — store has `updateRecord()` but no UI trigger
  - `POST /attendance/school-mode` — **Mark attendance for employee** — no UI
  - `POST /attendance/school-mode/bulk` — **Bulk school-mode attendance** — no UI
- **Suggested UI:** Add "Manual Entry" button to attendance page with modal (employee selector, date, clock-in/out times). Add edit icon to table rows. Add "Mark Attendance" bulk action toolbar for school-mode.

### 8. Payslip Viewing (Payroll Service)
- **What exists:** "View payslips" button in payroll run table
- **Missing:**
  - `GET /payroll/runs/{id}/payslips` — store has `fetchPayslips()` but button handler is `console.log` only
  - `GET /payroll/my-payslips` — **Employee's own payslips** — no UI at all
- **Suggested UI:** Wire up payslip dialog showing breakdown table (basic, HRA, allowances, deductions, net). Add "My Payslips" section visible to all roles.

### 9. Audit Logs (Audit Service)
- **What exists:** List + payload viewer
- **Missing:**
  - **Filters** — Backend supports `event_type, service_source, user_id, date_from, date_to, correlation_id` but UI has no filter controls
  - `GET /audit/logs/export/csv` — **CSV export** — no export button
- **Suggested UI:** Add filter bar (event type dropdown, service dropdown, date range picker, user autocomplete). Add "Export CSV" button (super_admin only).

---

## ❌ Missing UI — High Priority

These are fully implemented backend features with **zero** UI coverage.

### 1. User Management (Auth Service)

**Backend endpoints:**
- `POST /auth/users` — Admin create user with role assignment
- `PATCH /auth/users/{user_id}/role` — Update user's RBAC role

**Backend models:** User (id, email, role, is_active, company_id)

**Impact:** Admins currently cannot create new system users or change user roles from the UI. Employee creation uses `POST /auth/register` (public endpoint) as a workaround.

**Suggested UI:**
- **Page:** `UserManagement.vue` (route: `/users`)
- **Features:**
  - DataTable listing all users (email, role, status, created_at)
  - "Create User" modal: email, password, role dropdown (SUPER_ADMIN, HR, MANAGER, EMPLOYEE), company selector
  - Inline role change: click role chip → dropdown to change role
  - User activation/deactivation toggle
- **Required fields:** email, password, role, company_id
- **Actions:** Create, Read, Update Role
- **Access:** Super Admin, Admin

---

### 2. Employee Bulk Import (Employee Service)

**Backend endpoint:**
- `POST /employees/bulk` — Bulk import employees (returns total/succeeded/failed/results)

**Impact:** HR admins must create employees one-by-one. No batch onboarding capability.

**Suggested UI:**
- **Component:** "Bulk Import" button on `Employees.vue` page
- **Features:**
  - CSV/Excel file upload with column mapping
  - Preview table showing parsed rows with validation status
  - Submit bulk create with progress indicator
  - Results summary: X succeeded, Y failed, with error details per row
- **Access:** HR, Super Admin

---

### 3. Attendance Tasks System (Attendance Service)

**Backend endpoints:**
- `POST /attendance/tasks` — Add daily task
- `GET /attendance/tasks/today` — Get today's tasks
- `PATCH /attendance/tasks/{id}` — Edit task
- `DELETE /attendance/tasks/{id}` — Delete task
- `PATCH /attendance/tasks/{id}/complete` — Mark task completion
- `POST /attendance/tasks/assign` — Assign task to another employee

**Impact:** Entire daily task tracking system is invisible. Tasks only appear as count badges in attendance history—no way to create, edit, complete, or assign tasks.

**Suggested UI:**
- **Page/Section:** "Daily Tasks" panel on `Attendance.vue` or standalone `Tasks.vue` page
- **Features:**
  - Today's task list with status indicators
  - "Add Task" form: title, details, estimated finish time, expected expenses
  - Task completion form: status dropdown, completion notes, actual expenses
  - "Assign Task" modal: target employee selector + task details
  - Task detail view with timeline
- **Required fields:** title (required), details, estimated_finish_time, expected_expenses
- **Actions:** Create, Read, Update, Delete, Complete, Assign
- **Access:** All roles (create own tasks); HR/Manager (assign to others)

---

### 4. Attendance Productivity Reports (Attendance Service)

**Backend endpoint:**
- `GET /attendance/reports/productivity` — Monthly productivity analytics per employee

**Response includes:** total_days, present_days, late_days, half_days, total_tasks, completed_tasks, completion_rate, avg_day_rating, total_task_expenses

**Impact:** Rich analytics data is available but completely hidden from admin users.

**Suggested UI:**
- **Page:** `ProductivityReports.vue` (route: `/reports/productivity`)
- **Features:**
  - Month/year selector + optional employee filter
  - Summary cards: avg completion rate, total present days, total late days
  - DataTable per employee: all productivity metrics
  - Visual charts (bar chart for attendance, pie chart for task completion rates)
  - Export to CSV/PDF
- **Access:** HR, Manager, Super Admin

---

### 5. Geofence Location Management (Attendance Service)

**Backend endpoints:**
- `POST /attendance/geofences` — Create geofence
- `GET /attendance/geofences` — List geofences
- `PATCH /attendance/geofences/{id}` — Update geofence
- `DELETE /attendance/geofences/{id}` — Delete geofence

**Impact:** Geofence validation runs on clock-in but admins cannot manage office/site locations from the UI.

**Suggested UI:**
- **Page:** `GeofenceManagement.vue` (route: `/attendance/geofences`) or section within attendance settings
- **Features:**
  - DataTable: name, lat, lng, radius, status
  - "Add Location" modal: name, latitude, longitude, radius_meters (with map picker if feasible)
  - Edit/delete actions per row
  - Visual map showing geofence circles (optional, using Leaflet/Google Maps)
- **Required fields:** name, latitude, longitude, radius_meters
- **Actions:** Full CRUD
- **Access:** HR, Super Admin

---

### 6. Attendance Policy Management (Attendance Service)

**Backend endpoints:**
- `POST /attendance/policies` — Create attendance policy
- `GET /attendance/policies` — List policies
- `PATCH /attendance/policies/{id}` — Update policy
- `DELETE /attendance/policies/{id}` — Delete policy

**Impact:** Policies control whether employees use manual, geofence, or both for attendance—currently unconfigurable from UI.

**Suggested UI:**
- **Page:** `AttendancePolicies.vue` (route: `/attendance/policies`) or tab within attendance settings
- **Features:**
  - DataTable: department/employee, method (manual/geofence/both), geofence name, work start time, hours/day
  - "Create Policy" modal: department selector OR employee selector, method dropdown, geofence selector, work_start_time, work_hours_per_day
  - Edit/delete actions
- **Required fields:** method (required), work_hours_per_day (default 8.0)
- **Actions:** Full CRUD
- **Access:** HR, Super Admin

---

### 7. Holiday Management (Leave Service)

**Backend endpoints:**
- `POST /holidays` — Create holiday
- `GET /holidays` — List holidays
- `DELETE /holidays/{id}` — Delete holiday

**Impact:** Store has `fetchHolidays()` wired up but no UI page or component uses it.

**Suggested UI:**
- **Page/Section:** "Holidays" tab within `LeaveManagement.vue` or standalone page
- **Features:**
  - DataTable: name, date, description, status
  - "Add Holiday" modal: name, date picker, description
  - Delete action per row
  - Calendar view showing holidays highlighted
- **Required fields:** name, date
- **Actions:** Create, Read, Delete
- **Access:** HR, Super Admin

---

### 8. Leave Calendar View (Leave Service)

**Backend endpoint:**
- `GET /leave-calendar` — Calendar view with staff availability per date

**Response includes:** date, staff_on_leave count, staff_available count, individual leave details

**Impact:** Powerful calendar visualization data exists but no UI consumes it.

**Suggested UI:**
- **Component:** Calendar view within `LeaveManagement.vue` or `LeaveCalendar.vue`
- **Features:**
  - Month calendar grid showing leave density per day
  - Click a date to see who's on leave vs available
  - Color-coded cells (green = full staff, yellow = some on leave, red = many on leave)
  - Date range navigation
- **Access:** HR, Manager, Super Admin

---

### 9. Employee Salary Assignment (Payroll Service)

**Backend endpoints:**
- `POST /salary/assign` — Assign salary structure + CTC to employee
- `GET /salary/employee/{id}` — Get active salary
- `GET /salary/employee/{id}/history` — Get salary history

**Impact:** Payroll runs require salary assignments, but there's no way to assign salaries or view salary history from the UI.

**Suggested UI:**
- **Component:** "Salary" tab within employee detail drawer or standalone section in Payroll page
- **Features:**
  - "Assign Salary" modal: employee selector, salary structure dropdown, CTC input, effective_from date
  - Current salary display card per employee
  - Salary history timeline table (structure, CTC, effective dates)
- **Required fields:** employee_id, salary_structure_id, ctc, effective_from
- **Actions:** Create (assign), Read (current + history)
- **Access:** HR, Super Admin

---

### 10. Guardian Management (Students Service)

**Backend endpoints:**
- `POST /guardians` — Add guardian
- `GET /guardians/{id}` — Get guardian
- `GET /guardians/student/{student_id}` — Get all guardians for a student
- `PUT /guardians/{id}` — Update guardian
- `DELETE /guardians/{id}` — Remove guardian

**Impact:** Student records are incomplete without parent/guardian contact info. Store has `fetchGuardians()` wired up but no UI.

**Suggested UI:**
- **Component:** "Guardians" section within student detail view or expandable row
- **Features:**
  - List guardians per student
  - "Add Guardian" modal: first_name, last_name, email, phone, relationship, address
  - Edit/delete actions per guardian
- **Required fields:** student_id, first_name, last_name, relationship
- **Actions:** Full CRUD
- **Access:** Admin, HR

---

### 11. Notification Preferences (Notification Service)

**Backend endpoints:**
- `GET /preferences` — Get current user's notification preferences
- `PUT /preferences` — Update preferences (email_enabled, sms_enabled)

**Impact:** Users cannot control their notification channel preferences.

**Suggested UI:**
- **Component:** Settings section or notification preferences toggle in user profile dropdown
- **Features:**
  - Toggle switches: Email notifications, SMS notifications
  - Auto-save on toggle
- **Required fields:** email_enabled, sms_enabled
- **Actions:** Read, Update
- **Access:** All roles

---

## 🟡 Missing UI — Medium Priority

### 12. Magic Link / Passwordless Login (Auth Service)

**Backend endpoints:**
- `POST /auth/magic-link` — Request magic login link
- `GET /auth/verify-magic?token={token}` — Verify magic link

**Suggested UI:** "Sign in with email link" option on Login page. Separate `VerifyMagicLink.vue` route to handle `?token=` redirect.

---

### 13. Password Reset Flow (Auth Service)

**Backend endpoints:**
- `POST /auth/forgot-password` — Initiate reset
- `POST /auth/reset-password` — Complete reset with token

**Suggested UI:** "Forgot password?" link on Login page. `ForgotPassword.vue` form (email input). `ResetPassword.vue` page (new password + confirm).

---

### 14. Token Refresh (Auth Service)

**Backend endpoint:**
- `POST /auth/refresh` — Rotate refresh token

**Suggested UI:** No visible UI needed, but `api-client.ts` should implement a 401 interceptor that automatically calls refresh before retrying the failed request. Currently it just redirects to login.

---

## 🔵 Missing UI — Low Priority

### 15. Employee Self-Service Profile (Employee Service)

**Backend endpoint:**
- `GET /employees/me` — Get own employee profile

**Suggested UI:** "My Profile" page accessible to all roles showing their own employee record in read-only or limited-edit mode.

---

### 16. Service Health Dashboards (Multiple Services)

**Backend endpoints:**
- `GET /health` (Payroll, Audit services)

**Suggested UI:** System health indicators on the admin dashboard (green/red dots per service). Only valuable for super_admin.

---

---

## 🔒 Role-Based Access Gaps

| Gap | Description | Severity |
|-----|-------------|----------|
| **No user role management UI** | Backend supports `PATCH /users/{id}/role` but there's no UI to manage user roles. Super Admin/HR cannot promote/demote users. | 🔴 Critical |
| **No admin user creation UI** | Backend has `POST /auth/users` (admin-only, with role assignment) but UI uses public `POST /auth/register` (always creates EMPLOYEE). New admins/HR/managers cannot be created. | 🔴 Critical |
| **Employee page lacks role restrictions** | The Employees page is visible to all authenticated users, but Create/Edit/Deactivate actions should be conditionally hidden for non-HR/non-admin roles. | 🟡 Medium |
| **Attendance edit actions unprotected** | Manual entry and record editing should only be visible to HR/Super Admin in the UI. Currently not exposed, but when added, must be role-gated. | 🟡 Medium |
| **Leave approval lacks role check** | Approve/Reject buttons show for all users, but backend restricts to HR/Manager/Super Admin. UI should hide these for EMPLOYEE role. | 🟡 Medium |
| **Payroll page fully visible** | Salary structures and payroll runs should be read-only for HR, full access for Super Admin. No differentiation currently. | 🟢 Low |
| **Missing MANAGER role in sidebar** | Sidebar role labels cover `super_admin`, `admin`, `hr` but MANAGER role (which backend supports) has no specific nav group or access rules. | 🟡 Medium |
| **Audit CSV export needs super_admin gate** | When export button is added, it must be restricted to super_admin per backend authorization. | 🟡 Medium |

---

## 💡 UX Improvements

### Navigation & Layout
1. **Add breadcrumb page titles** — DashboardLayout has breadcrumbs but child pages don't emit their titles to the route meta
2. **Add global search** — Search icon in AppBar is non-functional. Implement command-palette (Ctrl+K) searching across employees, students, departments
3. **Add loading skeleton states** — Replace raw spinners with skeleton loaders on dashboard KPI cards and tables during initial load
4. **Mobile responsive sidebar** — Sidebar should auto-collapse to rail mode on smaller screens

### Data Tables
5. **Add advanced filters** — Most DataTables lack filter controls. Key filters needed:
   - Employees: department, status, date joined range
   - Attendance: employee, date range, status
   - Leave requests: status, leave type, date range
   - Audit logs: event type, service, date range, user
6. **Add column sorting** — DataTable supports it but most pages don't define sortable columns
7. **Add row selection + bulk actions** — Select multiple rows for bulk delete, bulk status change, bulk export
8. **Add data export** — "Export CSV" button on major tables (employees, attendance, payroll runs, students)

### Forms & Interactions
9. **Leave request form needs auto-calculate** — `total_days` should auto-calculate from start_date/end_date instead of requiring manual entry
10. **Leave request employee_id** — Currently requires manual ID input. Should auto-fill with current user's employee_id or provide employee selector for HR
11. **Payslip viewer** — The "view payslips" button does `console.log()`. Wire up the actual payslip dialog
12. **Confirmation toasts on destructive actions** — Some delete actions lack success confirmation feedback

### Dashboard
13. **Role-specific dashboard widgets** — Super Admin should see multi-company stats; HR should see team-specific pending actions; Employee role needs self-service view
14. **Add trend indicators** — KPI cards show counts but no trend (up/down vs. previous period)
15. **Recent activity should be real-time** — Consider polling or WebSocket for live audit feed

---

## 🧱 Missing Reusable Components

| Component | Description | Where Needed |
|-----------|-------------|--------------|
| **`FilterBar.vue`** | Composable filter bar with dropdowns, date range pickers, and search input that emits filter params | Audit Logs, Attendance, Leave, Employees, Students |
| **`ConfirmDialog.vue`** | Generic confirmation dialog (title, message, confirm/cancel) to replace per-page dialog duplication | Companies, Students, Classes, Holidays, Geofences |
| **`StatusChip.vue`** | Standardized status chip with color mapping (active/inactive, approved/pending/rejected, etc.) | All list pages — currently each page duplicates status color logic |
| **`UserAvatar.vue`** | User avatar with initials fallback, role badge, and tooltip | Sidebar, AppBar, Employee list, Audit logs actor column |
| **`CalendarView.vue`** | Monthly calendar grid component for date-based data visualization | Leave Calendar, Holiday Calendar, Attendance overview |
| **`FileUpload.vue`** | Drag-and-drop file upload with preview and validation | Bulk employee import, leave supporting documents, student documents |
| **`StatCard.vue`** | Reusable KPI stat card (title, value, icon, color, trend) | Dashboard — currently duplicated 5+ times |
| **`DetailDrawer.vue`** | Generic side-drawer for entity detail view (currently only exists for Employee) | Students, Attendance Records, Leave Requests, Payslips |
| **`TabLayout.vue`** | Tabbed content layout for pages with multiple sections | Leave (Requests/Types/Balances/Holidays), Payroll (Runs/Structures/Salary Assignment), Attendance (Records/Tasks/Policies/Geofences) |
| **`EmptyState.vue`** | Illustrated empty state placeholder for tables/lists with no data | All DataTable instances |

---

## 📊 Summary Matrix

### Backend Feature Coverage by Service

| Service | Total Endpoints | UI Covered | Partially Covered | No UI | Coverage % |
|---------|:-:|:-:|:-:|:-:|:-:|
| **Auth** | 13 | 5 | 1 | 7 | **38%** |
| **Employee** | 7 | 5 | 0 | 2 | **71%** |
| **Attendance** | 19 | 5 | 2 | 12 | **26%** |
| **Leave** | 11 | 5 | 2 | 4 | **45%** |
| **Payroll** | 9 | 3 | 2 | 4 | **33%** |
| **Notification** | 2 | 1 | 0 | 1 | **50%** |
| **Students** | 11 | 3 | 2 | 6 | **27%** |
| **Audit** | 3 | 1 | 1 | 1 | **33%** |
| **TOTAL** | **75** | **28** | **10** | **37** | **37%** |

### Priority Breakdown

| Priority | Count | Key Items |
|----------|:-----:|-----------|
| 🔴 **High** | 11 | User Management, Bulk Import, Tasks, Productivity Reports, Geofences, Policies, Holidays, Leave Calendar, Salary Assignment, Guardians, Notification Preferences |
| 🟡 **Medium** | 3 | Magic Link, Password Reset, Token Refresh |
| 🟢 **Low** | 2 | Employee Self-Service Profile, Service Health |
| ⚠️ **Partial** | 9 | Companies CRUD, Salary Structures CRUD, Leave Types CRUD, Leave Balances, Students CRUD, Classes CRUD, Attendance Manual/Edit, Payslips, Audit Filters/Export |

### Recommended Implementation Order

1. **User Management Page** — Unblocks admin/HR user creation (critical gap)
2. **Complete existing CRUD** — Wire up missing edit/delete on Companies, Students, Classes, Salary Structures, Leave Types
3. **Attendance Tasks UI** — Large feature with dedicated endpoints sitting unused
4. **Salary Assignment** — Required for payroll runs to function correctly
5. **Holiday Management** — Simple CRUD, high visibility for HR
6. **Leave Calendar** — High-value visualization for HR planning
7. **Geofence & Policy Management** — Required for location-based attendance
8. **Productivity Reports** — Analytics dashboard value-add
9. **Password Reset & Magic Link** — Login convenience features
10. **Bulk Import & Guardian Management** — Efficiency features for scale
11. **Notification Preferences** — User self-service feature

---

*This audit covers only UI gaps for existing backend functionality. No new backend features were recommended.*
