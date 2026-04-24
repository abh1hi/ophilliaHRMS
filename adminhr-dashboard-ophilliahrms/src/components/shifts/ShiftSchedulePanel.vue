<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import FormSelect from '../ui/FormSelect.vue'
import EntitySearchSelect from '../ui/EntitySearchSelect.vue'
import { Button } from '@/components/ui/button'
import {
  Pencil,
  Trash2,
  CalendarClock,
  Calendar,
  CheckCircle2,
  XCircle,
  Layers,
  Clock,
  Users,
  MapPin,
  Coffee,
  CalendarOff,
  ChevronRight,
  ChevronLeft,
  Check,
} from 'lucide-vue-next'
import { listShiftSchedules, createShiftSchedule, updateShiftSchedule, deleteShiftSchedule } from '../../services/shift-schedule.service'
import { listShiftScheduleAssignments, createShiftScheduleAssignment, deleteShiftScheduleAssignment } from '../../services/shift-schedule.service'
import type { ShiftSchedule } from '../../services/shift-schedule.service'
import { listShiftTypes } from '../../services/shift-type.service'
import { listShiftLocations } from '../../services/shift-location.service'
import { listEmployees } from '../../services/employee.service'

interface ShiftType { id: string; name: string }
interface ShiftLocation { id: string; name: string }
interface Employee { id: string; first_name: string; last_name: string; employee_code: string }
interface ShiftScheduleForm extends Partial<ShiftSchedule> { employee_ids: string[] }

const WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
const STEPS = [
  { num: 1, label: 'Basic Info', icon: Layers },
  { num: 2, label: 'Clock Windows', icon: Clock },
  { num: 3, label: 'Locations', icon: MapPin },
  { num: 4, label: 'Off Days & Break', icon: CalendarOff },
  { num: 5, label: 'Settings', icon: CalendarClock },
  { num: 6, label: 'Employees', icon: Users },
]

// "Before/After minutes" UX — converted to actual times on save
const clockInBeforeMin  = ref(10)
const clockInAfterMin   = ref(5)
const clockOutBeforeMin = ref(10)
const clockOutAfterMin  = ref(10)

const currentStep = ref(1)
const stepErrors = ref<Record<number, string>>({})

function addMinutesToTime(timeStr: string, minutes: number): string {
  if (!timeStr) return ''
  const [h, m] = timeStr.split(':').map(Number)
  const total = h * 60 + m + minutes
  const hh = Math.floor(((total % 1440) + 1440) % 1440 / 60).toString().padStart(2, '0')
  const mm = (((total % 1440) + 1440) % 1440 % 60).toString().padStart(2, '0')
  return `${hh}:${mm}`
}

function getShiftStartTime(): string {
  const st = shiftTypes.value.find(t => t.id === form.value.shift_type_id)
  return (st as any)?.start_time ?? ''
}

function getShiftEndTime(): string {
  const st = shiftTypes.value.find(t => t.id === form.value.shift_type_id)
  return (st as any)?.end_time ?? ''
}

const rows = ref<ShiftSchedule[]>([])
const loading = ref(false)
const dialogOpen = ref(false)
const form = ref<ShiftScheduleForm>({
  allowed_clock_in_location_ids: [],
  allowed_clock_out_location_ids: [],
  auto_clock_out_enabled: true,
  tasks_mandatory: false,
  employee_ids: [],
  off_days: [],
})
const selected = ref<ShiftSchedule | null>(null)
const deleteTarget = ref<ShiftSchedule | null>(null)
const saving = ref(false)
const deleting = ref(false)
const errorMsg = ref('')

const shiftTypes = ref<ShiftType[]>([])
const shiftLocations = ref<ShiftLocation[]>([])
const employees = ref<Employee[]>([])

const shiftTypeOptions = computed(() => [
  { value: '', label: 'Select shift type' },
  ...shiftTypes.value.map(type => ({ value: String(type.id), label: type.name }))
])

const locationOptions = computed(() => 
  shiftLocations.value.map(loc => ({ value: String(loc.id), label: loc.name }))
)

