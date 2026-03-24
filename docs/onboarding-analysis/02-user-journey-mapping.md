# 02 — First-Time User Journey Mapping

## Persona: First Super Admin (Company Owner / IT Admin)

This is the person who deploys OphilliaHRMS and needs to set up their organization.

---

## Journey Map

### Stage 1: Deployment (Pre-UI)

| Step | Action | Experience | Emotion |
|------|--------|------------|---------|
| 1 | Clone repo, run `docker-compose up` | Watches containers build and start | Neutral |
| 2 | Wait for health checks to pass | ~60-90 seconds for all services | Impatient |
| 3 | Visit `http://localhost` | Sees login page | Curious |
| 4 | **Stuck** — no credentials exist | Cannot log in. No signup button. No guidance. | Confused |
| 5 | Read docs / README to find `seed_user.py` | Must find CLI command to create first user | Frustrated |
| 6 | Run `docker exec hrms-auth python seed_user.py ...` | Creates admin + company from terminal | Technical barrier |

**UX Gap:** The user must leave the browser, open a terminal, and run a CLI command before they can even see the application. There is no self-service registration or first-run setup wizard.

---

### Stage 2: First Login

| Step | Action | What They See | Issues |
|------|--------|---------------|--------|
| 7 | Enter email + password on login page | Clean login form with email/password fields | None — works well |
| 8 | Submit login | Loading state, then redirect | Quick, ~1-2s |
| 9 | System calls `/auth/post-login-context` | Invisible to user | None |
| 10 | Redirected to dashboard | Dashboard with KPI cards showing all zeros | Anticlimactic |

**UX Gap:** The user lands on a dashboard with 0 Employees, 0 Departments, 0 Leave Requests. No welcome message, no getting-started guide, no setup checklist.

---

### Stage 3: First Actions (Unguided)

The user must figure out on their own what to do next:

| Step | Action | Friction |
|------|--------|----------|
| 11 | Click sidebar → Departments | Empty list, no guidance |
| 12 | Create first department manually | Must figure out form fields |
| 13 | Click sidebar → Employees | Empty list |
| 14 | Create first employee | Long form (52 fields), no defaults |
| 15 | Click sidebar → Leave | No leave types exist |
| 16 | Must create leave types before any leave can be requested | Not obvious |
| 17 | Click sidebar → Payroll | No salary structures exist |
| 18 | Must create salary structure before payroll works | Not obvious |
| 19 | Click sidebar → Attendance → Policies | No policies, no geofences |
| 20 | Must set up geofences before geofence attendance works | Not obvious |

**UX Gap:** The user has to discover the correct setup order by trial and error. The implicit dependency chain is:

```
Company → Departments → Employees → Leave Types → Leave Balances
                                   → Salary Structures → Employee Salaries
                                   → Geofences → Attendance Policies
```

None of this is communicated to the user.

---

## Journey Map: Non-Admin User (HR / Manager / Employee)

| Step | Action | Experience |
|------|--------|------------|
| 1 | Receive credentials from admin | Out of band (email, Slack, etc.) |
| 2 | Visit login page | Standard login form |
| 3 | Log in | Redirected to dashboard |
| 4 | See dashboard | May see data if admin has set things up |

**UX Gap:** No self-registration. No invite flow. No welcome email. Admin must create users and communicate credentials manually.

---

## Journey Map: SaaS Self-Signup (If No Company Exists)

This flow triggers when a super_admin user has 0 companies:

| Step | Action | What They See |
|------|--------|---------------|
| 1 | Log in | Login form |
| 2 | `/auth/post-login-context` returns `CREATE_COMPANY` | Invisible |
| 3 | Redirected to `/create-company` | Simple form: Company Name + Domain |
| 4 | Fill in company name | Minimal form, no guidance |
| 5 | Submit | Company created, redirect to dashboard |
| 6 | Dashboard | Empty — same as Stage 2 above |

**UX Gap:** The company creation form collects only `name` and `domain`. No industry, timezone, country, logo, employee count range, or any other useful onboarding data.

---

## What's Missing from the User's Perspective

### No Welcome Experience
- No "Welcome to OphilliaHRMS!" screen
- No explanation of what the system does
- No tour or feature highlights

### No Setup Checklist
- No visible progress bar
- No "Complete these 5 steps to get started"
- No indication of what's required vs. optional

### No Smart Defaults
- No default leave types (Sick Leave, Casual Leave, etc.)
- No default salary structure templates
- No sample department or employee
- No default holiday calendar

### No Invite System
- Can't invite team members by email
- No invite links
- No bulk user import
- Admin must create users one by one via User Management

### No Contextual Help
- No tooltips explaining fields
- No "What is this?" links
- No documentation links from within the app
- No empty state illustrations with calls to action

### No Resume Capability
- If the user closes the browser mid-setup, there's no way to resume
- No onboarding state is persisted
- No "Continue setup" prompt on next login

---

## Emotional Journey Graph

```
Excitement  ████████░░░░░░░░░░░░░░░░░░░░░░
            "New HRMS! Let's try it"

Confusion   ░░░░░░░░████████░░░░░░░░░░░░░░
            "How do I log in? No signup?"

Frustration ░░░░░░░░░░░░░░░░████████░░░░░░
            "CLI command? Empty dashboard?"

Resignation ░░░░░░░░░░░░░░░░░░░░░░░░████████
            "I guess I'll manually create everything..."
```

The current onboarding is a **cliff drop** in user experience — from excitement to frustration in under 5 minutes.

---

## Screen-by-Screen Breakdown

### Login Page (`/login`)
- **What exists:** Email/password form, magic link toggle, forgot password link
- **What's missing:** Signup/register option, social login, "New here?" prompt

### Create Company (`/create-company`)
- **What exists:** Company name + domain form
- **What's missing:** Logo upload, industry selector, timezone, employee count, guided wizard steps

### Select Company (`/select-company`)
- **What exists:** Company list with name/domain and selection
- **What's missing:** Company avatars, last-accessed indicator, search/filter for many companies

### Dashboard (`/`)
- **What exists:** KPI cards, quick actions, system status, audit logs
- **What's missing:** Onboarding checklist, getting-started widget, empty state guidance, setup progress
