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
} from 'lucide-vue-next'
import { listShiftSchedules, createShiftSchedule, updateShiftSchedule, deleteShiftSchedule } from '../../services/shift-schedule.service'
import type { ShiftSchedule } from '../../services/shift-schedule.service'
import { listShiftTypes } from '../../services/shift-type.service'
import { listShiftLocations } from '../../services/shift-location.service'
import { listEmployees } from '../../services/employee.service'

interface ShiftType { id: string; name: string }
interface ShiftLocation { id: string; name: string }
interface Employee { id: string; first_name: string; last_name: string; employee_code: string }

const rows = ref<ShiftSchedule[]>([])
const loading = ref(false)
const dialogOpen = ref(false)
const form = ref<Partial<ShiftSchedule>>({
  allowed_clock_in_location_ids: [],
  allowed_clock_out_location_ids: [],
  auto_clock_out_enabled: true,
  tasks_mandatory: false,
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
  ...shiftTypes.value.map(type => ({ value: type.id, label: type.name }))
])

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
    employees.value = emps
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
  }
  errorMsg.value = ''
  dialogOpen.value = true
}

function openEdit(row: ShiftSchedule) {
  selected.value = row
  form.value = { ...row }
  errorMsg.value = ''
  dialogOpen.value = true
}

async function save() {
  saving.value = true
  errorMsg.value = ''
  try {
    if (selected.value) {
      await updateShiftSchedule(selected.value.id, form.value)
    } else {
      await createShiftSchedule(form.value)
    }
    dialogOpen.value = false
    load()
  } catch (e: any) {
    errorMsg.value = e.message
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
      <DialogContent class="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{{ selected ? 'Edit Schedule' : 'New Shift Schedule' }}</DialogTitle>
          <DialogDescription>
            Configure the schedule with shift type, locations, employees, and timing rules.
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-6 py-4">
          <div class="grid grid-cols-2 gap-4">
            <FormInput label="Schedule Name" v-model="form.name" required placeholder="e.g. Morning Shift Schedule" />
            <FormSelect 
              label="Shift Type" 
              v-model="form.shift_type_id" 
              required
              :options="shiftTypeOptions"
              placeholder="Select shift type"
            />
          </div>

          <FormTextarea label="Description" v-model="form.description" placeholder="Describe the schedule purpose or rules…" />

          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <Clock class="w-4 h-4 text-slate-400" />
              <span class="text-[10px] font-black uppercase tracking-widest text-slate-700">Clock-In Window</span>
            </div>
            <div class="grid grid-cols-2 gap-4 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
              <FormInput label="Start Time" type="time" v-model="form.clock_in_start_time" required />
              <FormInput label="End Time" type="time" v-model="form.clock_in_end_time" required />
            </div>
          </div>

          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <Clock class="w-4 h-4 text-slate-400" />
              <span class="text-[10px] font-black uppercase tracking-widest text-slate-700">Clock-Out Window</span>
            </div>
            <div class="grid grid-cols-2 gap-4 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
              <FormInput label="Start Time" type="time" v-model="form.clock_out_start_time" required />
              <FormInput label="End Time" type="time" v-model="form.clock_out_end_time" required />
            </div>
          </div>

          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <MapPin class="w-4 h-4 text-slate-400" />
              <span class="text-[10px] font-black uppercase tracking-widest text-slate-700">Allowed Clock-In Locations</span>
            </div>
            <div class="p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
              <div class="grid grid-cols-2 gap-2">
                <label v-for="location in shiftLocations" :key="location.id" class="flex items-center gap-2">
                  <input type="checkbox" :value="location.id" v-model="form.allowed_clock_in_location_ids" class="rounded border-slate-300" />
                  <span class="text-sm">{{ location.name }}</span>
                </label>
              </div>
            </div>
          </div>

          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <MapPin class="w-4 h-4 text-slate-400" />
              <span class="text-[10px] font-black uppercase tracking-widest text-slate-700">Allowed Clock-Out Locations</span>
            </div>
            <div class="p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
              <div class="grid grid-cols-2 gap-2">
                <label v-for="location in shiftLocations" :key="location.id" class="flex items-center gap-2">
                  <input type="checkbox" :value="location.id" v-model="form.allowed_clock_out_location_ids" class="rounded border-slate-300" />
                  <span class="text-sm">{{ location.name }}</span>
                </label>
              </div>
            </div>
          </div>

          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <CalendarClock class="w-4 h-4 text-slate-400" />
              <span class="text-[10px] font-black uppercase tracking-widest text-slate-700">Schedule Settings</span>
            </div>
            <div class="space-y-3 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
              <div class="flex items-center justify-between">
                <label class="text-sm font-medium">Auto Clock-Out</label>
                <input type="checkbox" v-model="form.auto_clock_out_enabled" class="rounded border-slate-300" />
              </div>
              <FormInput v-if="form.auto_clock_out_enabled" label="Auto Clock-Out At" type="time" v-model="form.auto_clock_out_time" />
              <div class="flex items-center gap-2 pt-2">
                <input type="checkbox" v-model="form.tasks_mandatory" class="rounded border-slate-300" />
                <label class="text-sm font-medium">Tasks Mandatory</label>
              </div>
            </div>
          </div>

          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <Calendar class="w-4 h-4 text-slate-400" />
              <span class="text-[10px] font-black uppercase tracking-widest text-slate-700">Validity Period</span>
            </div>
            <div class="grid grid-cols-2 gap-4 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
              <FormInput label="Start Date" type="date" v-model="form.effective_from" />
              <FormInput label="End Date" type="date" v-model="form.effective_to" />
            </div>
          </div>
        </div>

        <DialogFooter>
          <div class="flex items-center justify-between gap-4 w-full">
            <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
            <div v-else />
            <div class="flex gap-3">
              <Button variant="outline" @click="dialogOpen = false" class="rounded-full px-6 h-10">Cancel</Button>
              <Button @click="save" :disabled="saving" class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800">
                {{ saving ? 'Saving…' : selected ? 'Update' : 'Create Schedule' }}
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
