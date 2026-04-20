<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ChevronDown, ChevronRight, ExternalLink, CheckCircle2, Circle, AlertCircle } from 'lucide-vue-next'

const emit = defineEmits<{ (e: 'navigate', tab: string): void }>()

interface Block {
  heading?: string
  note?: string
  warn?: string
  bullets?: string[]
  numbered?: string[]
  text?: string
}

interface Section {
  id: string
  title: string
  badge?: string
  badgeColor?: string
  tab?: string
  content: Block[]
}

const sections: Section[] = [
  {
    id: 'overview',
    title: 'Before You Begin — Setup Overview',
    badge: 'Start Here',
    badgeColor: 'bg-indigo-600 text-white',
    content: [
      {
        text: 'Follow this checklist in order. Each step depends on the one before it. Estimated first-time setup time: 30–60 minutes.',
      },
      {
        heading: 'Full Setup Checklist',
        numbered: [
          'HR Setup — Departments, Branches, Designations, Employment Types, Grades, Groups',
          'Shift Locations (Geofencing) — office addresses with GPS coordinates and radius',
          'Shift Types — named shift patterns with start/end times and break duration',
          'Add Employees — individual or bulk CSV import',
          'Shift Assignments — assign each employee to a shift type',
          'Leave Types — categories like Annual Leave, Sick Leave, Casual Leave',
          'Leave Periods — annual calendar (e.g. Jan–Dec 2025)',
          'Holiday Lists — public and company holidays for the year',
          'Leave Policies — rules: max days, carry-forward, accrual schedule',
          'Leave Policy Assignments — assign policies to employees or groups',
          'Leave Allocations — grant each employee their annual entitlement',
          'Overtime Policies — thresholds and pay multipliers (if applicable)',
          'Salary Structures — component percentages for payroll calculation',
        ],
      },
      {
        note: 'You can start tracking attendance as soon as Steps 1–5 are complete. Leave and Payroll require Steps 6–13.',
      },
    ],
  },

  {
    id: 'hr-setup',
    title: 'Step 1 — HR Setup (Core Structure)',
    badge: 'Required first',
    badgeColor: 'bg-rose-100 text-rose-700',
    tab: 'departments',
    content: [
      {
        text: 'These are the building blocks for all employee records. Complete all six before adding any employees.',
      },
      {
        heading: 'Departments',
        numbered: [
          'Go to HR Setup → Departments.',
          'Click "Add Department". Enter the department name (e.g. Engineering, Finance, HR, Operations).',
          'Optionally assign a parent department for nested org structures.',
          'Save. Repeat for all departments.',
        ],
      },
      {
        heading: 'Branches',
        numbered: [
          'Go to HR Setup → Branches.',
          'Click "Add Branch". Enter the branch name and city/location.',
          'Add all office locations, remote sites, or regional branches your company operates.',
        ],
      },
      {
        heading: 'Designations',
        numbered: [
          'Go to HR Setup → Designations.',
          'Add every job title used in your organisation (e.g. Software Engineer, Team Lead, Product Manager).',
          'These appear as a dropdown when creating employee profiles.',
        ],
      },
      {
        heading: 'Employment Types',
        numbered: [
          'Go to HR Setup → Employment Types.',
          'Add types relevant to your workforce: Full-Time, Part-Time, Contract, Intern, Consultant.',
        ],
      },
      {
        heading: 'Employee Grades',
        numbered: [
          'Go to HR Setup → Employee Grades.',
          'Define compensation bands (e.g. L1, L2, L3 — or Junior, Mid, Senior, Lead).',
          'Grades are used for payroll structure assignment and leave policy differentiation.',
        ],
      },
      {
        heading: 'Employee Groups',
        numbered: [
          'Go to HR Setup → Employee Groups.',
          'Create logical groupings for leave policy assignment (e.g. "Management", "Field Staff", "Remote Workers").',
          'Groups let you assign policies to many employees at once instead of one by one.',
        ],
      },
    ],
  },

  {
    id: 'geofencing',
    title: 'Step 2 — Shift Locations & Geofencing',
    badge: 'Enables attendance tracking',
    badgeColor: 'bg-violet-100 text-violet-700',
    tab: 'shift-locations',
    content: [
      {
        text: 'Shift Locations define physical or virtual work sites. Each location has GPS coordinates and a radius — the geofence. Employees can only check in if their device is within this perimeter.',
      },
      {
        heading: 'Creating a Shift Location',
        numbered: [
          'Go to Shifts → Shift Locations.',
          'Click "Sync Hub" to add a new location.',
          'Enter the Hub Designation (e.g. "Headquarters North", "Mumbai Branch", "Remote").',
          'Enter the Logistics Address — the building entrance or full address.',
          'Enter the Latitudinal Point and Longitudinal Point (GPS coordinates).',
          'To get coordinates: open Google Maps, right-click on the building entrance, and copy the lat/lng shown.',
          'Set the Radial Perimeter in metres — the allowable check-in radius. Start with 100m for offices, 500m for campuses.',
          'Save. Create one location per physical office or remote site.',
        ],
      },
      {
        note: 'For remote/work-from-home employees, you can create a special "Remote" location with a very large radius (e.g. 50,000m) or disable geofencing for that shift type.',
      },
      {
        warn: 'Incorrect GPS coordinates are the most common setup mistake. Always verify by dropping a pin on the exact building entrance in Google Maps — not the road or parking lot.',
      },
      {
        heading: 'Recommended Radius by Site Type',
        bullets: [
          'Small office (single floor/building): 50–100 m',
          'Large campus or business park: 200–500 m',
          'Construction site or field work: 500–2000 m',
          'Work from home / fully remote: 50,000 m (or use a dedicated remote shift type)',
        ],
      },
    ],
  },

  {
    id: 'shift-types',
    title: 'Step 3 — Shift Types',
    badge: 'Required for attendance',
    badgeColor: 'bg-cyan-100 text-cyan-700',
    tab: 'shift-types',
    content: [
      {
        text: 'Shift Types define the working hours pattern. Each shift has a name, start time, end time, break duration, and grace period.',
      },
      {
        heading: 'Creating a Shift Type',
        numbered: [
          'Go to Shifts → Shift Types.',
          'Click "New Shift Type".',
          'Enter a Name (e.g. "Morning 9–6", "Night 10pm–6am", "Flexible").',
          'Set Start Time and End Time using 24-hour format.',
          'Set Break Minutes — the unpaid break duration deducted from work hours.',
          'Set Grace Period Minutes — extra minutes after shift start before a "late" mark is applied. Recommended: 5–15 min.',
          'Toggle Night Shift if the shift crosses midnight (required for correct overtime calculations).',
          'Save. Create one shift type per distinct working hours pattern.',
        ],
      },
      {
        heading: 'Common Shift Patterns',
        bullets: [
          'General Shift: 09:00–18:00, 60 min break, 10 min grace',
          'Morning Shift: 06:00–14:00, 30 min break, 5 min grace',
          'Afternoon Shift: 14:00–22:00, 30 min break, 5 min grace',
          'Night Shift: 22:00–06:00, 30 min break, 5 min grace, Night Shift = ON',
          'Flexible: set start/end to working day boundaries and use a wide grace period',
        ],
      },
    ],
  },

  {
    id: 'employees',
    title: 'Step 4 — Adding Employees',
    badge: 'Required',
    badgeColor: 'bg-blue-100 text-blue-700',
    tab: 'employees',
    content: [
      {
        heading: 'Add Employees One by One',
        numbered: [
          'Go to Employees → Employee Directory.',
          'Click "Add Employee".',
          'Personal tab: first name, last name, date of birth, gender, phone, personal email.',
          'Employment tab: department, branch, designation, employment type, grade, joining date.',
          'Save — an invitation email is sent to the employee.',
        ],
      },
      {
        heading: 'Bulk Import (Recommended for 10+ employees)',
        numbered: [
          'Go to Employees → Bulk Import.',
          'Click "Download Template" to get the CSV format.',
          'Open in Excel or Google Sheets. Fill one employee per row — required fields are marked with *.',
          'Required columns: first_name, last_name, email, department_name, branch_name, designation_name, employment_type_name, joining_date.',
          'Save as CSV (comma-separated). Upload the file.',
          'The system validates each row. Errors are shown inline — fix and re-upload.',
          'Monitor the import queue — each row shows Queued → Processing → Success / Failed.',
        ],
      },
      {
        note: 'Department, Branch, Designation, and Employment Type must match exactly what you created in HR Setup. Spelling differences will cause row failures.',
      },
    ],
  },

  {
    id: 'shift-assignments',
    title: 'Step 5 — Shift Assignments',
    badge: 'Required for attendance',
    badgeColor: 'bg-cyan-100 text-cyan-700',
    tab: 'shift-assignments',
    content: [
      {
        text: 'Assign each employee a shift type and location. Without an assignment the attendance system cannot calculate work hours, late arrivals, or overtime.',
      },
      {
        heading: 'Assigning Shifts',
        numbered: [
          'Go to Shifts → Shift Assignments.',
          'Click "New Assignment".',
          'Select the Employee.',
          'Select the Shift Type (created in Step 3).',
          'Select the Shift Location (geofenced site from Step 2).',
          'Set the Effective From date. Optionally set an Effective To end date for temporary assignments.',
          'Save.',
        ],
      },
      {
        note: 'An employee can only have one active shift assignment at a time. To change a shift, create a new assignment with a later start date — the previous one expires automatically.',
      },
      {
        heading: 'Viewing the Roster',
        bullets: [
          'Go to Shifts → Roster for a weekly calendar view of all shift assignments.',
          'Shifts → Shift Schedules shows a timeline view by employee.',
        ],
      },
    ],
  },

  {
    id: 'attendance',
    title: 'Attendance — Day-to-Day Operations',
    tab: 'attendance-records',
    content: [
      {
        heading: 'How Check-ins Work',
        bullets: [
          'Employees check in via the mobile app. The app verifies their GPS location against the assigned shift location geofence.',
          'If outside the geofence, the check-in is flagged as "Out of Perimeter".',
          'Check-in time is compared to shift start time to determine Present / Late / Absent.',
          'Check-out time determines total work hours and overtime.',
        ],
      },
      {
        heading: 'Reviewing Attendance Records',
        numbered: [
          'Go to Attendance → Attendance Records.',
          'Filter by date range and employee. Each row shows: clock-in, clock-out, work hours, overtime hours, status.',
          'Status values: Present (on time), Late (after grace period), Absent, On Leave, Holiday.',
        ],
      },
      {
        heading: 'Attendance Adjustments',
        numbered: [
          'An employee submits an adjustment request when they forgot to check in/out or were incorrectly marked absent.',
          'Go to Attendance → Attendance Adjustments to review pending requests.',
          'Click the review icon (✓) on a row to Approve or Reject with a note.',
          'For bulk approvals: tick the checkbox next to multiple rows, then click "Approve All".',
        ],
      },
      {
        heading: 'Importing from Biometric Devices',
        numbered: [
          'Export attendance data from your fingerprint/card device as a CSV.',
          'Go to Attendance → Import from Biometric. Upload the file.',
          'The system matches records by employee ID and date, filling in any missed check-ins.',
        ],
      },
      {
        heading: 'Holiday Calendars',
        numbered: [
          'Go to Attendance → Holiday Calendars to create calendars for each branch or region.',
          'Add holidays by date — these dates are automatically excluded from "Absent" calculations.',
        ],
      },
    ],
  },

  {
    id: 'leave-setup',
    title: 'Step 6–11 — Leave Management Setup',
    badge: 'Do in order',
    badgeColor: 'bg-emerald-100 text-emerald-700',
    tab: 'leave-types',
    content: [
      {
        heading: 'Step 6 — Leave Types',
        numbered: [
          'Go to Leave → Leave Types. Click "Add Leave Type".',
          'Enter the name (Annual Leave, Sick Leave, Casual Leave, Maternity Leave, etc.).',
          'Set Days Allowed Per Year — the maximum entitlement.',
          'Toggle "Requires Manager Approval" on for types needing HR sign-off.',
          'Save. Create one type per leave category.',
        ],
      },
      {
        heading: 'Step 7 — Leave Periods',
        numbered: [
          'Go to Leave → Leave Periods. Click "New Period".',
          'Set the period name (e.g. "FY 2025"), start date (01-Jan-2025), and end date (31-Dec-2025).',
          'Save. This is the container that all allocations and transactions belong to.',
        ],
      },
      {
        heading: 'Step 8 — Holiday Lists',
        numbered: [
          'Go to Leave → Holiday Lists. Click "New List".',
          'Name it (e.g. "National Holidays 2025"). Set valid-from and valid-to dates covering the leave period.',
          'Save, then click the + icon on the row to add individual holiday entries (date + description).',
          'Add every public holiday and any company-specific paid holidays.',
        ],
      },
      {
        heading: 'Step 9 — Leave Policies',
        numbered: [
          'Go to Leave → Leave Policies. Click "New Policy".',
          'Set the policy name, maximum consecutive leave days, and carry-forward rules.',
          'Link the holiday list created in Step 8.',
          'Configure accrual: Monthly, Quarterly, or Annual.',
          'Save. Create separate policies for different employee groups if rules differ (e.g. Management vs Field Staff).',
        ],
      },
      {
        heading: 'Step 10 — Policy Assignments',
        numbered: [
          'Go to Leave → Policy Assignments. Click "New Assignment".',
          'Select the employee (or employee group) and the policy from Step 9.',
          'Set the effective date.',
          'Save. Every employee must have at least one active policy assignment.',
        ],
      },
      {
        heading: 'Step 11 — Leave Allocations',
        numbered: [
          'Go to Leave → Leave Allocations. Click "New Allocation".',
          'Select the employee, leave type, and leave period.',
          'Enter the New Leaves Allocated (from the leave type entitlement) and any Carry Forward Days from the previous year.',
          'Save. The system calculates Total Leaves Allocated = new + carry-forward.',
          'Repeat for every employee × every leave type they are entitled to.',
        ],
      },
      {
        note: 'After completing Steps 6–11, employees can submit leave requests from their portal. You can monitor balances at Leave → Leave Balances.',
      },
    ],
  },

  {
    id: 'overtime',
    title: 'Step 12 — Overtime Policies (Optional)',
    tab: 'ot-policies',
    content: [
      {
        text: 'Skip this section if your organisation does not pay overtime. If you do, configure policies before the first payroll run.',
      },
      {
        heading: 'Creating an Overtime Policy',
        numbered: [
          'Go to Overtime → Overtime Policies. Click "New Policy".',
          'Choose a compliance template if applicable (India Factories Act: 2× after 9h/day; EU WTD: 1.25× after 10h/day) or configure manually.',
          'Set Daily OT After (h) — work hours after which overtime pay starts (e.g. 9).',
          'Set Weekly OT After (h) — total weekly hours threshold (e.g. 48).',
          'Set Daily OT Rate (×) — pay multiplier, e.g. 1.5 or 2.0.',
          'Set Grace Minutes — extra minutes after shift end before OT counting starts (e.g. 15).',
          'Set scope: Company-wide, a specific Department, or an individual Employee.',
          'Save.',
        ],
      },
      {
        heading: 'Overtime Approval Flow',
        bullets: [
          'Employees submit overtime requests before or after working extra hours.',
          'HR reviews at Overtime → Overtime Requests.',
          'Approved overtime is aggregated in Overtime → Overtime Records for payroll processing.',
          'View monthly reports at Overtime → Overtime Reports.',
        ],
      },
    ],
  },

  {
    id: 'payroll-setup',
    title: 'Step 13 — Payroll Setup',
    tab: 'payroll',
    content: [
      {
        heading: 'Salary Structures',
        numbered: [
          'Go to Payroll → Settings → Salary Structures.',
          'Click "New Structure". Enter a name (e.g. "Standard CTC Structure").',
          'Set the component percentages:',
          '  • Basic % — percentage of CTC as basic salary. Typically 40–50%. This drives PF and HRA calculations.',
          '  • HRA % — House Rent Allowance as % of basic. Typically 40–50%.',
          '  • Allowances % — special allowances.',
          '  • PF % — Provident Fund contribution (employer + employee). India: 12% each.',
          '  • ESI % — Employee State Insurance. India: 3.25% employer, 0.75% employee.',
          'Save. Create separate structures for different salary bands or designations.',
          'Assign a structure to each employee from their employment profile.',
        ],
      },
      {
        heading: 'Tax Profiles',
        numbered: [
          'Go to Payroll → Settings → Tax Profiles.',
          'Create a tax profile for each tax regime applicable to your employees.',
          'Set TDS slab rates, standard deduction, and exemptions.',
          'Assign to employees from their profile.',
        ],
      },
      {
        heading: 'Running Your First Payroll',
        numbered: [
          'Go to Payroll. Click "New Payroll Run".',
          'Select the month and confirm the employee list.',
          'The system auto-calculates gross, all deductions, and net pay.',
          'Review the run — check for anomalies (unusually high/low figures).',
          'Click "Finalise" to lock the payroll. Payslips become available for download.',
        ],
      },
      {
        note: 'Every employee must have a Salary Structure and Tax Profile assigned before running payroll. Employees without these are excluded from the run.',
      },
    ],
  },

  {
    id: 'leave-operations',
    title: 'Leave — Day-to-Day Operations',
    tab: 'leave-allocations',
    content: [
      {
        heading: 'Viewing Balances',
        bullets: [
          'Leave → Leave Balances — grid of remaining balance per employee per leave type.',
          'Colour coding: green = ≥50% remaining, amber = 20–49%, red = <20%.',
          'Use the employee search filter to find a specific person quickly.',
        ],
      },
      {
        heading: 'Leave Block Lists',
        bullets: [
          'Block Lists prevent employees from taking leave during critical periods (e.g. year-end close, product launches).',
          'Go to Leave → Leave Block Lists. Set the blocked date range and which employee group it applies to.',
        ],
      },
      {
        heading: 'Compensatory Leave',
        bullets: [
          'When an employee works on a holiday or week-off, they earn compensatory leave.',
          'Go to Leave → Compensatory Leave to review and approve comp-off grants.',
        ],
      },
      {
        heading: 'Leave Encashment',
        bullets: [
          'Employees can request unused leave be converted to cash at year-end.',
          'Go to Leave → Leave Encashment to process encashment requests.',
        ],
      },
    ],
  },

  {
    id: 'workspace',
    title: 'Workspace — Team Collaboration',
    tab: 'workspace-hub',
    content: [
      {
        bullets: [
          'Team Hub — activity feed, quick links, and announcements for the HR team.',
          'Calendar — shared calendar showing approved leaves, public holidays, and team events.',
          'Task Board — Kanban board for HR project tasks (onboarding checklists, policy reviews, etc.).',
          'Notes — shared knowledge base for HR policies, FAQs, and SOPs.',
          'Settings — configure workspace notifications and integrations.',
        ],
      },
    ],
  },

  {
    id: 'permissions',
    title: 'Role Permissions Reference',
    content: [
      { text: 'What each role can do:' },
    ],
  },
]

