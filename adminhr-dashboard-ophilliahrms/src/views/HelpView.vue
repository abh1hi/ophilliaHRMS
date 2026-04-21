<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  MapPin,
  Smartphone,
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

const emit = defineEmits<{ (e: 'navigate', tab: string): void }>()

interface Step {
  id: string
  title: string
  tab?: string
  summary: string
  actions: string[]
  checks: string[]
}

const steps: Step[] = [
  {
    id: 'hr-setup',
    title: '1. Create HR basics',
    tab: 'departments',
    summary: 'Departments, branches, designations, employment types, grades, and groups are the lookup data used by employee profiles.',
    actions: [
      'Go to HR Setup and create every department and branch that will record attendance.',
      'Create designations and employment types before importing employees.',
      'Use employee groups for field teams, remote staff, or night-shift teams if rules differ.',
    ],
    checks: [
      'Every employee can be assigned to a department and branch.',
      'Names match the CSV import template exactly.',
    ],
  },
  {
    id: 'locations',
    title: '2. Create geofence shift locations',
    tab: 'shift-locations',
    summary: 'Shift Locations are backed by attendance geofences. They define where GPS-based clock-in and clock-out are allowed.',
    actions: [
      'Go to Shifts > Locations and choose Add Location.',
      'Drop the map marker on the building entrance or worksite center.',
      'Set radius: 50-100m for offices, 200-500m for campuses, wider for field sites.',
      'Save one location per physical worksite. Remote teams can use a wide-radius remote location if your policy allows it.',
    ],
    checks: [
      'Location appears in the list after saving.',
      'Latitude, longitude, and radius are populated.',
      'Employee app shows the expected work site during attendance.',
    ],
  },
  {
    id: 'shift-types',
    title: '3. Create shift types',
    tab: 'shift-types',
    summary: 'Shift Types define start time, end time, break duration, grace period, night-shift behavior, and overtime baseline hours.',
    actions: [
      'Go to Shifts > Shift Types and choose New Shift Type.',
      'Create one type for each working pattern: General, Morning, Afternoon, Night, Flexible.',
      'Set Night Shift when the shift crosses midnight.',
      'Use color labels so roster and overlap visuals are easy to scan.',
    ],
    checks: [
      'Start and end times match the real workday.',
      'Grace period reflects HR policy.',
      'Work hours per day matches overtime policy assumptions.',
    ],
  },
  {
    id: 'employees',
    title: '4. Add or import employees',
    tab: 'employees',
    summary: 'Attendance works only after employees have active records and portal access.',
    actions: [
      'Add employees manually or use Employees > Bulk Import for CSV uploads.',
      'Send or resend employee portal invites from the employee profile.',
      'Ask employees to activate the invite before first attendance recording.',
    ],
    checks: [
      'Employee status is active.',
      'Employee has a portal account or active invite.',
      'Department and branch are correct.',
    ],
  },
  {
    id: 'assignments',
    title: '5. Assign shifts and locations',
    tab: 'shift-assignments',
    summary: 'Shift Assignments connect each employee to a shift type and geofence location for a date range.',
    actions: [
      'Go to Shifts > Assignments and choose Assign Employee.',
      'Select employee, shift type, location, and effective-from date.',
      'Use effective-to only for temporary coverage.',
      'Create a new assignment for future changes instead of editing history.',
    ],
    checks: [
      'Every attendance employee has one active assignment.',
      'No active assignment has a missing shift type or location.',
      'No employee has overlapping active date ranges.',
    ],
  },
  {
    id: 'roster',
    title: '6. Verify roster and overlap warnings',
    tab: 'roster',
    summary: 'The Roster and Attendance Overview give HR a visual check before employees start punching in.',
    actions: [
      'Open Shifts > Roster for the current week.',
      'Open Attendance > Overview and review setup health.',
      'Fix missing shift type, missing location, and overlapping assignment warnings.',
    ],
    checks: [
      'Roster shows expected employees on expected days.',
      'Attendance Overview setup cards are ready.',
      'Warnings are resolved before go-live.',
    ],
  },
  {
    id: 'employee-app',
    title: '7. Install employee PWA and grant location',
    summary: 'Employees should install the app and allow location access for geofence attendance.',
    actions: [
      'Employee opens the employee app on their phone and signs in.',
      'From browser menu, choose Add to Home Screen or Install App.',
      'When prompted, allow location access.',
      'If offline, employees can still save attendance; the app queues it and syncs when online.',
    ],
    checks: [
      'App opens from the phone home screen.',
      'Home page shows Online or Offline sync status.',
      'Attendance page shows GPS accuracy and geofence distance.',
    ],
  },
  {
    id: 'record',
    title: '8. Start recording attendance',
    tab: 'attendance',
    summary: 'Employees clock in, add tasks, and clock out. HR monitors live data from Attendance Overview and Records.',
    actions: [
      'Employee opens Attendance and taps Clock in.',
      'Employee adds tasks from the native action sheet while the shift is active.',
      'At day end, employee opens the punch-out sheet, rates the day, completes tasks, and clocks out.',
      'If offline, the app saves each action locally and replays it in order when online.',
    ],
    checks: [
      'Admin Attendance Records shows the record.',
      'Work hours and overtime are calculated after clock-out.',
      'Queued offline actions disappear after sync.',
    ],
  },
  {
    id: 'review',
    title: '9. Review, adjust, and export',
    tab: 'attendance-records',
    summary: 'HR reviews exceptions, missed punch-outs, employee adjustments, and biometric uploads from the Attendance section.',
    actions: [
      'Use Attendance > Overview for late and missed punch-out monitoring.',
      'Use Attendance > Records for filtering and manual corrections.',
      'Use Attendance > Adjustments to approve employee correction requests.',
      'Use Attendance > Upload Attendance for biometric CSV import when required.',
    ],
    checks: [
      'Corrections include notes.',
      'Missed punch-outs are resolved daily.',
      'Exports match payroll and compliance expectations.',
    ],
  },
]

