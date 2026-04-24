<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Grid3X3, BarChart2, ChevronLeft, ChevronRight, Calendar } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { listShiftScheduleAssignments, listShiftSchedules } from '../../services/shift-schedule.service'
import { listShiftTypes } from '../../services/shift-type.service'
import { listEmployees } from '../../services/employee.service'
import type { ShiftSchedule, ShiftScheduleAssignment } from '../../services/shift-schedule.service'
import type { ShiftType } from '../../services/shift-type.service'

type ViewMode = 'roster' | 'timeline'

const view = ref<ViewMode>('roster')
const loading = ref(false)
const currentDate = ref(new Date())

interface EmployeeRow {
  id: string
  name: string
  employee_code: string
}

const employees = ref<EmployeeRow[]>([])
const schedules = ref<ShiftSchedule[]>([])
const shiftTypes = ref<ShiftType[]>([])
const assignments = ref<ShiftScheduleAssignment[]>([])

// Roster: week dates (Mon–Sun)
const weekDates = computed(() => {
  const d = new Date(currentDate.value)
  const day = d.getDay()
  const monday = new Date(d)
  monday.setDate(d.getDate() - (day === 0 ? 6 : day - 1))
  return Array.from({ length: 7 }, (_, i) => {
    const date = new Date(monday)
    date.setDate(monday.getDate() + i)
    return date
  })
})

const weekLabel = computed(() => {
  const first = weekDates.value[0]
  const last = weekDates.value[6]
  return `${first.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })} – ${last.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}`
})

function prevWeek() {
  const d = new Date(currentDate.value)
  d.setDate(d.getDate() - 7)
  currentDate.value = d
}
function nextWeek() {
  const d = new Date(currentDate.value)
  d.setDate(d.getDate() + 7)
  currentDate.value = d
}
function goToday() { currentDate.value = new Date() }

function getShiftType(scheduleId: string): ShiftType | undefined {
  const schedule = schedules.value.find(s => s.id === scheduleId)
  if (!schedule) return undefined
  return shiftTypes.value.find(t => t.id === schedule.shift_type_id)
}

function getAssignmentForDate(employeeId: string, date: Date): ShiftScheduleAssignment | undefined {
  const dateStr = date.toISOString().slice(0, 10)
  return assignments.value.find(a => {
    if (a.employee_id !== employeeId) return false
    if (a.effective_from && a.effective_from > dateStr) return false
    if (a.effective_to && a.effective_to < dateStr) return false
    return true
  })
}

function getScheduleForEmployee(employeeId: string, date: Date): ShiftSchedule | undefined {
  const assignment = getAssignmentForDate(employeeId, date)
  if (!assignment) return undefined
  return schedules.value.find(s => s.id === assignment.schedule_id)
}

function isOffDay(schedule: ShiftSchedule | undefined, date: Date): boolean {
  if (!schedule?.off_days?.length) return false
  const day = date.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase()
  return schedule.off_days.includes(day)
}