const permissionMatrix = [
  { feature: 'View Dashboard',               admin: true,  hr: true,  employee: false },
  { feature: 'HR Setup (Depts, Branches…)',  admin: true,  hr: true,  employee: false },
  { feature: 'Add / Edit Employees',         admin: true,  hr: true,  employee: false },
  { feature: 'Delete Employees',             admin: true,  hr: false, employee: false },
  { feature: 'Bulk Import Employees',        admin: true,  hr: true,  employee: false },
  { feature: 'Manage Shift Types/Locations', admin: true,  hr: true,  employee: false },
  { feature: 'Assign Shifts to Employees',   admin: true,  hr: true,  employee: false },
  { feature: 'View Attendance Records',      admin: true,  hr: true,  employee: false },
  { feature: 'Approve Attendance Requests',  admin: true,  hr: true,  employee: false },
  { feature: 'Submit Attendance Request',    admin: true,  hr: true,  employee: true  },
  { feature: 'Manage Leave Types/Periods',   admin: true,  hr: true,  employee: false },
  { feature: 'Manage Leave Policies',        admin: true,  hr: true,  employee: false },
  { feature: 'Approve Leave Requests',       admin: true,  hr: true,  employee: false },
  { feature: 'View Own Leave Balance',       admin: true,  hr: true,  employee: true  },
  { feature: 'Manage Overtime Policies',     admin: true,  hr: false, employee: false },
  { feature: 'Approve Overtime Requests',    admin: true,  hr: true,  employee: false },
  { feature: 'View Payroll',                 admin: true,  hr: true,  employee: false },
  { feature: 'Run Payroll',                  admin: true,  hr: false, employee: false },
  { feature: 'Manage Salary Structures',     admin: true,  hr: false, employee: false },
  { feature: 'View Own Profile & Payslips',  admin: true,  hr: true,  employee: true  },
]