const troubleshooting = [
  {
    title: 'GPS permission denied',
    fix: 'Ask the employee to enable location permission for the installed PWA or browser, then reopen Attendance and tap Refresh location.',
  },
  {
    title: 'Outside geofence',
    fix: 'Verify the employee is at the correct site. If the marker is wrong, update Shifts > Locations with the correct building entrance and radius.',
  },
  {
    title: 'Duplicate punch or conflict',
    fix: 'Check Attendance > Records for an existing open record. If needed, correct the record instead of creating another punch.',
  },
  {
    title: 'Missing shift assignment',
    fix: 'Create an active Shifts > Assignment with employee, shift type, location, and effective-from date.',
  },
  {
    title: 'Offline queue stuck',
    fix: 'Employee should reconnect and tap Sync now. If a row fails, review the error, confirm token/session, then retry after logging in again.',
  },
  {
    title: 'Invite or account issue',
    fix: 'Open the employee profile, resend invite, and confirm the employee uses the newest invite link.',
  },
]

const open = ref<Set<string>>(new Set(['hr-setup', 'locations', 'shift-types']))
const activeStep = computed(() => steps.find(step => open.value.has(step.id))?.id ?? steps[0].id)

function toggle(id: string) {
  const next = new Set(open.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  open.value = next
}

function goTo(tab?: string) {
  if (tab) emit('navigate', tab)
}
</script>

<template>
  <div class="grid gap-6 xl:grid-cols-[260px_1fr]">
    <aside class="space-y-4 xl:sticky xl:top-4 xl:self-start">
      <div class="rounded-lg border border-slate-200 bg-white p-4">
        <p class="text-xs font-semibold uppercase tracking-widest text-slate-400">Attendance launch</p>
        <div class="mt-4 space-y-1">
          <button
            v-for="step in steps"
            :key="step.id"
            :class="[
              'w-full rounded-md px-3 py-2 text-left text-sm font-medium',
              activeStep === step.id ? 'bg-teal-50 text-teal-800' : 'text-slate-600 hover:bg-slate-50'
            ]"
            type="button"
            @click="toggle(step.id)"
          >
            {{ step.title.replace(/^\d+\.\s*/, '') }}
          </button>
        </div>
      </div>

      <div class="rounded-lg border border-teal-100 bg-teal-50 p-4">
        <Smartphone class="h-5 w-5 text-teal-700" />
        <h3 class="mt-3 font-semibold text-teal-950">Employee app</h3>
        <p class="mt-1 text-sm text-teal-800">Install as a PWA, allow location, and use offline sync when field teams lose network.</p>
      </div>
    </aside>

    <main class="space-y-4">
      <section class="rounded-lg border border-slate-200 bg-white p-5">
        <p class="text-xs font-semibold uppercase tracking-widest text-slate-400">Start here</p>
        <h2 class="mt-2 text-2xl font-semibold text-slate-950">Set up attendance in the right order</h2>
        <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Complete steps 1-6 before your first live punch. Steps 7-9 cover employee rollout and daily HR operations.
        </p>
      </section>

      <section v-for="step in steps" :key="step.id" :id="step.id" class="rounded-lg border border-slate-200 bg-white">
        <button class="flex w-full items-center justify-between gap-4 px-5 py-4 text-left" type="button" @click="toggle(step.id)">
          <div>
            <h3 class="font-semibold text-slate-950">{{ step.title }}</h3>
            <p class="mt-1 text-sm text-slate-500">{{ step.summary }}</p>
          </div>
          <div class="flex items-center gap-3">
            <Button v-if="step.tab" variant="outline" size="sm" class="rounded-md" @click.stop="goTo(step.tab)">
              Open <ExternalLink class="ml-2 h-3.5 w-3.5" />
            </Button>
            <component :is="open.has(step.id) ? ChevronDown : ChevronRight" class="h-4 w-4 text-slate-400" />
          </div>
        </button>

        <div v-if="open.has(step.id)" class="grid gap-4 border-t border-slate-100 p-5 lg:grid-cols-2">
          <div>
            <p class="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">Do this</p>
            <ol class="space-y-2">
              <li v-for="(action, index) in step.actions" :key="action" class="flex gap-3 text-sm leading-6 text-slate-700">
                <span class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-900 text-[10px] font-bold text-white">{{ index + 1 }}</span>
                <span>{{ action }}</span>
              </li>
            </ol>
          </div>
          <div>
            <p class="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">Verify</p>
            <div class="space-y-2">
              <div v-for="check in step.checks" :key="check" class="flex gap-2 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
                <CheckCircle2 class="mt-0.5 h-4 w-4 shrink-0 text-teal-600" />
                <span>{{ check }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="rounded-lg border border-amber-200 bg-amber-50 p-5">
        <div class="flex items-start gap-3">
          <AlertTriangle class="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
          <div>
            <h3 class="font-semibold text-amber-950">Troubleshooting</h3>
            <div class="mt-4 grid gap-3 md:grid-cols-2">
              <div v-for="item in troubleshooting" :key="item.title" class="rounded-md border border-amber-200 bg-white/70 p-3">
                <p class="font-semibold text-amber-950">{{ item.title }}</p>
                <p class="mt-1 text-sm leading-6 text-amber-900">{{ item.fix }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="rounded-lg border border-slate-200 bg-white p-5">
        <div class="flex items-start gap-3">
          <MapPin class="mt-0.5 h-5 w-5 shrink-0 text-teal-700" />
          <div>
            <h3 class="font-semibold text-slate-950">Go-live checklist</h3>
            <p class="mt-1 text-sm leading-6 text-slate-600">
              HR setup complete, geofences created, shift types ready, employees active, assignments verified, roster warnings resolved,
              employee PWA installed, location permission granted, and Attendance Overview monitored daily.
            </p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
