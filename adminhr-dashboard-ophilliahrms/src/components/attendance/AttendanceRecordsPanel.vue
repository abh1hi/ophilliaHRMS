<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Button } from '../ui/button'
import { Pencil, Search, Clock, Calendar, Hash } from 'lucide-vue-next'
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
const filterStatus = ref('ALL')

const columns = [
  { key: 'employee_id', label: 'Employee' },
  { key: 'date',        label: 'Date'        },
  { key: 'status',      label: 'Status'      },
  { key: 'clock_in',   label: 'In / Out'    }, // Combined In/Out
  { key: 'work_hours', label: 'Hours'        },
  { key: 'method',     label: 'Method'      },
]

const statusColors: Record<string, string> = {
  present:          'bg-emerald-100/50 text-emerald-700 border-emerald-200/50',
  late:             'bg-amber-100/50 text-amber-700 border-amber-200/50',
  absent:           'bg-rose-100/50 text-rose-700 border-rose-200/50',
  half_day:         'bg-violet-100/50 text-violet-700 border-violet-200/50',
  auto_closed:      'bg-slate-100/50 text-slate-500 border-slate-200/50',
  request_approved: 'bg-blue-100/50 text-blue-700 border-blue-200/50',
  auto_attendance:  'bg-cyan-100/50 text-cyan-700 border-cyan-200/50',
}

async function load() {
  loading.value = true
  try {
    const res = await listAttendanceRecords({
      employee_id: filterEmployeeId.value || undefined,
      date_from: filterDateFrom.value || undefined,
      date_to: filterDateTo.value || undefined,
      status: filterStatus.value === 'ALL' ? undefined : (filterStatus.value || undefined),
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

const statusOptions = [
  { value: 'ALL', label: 'All Status' },
  { value: 'present', label: 'Present' },
  { value: 'late', label: 'Late' },
  { value: 'absent', label: 'Absent' },
  { value: 'half_day', label: 'Half Day' },
  { value: 'auto_closed', label: 'Auto Closed' },
]

const editStatusOptions = [
  { value: 'present', label: 'Present' },
  { value: 'late', label: 'Late' },
  { value: 'absent', label: 'Absent' },
  { value: 'half_day', label: 'Half Day' },
]
</script>

<template>
  <div class="space-y-8">
    <PageHeader title="Attendance Records" subtitle="Daily attendance data ledger and corrections" />

    <!-- Filters -->
    <div class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-6 shadow-sm">
      <div class="flex flex-wrap items-end gap-4">
        <div class="flex-1 min-w-[200px]">
          <FormInput label="Employee" :modelValue="filterEmployeeId" @update:modelValue="filterEmployeeId = $event" placeholder="Search UUID..." />
        </div>
        <div class="w-40">
          <FormInput label="From Date" type="date" :modelValue="filterDateFrom" @update:modelValue="filterDateFrom = $event" />
        </div>
        <div class="w-40">
          <FormInput label="To Date" type="date" :modelValue="filterDateTo" @update:modelValue="filterDateTo = $event" />
        </div>
        <div class="w-44">
          <FormSelect label="Status" :modelValue="filterStatus" @update:modelValue="filterStatus = $event" :options="statusOptions" />
        </div>
        <Button @click="load" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
          <Search class="w-4 h-4 mr-2" /> Search
        </Button>
      </div>
    </div>

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="false" empty-text="No attendance records found.">
      <template #cell-employee_id="{ value }">
        <div class="flex items-center gap-2">
          <Hash class="w-3 h-3 text-muted-foreground" />
          <span class="font-mono text-[10px] text-muted-foreground">{{ String(value).slice(0, 13) }}…</span>
        </div>
      </template>
      <template #cell-date="{ value }">
        <div class="flex items-center gap-2">
          <Calendar class="w-3 h-3 text-muted-foreground" />
          <span class="text-xs font-bold text-slate-900 dark:text-slate-100">{{ value }}</span>
        </div>
      </template>
      <template #cell-status="{ value }">
        <span 
          :class="[
            'inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm', 
            statusColors[value] ?? 'bg-slate-100 text-slate-500 border-slate-200'
          ]"
        >
          {{ value?.replace('_', ' ') }}
        </span>
      </template>
      <template #cell-clock_in="{ row }">
        <div class="flex items-center gap-2 text-[11px] font-medium text-slate-600 dark:text-slate-400">
          <Clock class="w-3 h-3 text-muted-foreground" />
          <span>{{ fmtTime(row.clock_in) }}</span>
          <span class="text-slate-300">→</span>
          <span>{{ fmtTime(row.clock_out) }}</span>
        </div>
      </template>
      <template #cell-work_hours="{ value }">
        <span class="text-xs font-bold text-slate-900">{{ value != null ? value.toFixed(1) : '—' }}<span class="text-[10px] font-medium text-muted-foreground ml-0.5">hrs</span></span>
      </template>
      <template #cell-method="{ value }">
        <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{{ value || 'Manual' }}</span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end">
          <Button 
            variant="ghost" 
            size="icon" 
            @click="openEdit(row)" 
            class="h-8 w-8 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-900"
          >
            <Pencil class="w-4 h-4" />
          </Button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" title="Correct Attendance Record" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6">
        <div v-if="selected" class="p-4 rounded-2xl bg-muted/30 border border-dashed text-sm space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Record Info</span>
            <span class="text-[10px] font-bold text-slate-900">{{ selected.date }}</span>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-[11px] text-muted-foreground mb-0.5">Employee ID</p>
              <p class="font-semibold text-slate-900">{{ selected.employee_id }}</p>
            </div>
            <div>
              <p class="text-[11px] text-muted-foreground mb-0.5">Computed Hours</p>
              <p class="font-semibold text-slate-900">{{ selected.work_hours?.toFixed(2) ?? '0.00' }} hrs</p>
            </div>
          </div>
        </div>

        <FormSelect 
          label="Adjust Status" 
          :modelValue="form.status" 
          @update:modelValue="form.status = $event" 
          :options="editStatusOptions"
        />
        
        <FormInput 
          label="Correction Notes" 
          :modelValue="form.notes" 
          @update:modelValue="form.notes = $event" 
          placeholder="Reason for manual adjustment..." 
        />
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="errorMsg" class="text-[11px] text-destructive font-bold uppercase tracking-tight">{{ errorMsg }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800 shadow-lg shadow-slate-200 dark:shadow-none">
              {{ saving ? 'Updating...' : 'Save Correction' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