const open = ref<Set<string>>(new Set(['overview']))
const activeId = ref('overview')

function toggle(id: string) {
  if (open.value.has(id)) open.value.delete(id)
  else open.value.add(id)
}

function scrollTo(id: string) {
  open.value.add(id)
  activeId.value = id
  nextTick(() => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function goTo(tab?: string) {
  if (tab) emit('navigate', tab)
}

const setupSteps = [
  { id: 'hr-setup',         label: '1. HR Setup',          tab: 'departments'     },
  { id: 'geofencing',       label: '2. Shift Locations',   tab: 'shift-locations' },
  { id: 'shift-types',      label: '3. Shift Types',       tab: 'shift-types'     },
  { id: 'employees',        label: '4. Add Employees',     tab: 'employees'       },
  { id: 'shift-assignments',label: '5. Shift Assignments', tab: 'shift-assignments'},
  { id: 'leave-setup',      label: '6–11. Leave Setup',    tab: 'leave-types'     },
  { id: 'overtime',         label: '12. Overtime',         tab: 'ot-policies'     },
  { id: 'payroll-setup',    label: '13. Payroll Setup',    tab: 'payroll'         },
]
</script>

<template>
  <div class="flex gap-8 min-h-0">
    <!-- TOC -->
    <aside class="w-56 shrink-0 sticky top-0 self-start space-y-4">
      <div>
        <p class="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400 mb-2">Setup Steps</p>
        <nav class="space-y-0.5">
          <button
            v-for="step in setupSteps"
            :key="step.id"
            @click="scrollTo(step.id)"
            :class="[
              'w-full text-left px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-colors',
              activeId === step.id
                ? 'bg-indigo-600 text-white'
                : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
            ]"
          >
            {{ step.label }}
          </button>
        </nav>
      </div>

      <div>
        <p class="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400 mb-2">Operations</p>
        <nav class="space-y-0.5">
          <button
            v-for="s in sections.filter(s => !setupSteps.find(st => st.id === s.id) && s.id !== 'overview')"
            :key="s.id"
            @click="scrollTo(s.id)"
            :class="[
              'w-full text-left px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-colors',
              activeId === s.id
                ? 'bg-slate-900 text-white'
                : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
            ]"
          >
            {{ s.title.replace(/Step \d+[\–\d]* — /, '').replace(/\(.*\)/, '').trim() }}
          </button>
        </nav>
      </div>

      <div class="pt-2 border-t border-slate-100">
        <p class="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400 mb-2">Shortcuts</p>
        <div class="space-y-1 text-[10px] text-slate-500">
          <div class="flex justify-between"><span>Jump anywhere</span><kbd class="bg-slate-100 px-1.5 rounded font-mono text-[9px]">⌘K</kbd></div>
          <div class="flex justify-between"><span>Close drawer</span><kbd class="bg-slate-100 px-1.5 rounded font-mono text-[9px]">Esc</kbd></div>
        </div>
      </div>
    </aside>

    <!-- Content -->
    <div class="flex-1 space-y-3 pb-16 max-w-3xl">
      <div
        v-for="s in sections"
        :key="s.id"
        :id="s.id"
        class="bg-white border border-slate-200 rounded-2xl overflow-hidden"
      >
        <!-- Section header -->
        <button
          @click="toggle(s.id)"
          class="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 transition-colors text-left"
        >
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <span class="font-bold text-sm text-slate-900">{{ s.title }}</span>
            <span v-if="s.badge" :class="['text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full shrink-0', s.badgeColor]">
              {{ s.badge }}
            </span>
          </div>
          <div class="flex items-center gap-3 ml-3 shrink-0">
            <button
              v-if="s.tab"
              @click.stop="goTo(s.tab)"
              class="flex items-center gap-1 text-[10px] font-bold text-indigo-600 hover:text-indigo-700 uppercase tracking-widest"
            >
              Go there <ExternalLink class="w-3 h-3" />
            </button>
            <component :is="open.has(s.id) ? ChevronDown : ChevronRight" class="w-4 h-4 text-slate-400" />
          </div>
        </button>

        <!-- Section body -->
        <div v-if="open.has(s.id)" class="px-6 pb-6 border-t border-slate-100 pt-5 space-y-5">

          <!-- Permissions table -->
          <template v-if="s.id === 'permissions'">
            <div class="overflow-x-auto rounded-xl border border-slate-100">
              <table class="w-full text-xs">
                <thead>
                  <tr class="bg-slate-50 border-b border-slate-100">
                    <th class="text-left px-4 py-2.5 font-bold uppercase tracking-widest text-[10px] text-slate-500">Feature</th>
                    <th class="text-center px-4 py-2.5 font-bold uppercase tracking-widest text-[10px] text-slate-500">Admin</th>
                    <th class="text-center px-4 py-2.5 font-bold uppercase tracking-widest text-[10px] text-slate-500">HR</th>
                    <th class="text-center px-4 py-2.5 font-bold uppercase tracking-widest text-[10px] text-slate-500">Employee</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in permissionMatrix" :key="row.feature" class="border-b border-slate-50 last:border-0 hover:bg-slate-50/50">
                    <td class="px-4 py-2.5 text-slate-700 font-medium">{{ row.feature }}</td>
                    <td class="text-center px-4 py-2.5"><span :class="row.admin ? 'text-emerald-600 font-bold' : 'text-slate-300'">{{ row.admin ? '✓' : '—' }}</span></td>
                    <td class="text-center px-4 py-2.5"><span :class="row.hr ? 'text-emerald-600 font-bold' : 'text-slate-300'">{{ row.hr ? '✓' : '—' }}</span></td>
                    <td class="text-center px-4 py-2.5"><span :class="row.employee ? 'text-emerald-600 font-bold' : 'text-slate-300'">{{ row.employee ? '✓' : '—' }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>

          <!-- Regular content -->
          <template v-else>
            <div v-for="(block, i) in s.content" :key="i" class="space-y-2">
              <h4 v-if="block.heading" class="text-[11px] font-black uppercase tracking-widest text-slate-500 pt-1">{{ block.heading }}</h4>

              <p v-if="block.text" class="text-sm text-slate-600 leading-relaxed">{{ block.text }}</p>

              <!-- Note box -->
              <div v-if="block.note" class="flex items-start gap-2.5 bg-indigo-50 border border-indigo-100 rounded-xl px-4 py-3">
                <AlertCircle class="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                <p class="text-xs text-indigo-700 leading-relaxed">{{ block.note }}</p>
              </div>

              <!-- Warning box -->
              <div v-if="block.warn" class="flex items-start gap-2.5 bg-amber-50 border border-amber-100 rounded-xl px-4 py-3">
                <AlertCircle class="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                <p class="text-xs text-amber-700 leading-relaxed font-medium">{{ block.warn }}</p>
              </div>

              <!-- Numbered steps -->
              <ol v-if="block.numbered" class="space-y-1.5">
                <li
                  v-for="(step, j) in block.numbered"
                  :key="j"
                  class="flex items-start gap-3"
                >
                  <span class="mt-0.5 w-5 h-5 rounded-full bg-slate-900 text-white text-[9px] font-black flex items-center justify-center shrink-0">{{ j + 1 }}</span>
                  <span class="text-sm text-slate-600 leading-relaxed">{{ step }}</span>
                </li>
              </ol>

              <!-- Bullet points -->
              <ul v-if="block.bullets" class="space-y-1.5">
                <li
                  v-for="(b, j) in block.bullets"
                  :key="j"
                  class="flex items-start gap-2 text-sm text-slate-600"
                >
                  <span class="mt-2 w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0"></span>
                  {{ b }}
                </li>
              </ul>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