const columns = [
  { key: 'name',           label: 'Schedule Name' },
  { key: 'shift_type',     label: 'Shift Type' },
  { key: 'effective_from', label: 'Start Date' },
  { key: 'is_active',      label: 'Status' },
]

async function load() {
  loading.value = true
  try {
    const [schedules, types, locations, emps] = await Promise.all([
      listShiftSchedules(),
      listShiftTypes(),
      listShiftLocations(),
      listEmployees(),
    ])
    rows.value = schedules
    shiftTypes.value = types
    shiftLocations.value = locations
    employees.value = emps.data ?? []
  } catch (e) {
    console.error('Failed to load data:', e)
  } finally {
    loading.value = false
  }
}

onMounted(load)

function openCreate() {
  selected.value = null
  form.value = {
    allowed_clock_in_location_ids: [],
    allowed_clock_out_location_ids: [],
    auto_clock_out_enabled: true,
    tasks_mandatory: false,
    employee_ids: [],
    off_days: ['saturday', 'sunday'],
  }
  clockInBeforeMin.value = 10
  clockInAfterMin.value = 5
  clockOutBeforeMin.value = 10
  clockOutAfterMin.value = 10
  errorMsg.value = ''
  currentStep.value = 1
  stepErrors.value = {}
  dialogOpen.value = true
}

function openEdit(row: ShiftSchedule) {
  selected.value = row
  form.value = { ...row, employee_ids: [] }
  errorMsg.value = ''
  currentStep.value = 1
  stepErrors.value = {}
  dialogOpen.value = true
  void loadAssignmentsForSchedule(row.id)
}

async function loadAssignmentsForSchedule(scheduleId: string) {
  try {
    const assignments = await listShiftScheduleAssignments(scheduleId)
    form.value.employee_ids = assignments.map(item => item.employee_id)
  } catch (e) {
    console.error('Failed to load schedule assignments:', e)
  }
}

async function syncAssignments(scheduleId: string) {
  const employeeIds = Array.from(new Set(form.value.employee_ids ?? [])).filter(Boolean)
  const existing = await listShiftScheduleAssignments(scheduleId)
  await Promise.all(existing.map(item => deleteShiftScheduleAssignment(item.id)))

  const effectiveFrom = form.value.effective_from || new Date().toISOString().slice(0, 10)
  await Promise.all(
    employeeIds.map((employeeId) =>
      createShiftScheduleAssignment({
        schedule_id: scheduleId,
        employee_id: employeeId,
        effective_from: effectiveFrom,
        effective_to: form.value.effective_to || undefined,
      }),
    ),
  )
}

async function save() {
  if (!validateStep(currentStep.value)) {
    return
  }

  saving.value = true
  errorMsg.value = ''
  try {
    const shiftStart = getShiftStartTime()
    const shiftEnd = getShiftEndTime()
    if (!shiftStart || !shiftEnd) {
      errorMsg.value = 'Shift type is invalid. Please go back to Step 1 and select a valid shift type.'
      saving.value = false
      return
    }

    const computedWindows = {
      clock_in_start_time:  addMinutesToTime(shiftStart, -clockInBeforeMin.value),
      clock_in_end_time:    addMinutesToTime(shiftStart,  clockInAfterMin.value),
      clock_out_start_time: addMinutesToTime(shiftEnd,   -clockOutBeforeMin.value),
      clock_out_end_time:   addMinutesToTime(shiftEnd,    clockOutAfterMin.value),
    }

    const { employee_ids, ...restForm } = form.value
    const schedulePayload = { ...restForm, ...computedWindows }

    if (selected.value) {
      await updateShiftSchedule(selected.value.id, schedulePayload)
      await syncAssignments(selected.value.id)
    } else {
      const created = await createShiftSchedule(schedulePayload)
      await syncAssignments(created.id)
    }
    dialogOpen.value = false
    load()
  } catch (e: any) {
    errorMsg.value = e.message || 'Failed to save schedule. Please check your inputs.'
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await deleteShiftSchedule(deleteTarget.value.id)
    deleteTarget.value = null
    load()
  } catch (e) {
    console.error('Failed to delete:', e)
  } finally {
    deleting.value = false
  }
}

