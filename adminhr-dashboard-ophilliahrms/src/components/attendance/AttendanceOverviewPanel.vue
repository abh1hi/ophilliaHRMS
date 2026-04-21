<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock,
  MapPin,
  RefreshCw,
  Timer,
  Users,
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  getAttendanceAlerts,
  getAttendanceKpi,
  getAttendanceStatusBreakdown,
  getAttendanceTrend,
  listAttendanceRecords,
} from '../../services/attendance.service'
import type {
  AttendanceAlertsResponse,
  AttendanceKpi,
  AttendanceStatusBreakdown,
  AttendanceTrendPoint,
} from '../../services/attendance.service'
import { listShiftAssignments } from '../../services/shift-assignment.service'
import type { ShiftAssignment } from '../../services/shift-assignment.service'
import { listShiftLocations } from '../../services/shift-location.service'
import { listShiftTypes } from '../../services/shift-type.service'
import { getShiftAssignmentWarnings } from '../../utils/shiftAssignmentHealth'

const loading = ref(false)
const errorMsg = ref('')
const kpi = ref<AttendanceKpi | null>(null)
const trend = ref<AttendanceTrendPoint[]>([])
const breakdown = ref<AttendanceStatusBreakdown | null>(null)
const alerts = ref<AttendanceAlertsResponse | null>(null)
const assignments = ref<ShiftAssignment[]>([])
const shiftTypeIds = ref<Set<string>>(new Set())
const locationIds = ref<Set<string>>(new Set())
const recordsToday = ref(0)

const today = new Date().toISOString().slice(0, 10)

const statusSegments = computed(() => {
  const b = breakdown.value
  if (!b) return []
  const total = Math.max(1, b.present + b.late + b.half_day + b.absent + b.auto_closed)
  return [
    { label: 'Present', value: b.present, color: 'bg-emerald-300', pct: (b.present / total) * 100 },
    { label: 'Late', value: b.late, color: 'bg-amber-300', pct: (b.late / total) * 100 },
    { label: 'Half day', value: b.half_day, color: 'bg-sky-300', pct: (b.half_day / total) * 100 },
    { label: 'Absent', value: b.absent, color: 'bg-rose-300', pct: (b.absent / total) * 100 },
    { label: 'Auto closed', value: b.auto_closed, color: 'bg-slate-300', pct: (b.auto_closed / total) * 100 },
  ]
})

const overlapWarnings = computed(() => {
  return getShiftAssignmentWarnings(assignments.value, shiftTypeIds.value, locationIds.value).slice(0, 8)
})

const setupHealth = computed(() => [
  { label: 'Shift types', value: shiftTypeIds.value.size, ok: shiftTypeIds.value.size > 0, icon: Clock },
  { label: 'Geofence locations', value: locationIds.value.size, ok: locationIds.value.size > 0, icon: MapPin },
  { label: 'Assignments', value: assignments.value.length, ok: assignments.value.length > 0, icon: Users },
  { label: 'Today records', value: recordsToday.value, ok: recordsToday.value > 0, icon: Activity },
])

function maxTrendValue() {
  return Math.max(1, ...trend.value.map(item => item.present + item.late + item.absent + item.half_day + item.auto_closed))
}