function isToday(date: Date): boolean {
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

function shiftColor(shiftTypeId: string | undefined): string {
  if (!shiftTypeId) return '#94a3b8'
  const st = shiftTypes.value.find(t => t.id === shiftTypeId)
  return st?.color_code || '#6366f1'
}

// Timeline: hours 0–24
const hours = Array.from({ length: 25 }, (_, i) => i)

function timeToPercent(timeStr: string): number {
  if (!timeStr) return 0
  const [h, m] = timeStr.split(':').map(Number)
  return ((h * 60 + m) / (24 * 60)) * 100
}

function shiftWidthPercent(startTime: string, endTime: string, isNight: boolean): number {
  const startMin = parseInt(startTime.split(':')[0]) * 60 + parseInt(startTime.split(':')[1])
  let endMin = parseInt(endTime.split(':')[0]) * 60 + parseInt(endTime.split(':')[1])
  if (isNight && endMin <= startMin) endMin += 24 * 60
  return ((endMin - startMin) / (24 * 60)) * 100
}

interface EmployeeShiftBar {
  employee: EmployeeRow
  schedule: ShiftSchedule
  shiftType: ShiftType
  startPct: number
  widthPct: number
}

const timelineDate = computed(() => currentDate.value.toLocaleDateString('en-IN', {
  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
}))

const timelineBars = computed((): EmployeeShiftBar[] => {
  return employees.value.flatMap(emp => {
    const schedule = getScheduleForEmployee(emp.id, currentDate.value)
    if (!schedule || isOffDay(schedule, currentDate.value)) return []
    const st = shiftTypes.value.find(t => t.id === schedule.shift_type_id)
    if (!st) return []
    return [{
      employee: emp,
      schedule,
      shiftType: st,
      startPct: timeToPercent(st.start_time),
      widthPct: shiftWidthPercent(st.start_time, st.end_time, st.is_night_shift),
    }]
  })
})

async function load() {
  loading.value = true
  try {
    const [emps, sched, types, assign] = await Promise.all([
      listEmployees(),
      listShiftSchedules(),
      listShiftTypes(),
      listShiftScheduleAssignments(),
    ])
    employees.value = (emps.data ?? []).map((e: any) => ({
      id: e.id,
      name: `${e.first_name ?? ''} ${e.last_name ?? ''}`.trim() || e.employee_code,
      employee_code: e.employee_code,
    }))
    schedules.value = sched
    shiftTypes.value = types
    assignments.value = assign
  } catch (e) {
    console.error('Visual shift scheduler load error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-black text-slate-900 tracking-tight">Visual Shift Scheduler</h2>
        <p class="text-xs text-slate-400 mt-0.5">View and manage employee shift assignments</p>
      </div>
      <div class="flex items-center gap-3">
        <!-- View toggle -->
        <div class="flex bg-slate-100 rounded-xl p-1 gap-1">
          <button
            @click="view = 'roster'"
            :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all', view === 'roster' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400 hover:text-slate-700']"
          >
            <Grid3X3 class="w-3.5 h-3.5" /> Roster
          </button>
          <button
            @click="view = 'timeline'"
            :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all', view === 'timeline' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400 hover:text-slate-700']"
          >
            <BarChart2 class="w-3.5 h-3.5" /> Timeline
          </button>
        </div>

        <!-- Navigation -->
        <div class="flex items-center gap-2 bg-white border border-slate-200 rounded-xl px-3 py-1.5">
          <button @click="prevWeek" class="text-slate-400 hover:text-slate-900 transition-colors p-0.5">
            <ChevronLeft class="w-4 h-4" />
          </button>
          <span class="text-xs font-bold text-slate-700 min-w-[180px] text-center">{{ weekLabel }}</span>
          <button @click="nextWeek" class="text-slate-400 hover:text-slate-900 transition-colors p-0.5">
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>

        <Button variant="outline" size="sm" @click="goToday" class="rounded-xl text-xs font-bold h-9">
          <Calendar class="w-3.5 h-3.5 mr-1.5" /> Today
        </Button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- ── ROSTER VIEW ── -->
    <div v-else-if="view === 'roster'" class="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-xs min-w-[800px]">
          <thead>
            <tr class="border-b border-slate-100">
              <th class="text-left px-4 py-3 text-[10px] font-black uppercase tracking-widest text-slate-400 w-48 sticky left-0 bg-white z-10">
                Employee
              </th>
              <th
                v-for="date in weekDates"
                :key="date.toISOString()"
                class="px-2 py-3 text-center text-[10px] font-black uppercase tracking-widest min-w-[110px]"
                :class="isToday(date) ? 'text-indigo-600 bg-indigo-50/50' : 'text-slate-400'"
              >
                <div>{{ date.toLocaleDateString('en-IN', { weekday: 'short' }) }}</div>
                <div class="text-[11px] font-bold mt-0.5" :class="isToday(date) ? 'text-indigo-700' : 'text-slate-700'">
                  {{ date.getDate() }}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="employees.length === 0">
              <td :colspan="8" class="text-center text-slate-400 py-16 text-sm">No employees found.</td>
            </tr>
            <tr
              v-for="emp in employees"
              :key="emp.id"
              class="border-b border-slate-50 hover:bg-slate-50/50 transition-colors group"
            >
              <td class="px-4 py-2.5 sticky left-0 bg-white group-hover:bg-slate-50/50 z-10">
                <div class="font-semibold text-slate-800">{{ emp.name }}</div>
                <div class="text-[10px] text-slate-400">{{ emp.employee_code }}</div>
              </td>
              <td
                v-for="date in weekDates"
                :key="date.toISOString()"
                class="px-2 py-2.5 text-center"
                :class="isToday(date) ? 'bg-indigo-50/30' : ''"
              >
                <template v-if="getScheduleForEmployee(emp.id, date) as schedule">
                  <div
                    v-if="isOffDay(schedule, date)"
                    class="inline-flex items-center px-2 py-1 rounded-lg bg-slate-100 text-[9px] font-bold text-slate-400 uppercase tracking-widest"
                  >
                    Off
                  </div>
                  <div
                    v-else
                    class="inline-flex flex-col items-center px-2.5 py-1.5 rounded-xl text-white text-[9px] font-bold gap-0.5 shadow-sm"
                    :style="{ backgroundColor: shiftColor(schedule.shift_type_id) }"
                  >
                    <span>{{ schedule.name }}</span>
                    <span class="opacity-80 font-normal">
                      {{
                        (() => {
                          const st = shiftTypes.find(t => t.id === schedule.shift_type_id)
                          return st ? `${st.start_time}–${st.end_time}` : ''
                        })()
                      }}
                    </span>
                  </div>
                </template>
                <span v-else class="text-slate-200">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Legend -->
      <div class="px-4 py-3 border-t border-slate-50 flex items-center gap-4 flex-wrap">
        <span class="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Shifts:</span>
        <div v-for="st in shiftTypes" :key="st.id" class="flex items-center gap-1.5">
          <div class="w-3 h-3 rounded-full shadow-sm" :style="{ backgroundColor: st.color_code || '#6366f1' }" />
          <span class="text-[10px] font-semibold text-slate-600">{{ st.name }}</span>
        </div>
        <div class="flex items-center gap-1.5 ml-2">
          <div class="w-3 h-3 rounded-full bg-slate-200" />
          <span class="text-[10px] font-semibold text-slate-400">Off Day</span>
        </div>
      </div>
    </div>

    <!-- ── TIMELINE VIEW ── -->
    <div v-else class="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
      <div class="px-4 py-3 border-b border-slate-50">
        <p class="text-xs font-bold text-slate-700">{{ timelineDate }}</p>
        <p class="text-[10px] text-slate-400 mt-0.5">Shift coverage across 24 hours (IST)</p>
      </div>

      <div class="overflow-x-auto">
        <div class="min-w-[900px] px-4 py-4">
          <!-- Hour axis -->
          <div class="flex mb-2 pl-44">
            <div
              v-for="h in hours.filter((_, i) => i % 2 === 0)"
              :key="h"
              class="text-[9px] text-slate-300 font-bold"
              :style="{ width: `${(2 / 24) * 100}%` }"
            >
              {{ h.toString().padStart(2, '0') }}:00
            </div>
          </div>

          <!-- Employee rows -->
          <div v-if="timelineBars.length === 0" class="text-center text-slate-400 py-16 text-sm">
            No shifts assigned for this day.
          </div>
          <div
            v-for="bar in timelineBars"
            :key="bar.employee.id"
            class="flex items-center mb-2 gap-3"
          >
            <!-- Employee name -->
            <div class="w-44 shrink-0 text-right pr-2">
              <div class="text-xs font-semibold text-slate-700 truncate">{{ bar.employee.name }}</div>
              <div class="text-[9px] text-slate-400">{{ bar.employee.employee_code }}</div>
            </div>

            <!-- Timeline bar container -->
            <div class="flex-1 relative h-9 bg-slate-50 rounded-xl overflow-hidden border border-slate-100">
              <!-- Hour grid lines -->
              <div
                v-for="h in hours"
                :key="h"
                class="absolute top-0 bottom-0 w-px bg-slate-100"
                :style="{ left: `${(h / 24) * 100}%` }"
              />

              <!-- Shift bar -->
              <div
                class="absolute top-1 bottom-1 rounded-lg flex items-center px-2 shadow-sm"
                :style="{
                  left: `${bar.startPct}%`,
                  width: `${bar.widthPct}%`,
                  backgroundColor: bar.shiftType.color_code || '#6366f1',
                }"
              >
                <span class="text-[9px] font-bold text-white truncate">
                  {{ bar.shiftType.start_time }}–{{ bar.shiftType.end_time }}
                  {{ bar.shiftType.is_night_shift ? '🌙' : '' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