function getShiftTypeName(id: string) {
  return shiftTypes.value.find(t => t.id === id)?.name || 'Unknown'
}

function getLocationNames(ids: string[]) {
  return ids.map(id => shiftLocations.value.find(l => l.id === id)?.name || 'Unknown').join(', ') || '—'
}

function getEmployeeName(employeeId: string) {
  const employee = employees.value.find(item => item.id === employeeId)
  if (!employee) return employeeId
  const fullName = `${employee.first_name ?? ''} ${employee.last_name ?? ''}`.trim()
  return fullName || employee.employee_code || employeeId
}

function validateStep(step: number): boolean {
  stepErrors.value[step] = ''

  if (step === 1) {
    if (!form.value.name?.trim()) { stepErrors.value[1] = 'Schedule name is required'; return false }
    if (!form.value.shift_type_id) { stepErrors.value[1] = 'Shift type is required'; return false }
  }
  if (step === 2) {
    if (!form.value.shift_type_id) { stepErrors.value[2] = 'Shift type must be set first'; return false }
  }
  if (step === 6) {
    if (!form.value.effective_from) { stepErrors.value[6] = 'Start date is required'; return false }
  }

  return true
}

function goToStep(step: number) {
  if (validateStep(currentStep.value)) {
    currentStep.value = step
  }
}

function nextStep() {
  if (validateStep(currentStep.value) && currentStep.value < STEPS.length) {
    currentStep.value += 1
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value -= 1
  }
}
</script>

