<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import { PencilIcon } from 'lucide-vue-next'
import { listAttendanceRecords, updateAttendanceRecord } from '../../services/attendance.service'
import type { AttendanceRecord } from '../../services/attendance.service'

const rows = ref<AttendanceRecord[]>([])
const loading = ref(false)
const drawerOpen = ref(false)
const selected = ref<AttendanceRecord | null>(null)
const form = ref<Partial<AttendanceRecord>>({})
const saving = ref(false)
const errorMsg = ref('')

// Filter state
const filterEmployeeId = ref('')
const filterDateFrom = ref('')
const filterDateTo = ref('')
const filterStatus = ref('')

const columns = [
  { key: 'employee_id', label: 'Employee ID' },
  { key: 'date',        label: 'Date'        },
  { key: 'status',      label: 'Status'      },
  { key: 'clock_in',   label: 'Clock In'    },
  { key: 'clock_out',  label: 'Clock Out'   },
  { key: 'work_hours', label: 'Hours'        },
  { key: 'method',     label: 'Method'      },
]

const statusColors: Record<string, string> = {
  present:          'bg-emerald-100 text-emerald-700',
  late:             'bg-amber-100 text-amber-700',
  absent:           'bg-rose-100 text-rose-700',
  half_day:         'bg-violet-100 text-violet-700',
  auto_closed:      'bg-slate-100 text-slate-500',
  request_approved: 'bg-blue-100 text-blue-700',
  auto_attendance:  'bg-cyan-100 text-cyan-700',
}

async function load() {
  loading.value = true
  try {
    const res = await listAttendanceRecords({
      employee_id: filterEmployeeId.value || undefined,
      date_from: filterDateFrom.value || undefined,
      date_to: filterDateTo.value || undefined,
      status: filterStatus.value || undefined,
      limit: 100,
    })
    rows.value = res.records ?? (res as any).items ?? []
  } catch {}
  finally { loading.value = false }
}

onMounted(load)

function openEdit(row: AttendanceRecord) {
  selected.value = row
  form.value = { notes: row.notes, status: row.status }
  errorMsg.value = ''
  drawerOpen.value = true
}

async function save() {
  if (!selected.value) return
  saving.value = true; errorMsg.value = ''
  try {
    await updateAttendanceRecord(selected.value.id, form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { saving.value = false }
}

function fmtTime(dt?: string) {
  if (!dt) return '—'
  return new Date(dt).toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Attendance Records" subtitle="View and correct attendance data" />

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[20px] px-5 py-4 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
      <input v-model="filterEmployeeId" placeholder="Employee ID" class="text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none focus:ring-2 focus:ring-slate-200 w-64" />
      <input type="date" v-model="filterDateFrom" class="text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none focus:ring-2 focus:ring-slate-200" />
      <span class="text-slate-300 self-center">→</span>
      <input type="date" v-model="filterDateTo" class="text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none focus:ring-2 focus:ring-slate-200" />
      <select v-model="filterStatus" class="text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none focus:ring-2 focus:ring-slate-200">
        <option value="">All Status</option>
        <option value="present">Present</option>
        <option value="late">Late</option>
        <option value="absent">Absent</option>
        <option value="half_day">Half Day</option>
        <option value="auto_closed">Auto Closed</option>
      </select>
      <button @click="load" class="px-5 py-2 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition-colors">Search</button>
    </div>

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="false" empty-text="No records found.">
      <template #cell-employee_id="{ value }">
        <span class="font-mono text-xs text-slate-400">{{ String(value).slice(0, 8) }}…</span>
      </template>
      <template #cell-status="{ value }">
        <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize', statusColors[value] ?? 'bg-slate-100 text-slate-500']">{{ value }}</span>
      </template>
      <template #cell-clock_in="{ value }">
        <span class="text-sm text-slate-600">{{ fmtTime(value) }}</span>
      </template>
      <template #cell-clock_out="{ value }">
        <span class="text-sm text-slate-600">{{ fmtTime(value) }}</span>
      </template>
      <template #cell-work_hours="{ value }">
        <span class="text-sm text-slate-700">{{ value != null ? `${value}h` : '—' }}</span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end">
          <button @click="openEdit(row)" class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"><PencilIcon class="w-4 h-4" /></button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" title="Edit Record" width="w-full max-w-md" @close="drawerOpen = false">
      <div class="space-y-5">
        <div>
          <p class="text-xs font-semibold text-slate-500 mb-1">Status</p>
          <select v-model="form.status" class="w-full text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none focus:ring-2 focus:ring-slate-200">
            <option value="present">Present</option>
            <option value="late">Late</option>
            <option value="absent">Absent</option>
            <option value="half_day">Half Day</option>
          </select>
        </div>
        <FormInput label="Notes" :modelValue="form.notes" @update:modelValue="form.notes = $event" placeholder="Optional correction note" />
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="drawerOpen = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="save" :disabled="saving" class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