async function load() {
  loading.value = true
  errorMsg.value = ''
  try {
    const [k, t, b, a, ass, types, locations, records] = await Promise.all([
      getAttendanceKpi(),
      getAttendanceTrend(14),
      getAttendanceStatusBreakdown(),
      getAttendanceAlerts(),
      listShiftAssignments(),
      listShiftTypes(),
      listShiftLocations(),
      listAttendanceRecords({ date_from: today, date_to: today, limit: 1 }),
    ])
    kpi.value = k
    trend.value = t.items ?? []
    breakdown.value = b
    alerts.value = a
    assignments.value = ass
    shiftTypeIds.value = new Set(types.map(item => item.id))
    locationIds.value = new Set(locations.map(item => item.id))
    recordsToday.value = records.total ?? 0
  } catch (e: any) {
    errorMsg.value = e.message ?? 'Unable to load attendance overview'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-widest text-slate-400">Live operations</p>
        <h2 class="mt-1 text-2xl font-semibold text-slate-950">Attendance Overview</h2>
        <p class="mt-1 text-sm text-slate-500">Monitor shift readiness, punches, late arrivals, and missed punch-outs.</p>
      </div>
      <Button variant="outline" class="h-10 rounded-md" :disabled="loading" @click="load">
        <RefreshCw :class="['mr-2 h-4 w-4', loading ? 'animate-spin' : '']" />
        Refresh
      </Button>
    </div>

    <div v-if="errorMsg" class="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {{ errorMsg }}
    </div>

    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <div class="rounded-lg border border-emerald-100 bg-emerald-50 p-4">
        <div class="flex items-center justify-between">
          <p class="text-sm font-medium text-emerald-900">Present</p>
          <CheckCircle2 class="h-5 w-5 text-emerald-600" />
        </div>
        <p class="mt-3 text-3xl font-semibold text-emerald-950">{{ kpi?.total_employees_present ?? 0 }}</p>
        <p class="mt-1 text-xs text-emerald-700">Records marked present today</p>
      </div>
      <div class="rounded-lg border border-amber-100 bg-amber-50 p-4">
        <div class="flex items-center justify-between">
          <p class="text-sm font-medium text-amber-900">Late</p>
          <Timer class="h-5 w-5 text-amber-600" />
        </div>
        <p class="mt-3 text-3xl font-semibold text-amber-950">{{ kpi?.late_checkins ?? 0 }}</p>
        <p class="mt-1 text-xs text-amber-700">After shift grace period</p>
      </div>
      <div class="rounded-lg border border-rose-100 bg-rose-50 p-4">
        <div class="flex items-center justify-between">
          <p class="text-sm font-medium text-rose-900">Absent</p>
          <Users class="h-5 w-5 text-rose-600" />
        </div>
        <p class="mt-3 text-3xl font-semibold text-rose-950">{{ kpi?.absent_employees ?? 0 }}</p>
        <p class="mt-1 text-xs text-rose-700">No valid attendance record</p>
      </div>
      <div class="rounded-lg border border-sky-100 bg-sky-50 p-4">
        <div class="flex items-center justify-between">
          <p class="text-sm font-medium text-sky-900">Missed punch-outs</p>
          <AlertTriangle class="h-5 w-5 text-sky-600" />
        </div>
        <p class="mt-3 text-3xl font-semibold text-sky-950">{{ kpi?.missed_punchouts ?? alerts?.missed_punch_out_count ?? 0 }}</p>
        <p class="mt-1 text-xs text-sky-700">Open records needing review</p>
      </div>
    </div>

    <div class="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
      <div class="rounded-lg border border-slate-200 bg-white p-4">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="font-semibold text-slate-900">14-day attendance trend</h3>
            <p class="text-xs text-slate-500">Present, late, absent, half-day, and auto-closed records.</p>
          </div>
          <BarChart3 class="h-5 w-5 text-slate-400" />
        </div>
        <div class="mt-6 flex h-48 items-end gap-2 overflow-x-auto pb-2">
          <div v-for="item in trend" :key="item.date" class="flex min-w-10 flex-1 flex-col items-center gap-2">
            <div class="flex h-36 w-full items-end rounded-md bg-slate-50 px-1">
              <div
                class="w-full rounded-sm bg-teal-300"
                :style="{ height: `${Math.max(6, ((item.present + item.late + item.half_day) / maxTrendValue()) * 100)}%` }"
              />
            </div>
            <span class="text-[10px] font-medium text-slate-400">{{ new Date(item.date).getDate() }}</span>
          </div>
          <p v-if="!trend.length && !loading" class="w-full py-16 text-center text-sm text-slate-400">No trend data yet.</p>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white p-4">
        <h3 class="font-semibold text-slate-900">Today status mix</h3>
        <div class="mt-5 h-3 overflow-hidden rounded-full bg-slate-100">
          <div class="flex h-full">
            <div v-for="seg in statusSegments" :key="seg.label" :class="seg.color" :style="{ width: `${seg.pct}%` }" />
          </div>
        </div>
        <div class="mt-5 space-y-3">
          <div v-for="seg in statusSegments" :key="seg.label" class="flex items-center justify-between text-sm">
            <div class="flex items-center gap-2">
              <span :class="['h-2.5 w-2.5 rounded-full', seg.color]" />
              <span class="text-slate-600">{{ seg.label }}</span>
            </div>
            <span class="font-semibold text-slate-900">{{ seg.value }}</span>
          </div>
        </div>
        <div class="mt-6 rounded-md bg-slate-50 p-3">
          <p class="text-xs text-slate-500">Task completion</p>
          <p class="mt-1 text-xl font-semibold text-slate-900">{{ Math.round(kpi?.task_completion_rate ?? 0) }}%</p>
          <p class="mt-1 text-xs text-slate-500">{{ kpi?.completed_tasks_today ?? 0 }} of {{ kpi?.total_tasks_today ?? 0 }} tasks closed</p>
        </div>
      </div>
    </div>

    <div class="grid gap-4 xl:grid-cols-2">
      <div class="rounded-lg border border-slate-200 bg-white p-4">
        <h3 class="font-semibold text-slate-900">Setup health</h3>
        <div class="mt-4 grid gap-3 sm:grid-cols-2">
          <div v-for="item in setupHealth" :key="item.label" class="rounded-md border border-slate-100 bg-slate-50 p-3">
            <div class="flex items-center justify-between">
              <component :is="item.icon" class="h-4 w-4 text-slate-500" />
              <span :class="['rounded-full px-2 py-0.5 text-[10px] font-semibold', item.ok ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700']">
                {{ item.ok ? 'Ready' : 'Needs setup' }}
              </span>
            </div>
            <p class="mt-3 text-2xl font-semibold text-slate-900">{{ item.value }}</p>
            <p class="text-xs text-slate-500">{{ item.label }}</p>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white p-4">
        <h3 class="font-semibold text-slate-900">Roster warnings</h3>
        <div v-if="overlapWarnings.length" class="mt-4 space-y-2">
          <div v-for="warning in overlapWarnings" :key="warning" class="flex items-start gap-2 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
            <AlertTriangle class="mt-0.5 h-4 w-4 shrink-0" />
            <span>{{ warning }}</span>
          </div>
        </div>
        <div v-else class="mt-4 rounded-md bg-emerald-50 px-3 py-4 text-sm text-emerald-800">
          No missing references or overlapping active assignments found.
        </div>
      </div>
    </div>
  </div>
</template>