<template>
  <div class="space-y-10">
    <PageHeader
      title="Shift Schedules"
      subtitle="Define and manage shift schedules with types, locations, and employee assignments"
      action-label="New Schedule"
      @action="openCreate"
    />

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No shift schedules yet.">
      <template #cell-name="{ value }">
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-xl bg-slate-100 flex items-center justify-center border border-white/40 shadow-sm shrink-0">
            <Layers class="w-4 h-4 text-slate-500" />
          </div>
          <span class="font-bold text-slate-900">{{ value }}</span>
        </div>
      </template>
      <template #cell-shift_type="{ row }">
        <div class="flex items-center gap-2">
          <Clock class="w-3.5 h-3.5 text-slate-300" />
          <span class="text-slate-600 text-[11px] font-bold">{{ getShiftTypeName(row.shift_type_id) }}</span>
        </div>
      </template>
      <template #cell-effective_from="{ value }">
        <div class="flex items-center gap-2">
          <Calendar class="w-3.5 h-3.5 text-slate-300" />
          <span class="text-slate-600 text-[11px] font-bold">{{ value || '—' }}</span>
        </div>
      </template>
      <template #cell-is_active="{ value }">
        <span :class="['inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm', value ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-slate-50 text-slate-400 border-slate-100']">
          <CheckCircle2 v-if="value" class="w-3 h-3 mr-1.5" />
          <XCircle v-else class="w-3 h-3 mr-1.5" />
          {{ value ? 'Active' : 'Inactive' }}
        </span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <Button variant="ghost" size="icon" @click="openEdit(row)" class="h-9 w-9 rounded-xl text-slate-400 hover:text-slate-900 hover:bg-slate-100">
            <Pencil class="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" @click="deleteTarget = row" class="h-9 w-9 rounded-xl text-slate-400 hover:text-destructive hover:bg-destructive/10">
            <Trash2 class="w-4 h-4" />
          </Button>
        </div>
      </template>
    </DataTable>

    <Dialog :open="dialogOpen" @update:open="dialogOpen = $event">
      <DialogContent class="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{{ selected ? 'Edit Schedule' : 'Create Shift Schedule' }}</DialogTitle>
          <DialogDescription>
            Step {{ currentStep }} of {{ STEPS.length }}: {{ STEPS[currentStep - 1].label }}
          </DialogDescription>
        </DialogHeader>

        <!-- Step Indicator -->
        <div class="flex items-center justify-between gap-2 py-4">
          <div v-for="(step, idx) of STEPS" :key="step.num" class="flex items-center gap-2 flex-1">
            <button
              @click="goToStep(step.num)"
              :disabled="idx === currentStep - 1"
              :class="[
                'flex items-center justify-center w-10 h-10 rounded-full font-bold text-sm transition-all',
                idx < currentStep - 1 ? 'bg-emerald-500 text-white' :
                idx === currentStep - 1 ? 'bg-slate-900 text-white' :
                'bg-slate-100 text-slate-400 hover:bg-slate-200 cursor-pointer'
              ]"
            >
              <Check v-if="idx < currentStep - 1" class="w-5 h-5" />
              <span v-else>{{ step.num }}</span>
            </button>
            <div v-if="idx < STEPS.length - 1" :class="['flex-1 h-1', idx < currentStep - 1 ? 'bg-emerald-500' : 'bg-slate-200']" />
          </div>
        </div>

        <!-- Step Content -->
        <div class="space-y-6 py-4 min-h-[300px]">
          <!-- Step 1: Basic Info -->
          <div v-show="currentStep === 1" class="space-y-4">
            <FormInput label="Schedule Name" v-model="form.name" required placeholder="e.g. Morning Shift Schedule" />
            <FormSelect
              label="Shift Type"
              v-model="form.shift_type_id"
              required
              :options="shiftTypeOptions"
              placeholder="Select shift type"
            />
            <FormTextarea label="Description" v-model="form.description" placeholder="Describe the schedule purpose or rules…" :rows="4" />
            <p v-if="stepErrors[1]" class="text-sm font-medium text-destructive">{{ stepErrors[1] }}</p>
          </div>

          <!-- Step 2: Clock Windows -->
          <div v-show="currentStep === 2" class="space-y-4">
            <div class="p-4 bg-blue-50 rounded-2xl border border-blue-100">
              <p class="text-xs text-blue-700 font-medium">⏰ Define how early/late employees can clock in/out relative to shift times.</p>
            </div>

            <div class="space-y-3">
              <div class="flex items-center gap-2 mb-2">
                <Clock class="w-4 h-4 text-slate-400" />
                <span class="text-xs font-bold uppercase tracking-widest text-slate-700">Clock-In Window</span>
              </div>
              <div class="grid grid-cols-2 gap-4 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
                <div>
                  <label class="text-xs font-semibold text-slate-600 block mb-2">Minutes before shift start</label>
                  <input type="number" min="0" max="120" v-model.number="clockInBeforeMin"
                    class="w-full h-10 rounded-xl border border-slate-200 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900" />
                  <p v-if="getShiftStartTime()" class="text-[10px] text-slate-500 mt-1">
                    Opens: {{ addMinutesToTime(getShiftStartTime(), -clockInBeforeMin) }} IST
                  </p>
                </div>
                <div>
                  <label class="text-xs font-semibold text-slate-600 block mb-2">Minutes after shift start</label>
                  <input type="number" min="0" max="120" v-model.number="clockInAfterMin"
                    class="w-full h-10 rounded-xl border border-slate-200 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900" />
                  <p v-if="getShiftStartTime()" class="text-[10px] text-slate-500 mt-1">
                    Closes: {{ addMinutesToTime(getShiftStartTime(), clockInAfterMin) }} IST
                  </p>
                </div>
              </div>
            </div>

            <div class="space-y-3">
              <div class="flex items-center gap-2 mb-2">
                <Clock class="w-4 h-4 text-slate-400" />
                <span class="text-xs font-bold uppercase tracking-widest text-slate-700">Clock-Out Window</span>
              </div>
              <div class="grid grid-cols-2 gap-4 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
                <div>
                  <label class="text-xs font-semibold text-slate-600 block mb-2">Minutes before shift end</label>
                  <input type="number" min="0" max="120" v-model.number="clockOutBeforeMin"
                    class="w-full h-10 rounded-xl border border-slate-200 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900" />
                  <p v-if="getShiftEndTime()" class="text-[10px] text-slate-500 mt-1">
                    Opens: {{ addMinutesToTime(getShiftEndTime(), -clockOutBeforeMin) }} IST
                  </p>
                </div>
                <div>
                  <label class="text-xs font-semibold text-slate-600 block mb-2">Minutes after shift end</label>
                  <input type="number" min="0" max="120" v-model.number="clockOutAfterMin"
                    class="w-full h-10 rounded-xl border border-slate-200 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900" />
                  <p v-if="getShiftEndTime()" class="text-[10px] text-slate-500 mt-1">
                    Closes: {{ addMinutesToTime(getShiftEndTime(), clockOutAfterMin) }} IST
                  </p>
                </div>
              </div>
            </div>
            <p v-if="stepErrors[2]" class="text-sm font-medium text-destructive">{{ stepErrors[2] }}</p>
          </div>

          <!-- Step 3: Locations -->
          <div v-show="currentStep === 3" class="space-y-4">
            <div class="p-4 bg-blue-50 rounded-2xl border border-blue-100">
              <p class="text-xs text-blue-700 font-medium">📍 Select the geofences where employees can clock in and out.</p>
            </div>

            <div class="space-y-3">
              <div class="flex items-center gap-2 mb-2">
                <MapPin class="w-4 h-4 text-slate-400" />
                <span class="text-xs font-bold uppercase tracking-widest text-slate-700">Clock-In Locations</span>
              </div>
              <EntitySearchSelect
                v-model="form.allowed_clock_in_location_ids"
                label=""
                entity="local"
                :local-options="locationOptions"
                :multiple="true"
                placeholder="Search and select clock-in locations..."
              />
            </div>

            <div class="space-y-3">
              <div class="flex items-center gap-2 mb-2">
                <MapPin class="w-4 h-4 text-slate-400" />
                <span class="text-xs font-bold uppercase tracking-widest text-slate-700">Clock-Out Locations</span>
              </div>
              <EntitySearchSelect
                v-model="form.allowed_clock_out_location_ids"
                label=""
                entity="local"
                :local-options="locationOptions"
                :multiple="true"
                placeholder="Search and select clock-out locations..."
              />
            </div>
            <p v-if="stepErrors[3]" class="text-sm font-medium text-destructive">{{ stepErrors[3] }}</p>
          </div>

          <!-- Step 4: Off Days & Break Window -->
          <div v-show="currentStep === 4" class="space-y-4">
            <div class="p-4 bg-blue-50 rounded-2xl border border-blue-100">
              <p class="text-xs text-blue-700 font-medium">📅 Define off days and when employees can take breaks.</p>
            </div>

            <div class="space-y-3">
              <div class="flex items-center gap-2 mb-2">
                <CalendarOff class="w-4 h-4 text-slate-400" />
                <span class="text-xs font-bold uppercase tracking-widest text-slate-700">Off Days</span>
              </div>
              <p class="text-xs text-slate-500 mb-3">Employees cannot clock in on off days without an approved request.</p>
              <div class="flex flex-wrap gap-2">
                <label
                  v-for="day in WEEKDAYS"
                  :key="day"
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border cursor-pointer transition-colors"
                  :class="form.off_days?.includes(day)
                    ? 'bg-slate-900 text-white border-slate-900'
                    : 'bg-white text-slate-500 border-slate-200 hover:border-slate-400'"
                >
                  <input
                    type="checkbox"
                    :value="day"
                    v-model="form.off_days"
                    class="sr-only"
                  />
                  {{ day.charAt(0).toUpperCase() + day.slice(1, 3) }}
                </label>
              </div>
            </div>

            <div class="space-y-3">
              <div class="flex items-center gap-2 mb-2">
                <Coffee class="w-4 h-4 text-slate-400" />
                <span class="text-xs font-bold uppercase tracking-widest text-slate-700">Break Window (Optional)</span>
              </div>
              <p class="text-xs text-slate-500 mb-2">If set, HR is notified when a break starts outside this window.</p>
              <div class="grid grid-cols-2 gap-4 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
                <FormInput label="Break Window Start" type="time" v-model="form.break_window_start" />
                <FormInput label="Break Window End" type="time" v-model="form.break_window_end" />
              </div>
            </div>
            <p v-if="stepErrors[4]" class="text-sm font-medium text-destructive">{{ stepErrors[4] }}</p>
          </div>

          <!-- Step 5: Settings -->
          <div v-show="currentStep === 5" class="space-y-4">
            <div class="p-4 bg-blue-50 rounded-2xl border border-blue-100">
              <p class="text-xs text-blue-700 font-medium">⚙️ Configure automatic clock-out and task requirements.</p>
            </div>

            <div class="space-y-3 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
              <div class="flex items-center justify-between mb-3">
                <label class="text-sm font-semibold text-slate-700">Auto Clock-Out Enabled</label>
                <input type="checkbox" v-model="form.auto_clock_out_enabled" class="rounded border-slate-300 w-5 h-5" />
              </div>
              <FormInput v-if="form.auto_clock_out_enabled" label="Auto Clock-Out At" type="time" v-model="form.auto_clock_out_time" />
            </div>

            <div class="space-y-3 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
              <div class="flex items-center justify-between">
                <div>
                  <label class="text-sm font-semibold text-slate-700 block">Tasks Mandatory</label>
                  <p class="text-xs text-slate-500 mt-1">Employees must log tasks before clocking out</p>
                </div>
                <input type="checkbox" v-model="form.tasks_mandatory" class="rounded border-slate-300 w-5 h-5" />
              </div>
            </div>
            <p v-if="stepErrors[5]" class="text-sm font-medium text-destructive">{{ stepErrors[5] }}</p>
          </div>

          <!-- Step 6: Employees & Validity -->
          <div v-show="currentStep === 6" class="space-y-4">
            <div class="p-4 bg-blue-50 rounded-2xl border border-blue-100">
              <p class="text-xs text-blue-700 font-medium">👥 Assign employees and set the validity period.</p>
            </div>

            <div class="space-y-3">
              <div class="flex items-center gap-2 mb-2">
                <Users class="w-4 h-4 text-slate-400" />
                <span class="text-xs font-bold uppercase tracking-widest text-slate-700">Assigned Employees</span>
              </div>
              <EntitySearchSelect
                v-model="form.employee_ids"
                label=""
                entity="employee"
                :multiple="true"
                placeholder="Search and select employees..."
              />
            </div>

            <div class="space-y-3">
              <div class="flex items-center gap-2 mb-2">
                <Calendar class="w-4 h-4 text-slate-400" />
                <span class="text-xs font-bold uppercase tracking-widest text-slate-700">Validity Period</span>
              </div>
              <div class="grid grid-cols-2 gap-4 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
                <FormInput label="Start Date" type="date" v-model="form.effective_from" required />
                <FormInput label="End Date (Optional)" type="date" v-model="form.effective_to" />
              </div>
              <p class="text-xs text-slate-500">Schedule auto-extends 10 days if validity expires.</p>
            </div>
            <p v-if="stepErrors[6]" class="text-sm font-medium text-destructive">{{ stepErrors[6] }}</p>
          </div>
        </div>

        <DialogFooter>
          <div class="flex items-center justify-between gap-4 w-full">
            <p v-if="errorMsg" class="text-xs text-destructive font-medium animate-pulse">{{ errorMsg }}</p>
            <div v-else />
            <div class="flex gap-3">
              <Button
                v-if="currentStep > 1"
                variant="outline"
                @click="prevStep"
                class="rounded-full px-6 h-10 flex items-center gap-2"
              >
                <ChevronLeft class="w-4 h-4" />
                Previous
              </Button>
              <Button
                v-if="currentStep < STEPS.length"
                @click="nextStep"
                class="rounded-full px-6 h-10 bg-slate-900 text-white hover:bg-slate-800 flex items-center gap-2"
              >
                Next
                <ChevronRight class="w-4 h-4" />
              </Button>
              <Button
                v-if="currentStep === STEPS.length"
                @click="save"
                :disabled="saving"
                class="rounded-full px-10 h-10 bg-emerald-600 text-white hover:bg-emerald-700 flex items-center gap-2"
              >
                <Check class="w-4 h-4" />
                {{ saving ? 'Saving…' : selected ? 'Update Schedule' : 'Create Schedule' }}
              </Button>
              <Button variant="outline" @click="dialogOpen = false" class="rounded-full px-6 h-10">
                {{ currentStep === STEPS.length ? 'Close' : 'Cancel' }}
              </Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Shift Schedule?"
      :message="`Remove '${deleteTarget?.name}'? This cannot be undone.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
