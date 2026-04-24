<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Button } from '../ui/button'
import { Pencil, Search, Clock, Calendar, Hash, AlertTriangle } from 'lucide-vue-next'
import { listAttendanceRecords, updateAttendanceRecord } from '../../services/attendance.service'
import type { AttendanceRecord } from '../../services/attendance.service'

const rows = ref<AttendanceRecord[]>([])
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')

// ── Standard edit drawer ──────────────────────────────────────────────────────
const drawerOpen = ref(false)
const selected = ref<AttendanceRecord | null>(null)
const form = ref<Partial<AttendanceRecord>>({})

// ── Early-out review drawer ───────────────────────────────────────────────────
const earlyOutDrawerOpen = ref(false)
const earlyOutRecord = ref<AttendanceRecord | null>(null)
const earlyOutForm = ref<{
  hours_override: string
  decision: 'early_out' | 'half_day'
  notes: string
}>({ hours_override: '', decision: 'early_out', notes: '' })

// ── Filters ───────────────────────────────────────────────────────────────────
const filterEmployeeId = ref('')
const filterDateFrom = ref('')
const filterDateTo = ref('')
const filterStatus = ref('ALL')

const columns = [
  { key: 'employee_id', label: 'Employee'  },
  { key: 'date',        label: 'Date'      },
  { key: 'status',      label: 'Status'    },
  { key: 'clock_in',   label: 'In / Out'  },
  { key: 'work_hours', label: 'Hours'      },
  { key: 'method',     label: 'Method'    },
]

const statusColors: Record<string, string> = {
  present:          'bg-emerald-100/50 text-emerald-700 border-emerald-200/50',
  early_in:         'bg-blue-100/50 text-blue-700 border-blue-200/50',
  late:             'bg-amber-100/50 text-amber-700 border-amber-200/50',
  early_out:        'bg-orange-100/50 text-orange-700 border-orange-200/50',
  pending_review:   'bg-orange-100/50 text-orange-700 border-orange-200/50',
  absent:           'bg-rose-100/50 text-rose-700 border-rose-200/50',
  half_day:         'bg-violet-100/50 text-violet-700 border-violet-200/50',
  auto_closed:      'bg-slate-100/50 text-slate-500 border-slate-200/50',
  request_approved: 'bg-blue-100/50 text-blue-700 border-blue-200/50',
  auto_attendance:  'bg-cyan-100/50 text-cyan-700 border-cyan-200/50',
}

const statusOptions = [
  { value: 'ALL',      label: 'All Status'    },
  { value: 'present',  label: 'Present'       },
  { value: 'early_in', label: 'Early In'      },
  { value: 'late',     label: 'Late'          },
  { value: 'early_out',label: 'Early Out'     },
  { value: 'absent',   label: 'Absent'        },
  { value: 'half_day', label: 'Half Day'      },
  { value: 'auto_closed', label: 'Auto Closed' },
]

const editStatusOptions = [
  { value: 'present',  label: 'Present'  },
  { value: 'early_in', label: 'Early In' },
  { value: 'late',     label: 'Late'     },
  { value: 'early_out',label: 'Early Out'},
  { value: 'absent',   label: 'Absent'   },
  { value: 'half_day', label: 'Half Day' },
]

const earlyOutDecisionOptions = [
  { value: 'early_out', label: 'Keep as Early Out' },
  { value: 'half_day',  label: 'Change to Half Day' },
]

async function load() {
  loading.value = true
  try {
    const res = await listAttendanceRecords({
      employee_id: filterEmployeeId.value || undefined,
      date_from:   filterDateFrom.value  || undefined,
      date_to:     filterDateTo.value    || undefined,
      status:      filterStatus.value === 'ALL' ? undefined : (filterStatus.value || undefined),
      limit: 100,
    })
    rows.value = res.records ?? (res as any).items ?? []
  } catch {}
  finally { loading.value = false }
}

onMounted(load)

// ── Standard edit ─────────────────────────────────────────────────────────────
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

// ── Early-out review ──────────────────────────────────────────────────────────
function openEarlyOutReview(row: AttendanceRecord) {
  earlyOutRecord.value = row
  const actualHours = row.work_hours ?? 0
  earlyOutForm.value = {
    hours_override: actualHours.toFixed(2),
    decision: 'early_out',
    notes: '',
  }
  errorMsg.value = ''
  earlyOutDrawerOpen.value = true
}

async function saveEarlyOutReview() {
  if (!earlyOutRecord.value) return
  saving.value = true; errorMsg.value = ''
  try {
    const payload: Partial<AttendanceRecord> = {
      status: earlyOutForm.value.decision,
      early_out_hours_override: parseFloat(earlyOutForm.value.hours_override) || undefined,
      notes: earlyOutForm.value.notes || undefined,
    }
    await updateAttendanceRecord(earlyOutRecord.value.id, payload)
    earlyOutDrawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { saving.value = false }
}

// ── Formatting ────────────────────────────────────────────────────────────────
function fmtTime(dt?: string) {
  if (!dt) return '—'
  return new Date(dt).toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' })
}

function fmtHours(val?: number | null) {
  if (val == null) return '—'
  return val.toFixed(1)
}

function statusLabel(s: string) {
  return s?.replace(/_/g, ' ')
}
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

    <!-- Table -->
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
          {{ statusLabel(value) }}
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

      <template #cell-work_hours="{ row }">
        <div class="flex flex-col items-start">
          <span class="text-xs font-bold text-slate-900">
            {{ fmtHours(row.early_out_hours_override ?? row.work_hours) }}<span class="text-[10px] font-medium text-muted-foreground ml-0.5">hrs</span>
          </span>
          <span v-if="row.early_out_hours_override != null" class="text-[9px] text-orange-500 font-bold uppercase tracking-widest">HR Override</span>
        </div>
      </template>

      <template #cell-method="{ value }">
        <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{{ value || 'Manual' }}</span>
      </template>

      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <!-- Early Out Review button — shown only for early_out / pending_review -->
          <Button
            v-if="row.status === 'early_out' || row.status === 'pending_review'"
            variant="ghost"
            size="sm"
            @click="openEarlyOutReview(row)"
            class="h-8 px-3 rounded-lg text-orange-600 hover:bg-orange-50 hover:text-orange-700 text-[10px] font-bold uppercase tracking-widest gap-1.5"
          >
            <AlertTriangle class="w-3.5 h-3.5" />
            Review
          </Button>
          <!-- Standard edit button -->
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

    <!-- ── Standard Edit Drawer ─────────────────────────────────────────────── -->
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
              <p class="font-semibold text-slate-900 font-mono text-xs">{{ selected.employee_id }}</p>
            </div>
            <div>
              <p class="text-[11px] text-muted-foreground mb-0.5">Computed Hours</p>
              <p class="font-semibold text-slate-900">{{ fmtHours(selected.work_hours) }} hrs</p>
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

    <!-- ── Early-Out Review Drawer ──────────────────────────────────────────── -->
    <SlideDrawer :open="earlyOutDrawerOpen" title="Review Early Clock-out" width="w-full max-w-lg" @close="earlyOutDrawerOpen = false">
      <div class="space-y-6">
        <!-- Record summary -->
        <div v-if="earlyOutRecord" class="p-4 rounded-2xl bg-orange-50/60 border border-orange-200/60 space-y-4">
          <div class="flex items-center gap-2">
            <AlertTriangle class="w-4 h-4 text-orange-500" />
            <span class="text-[10px] font-black text-orange-700 uppercase tracking-widest">Early Clock-out</span>
            <span class="ml-auto text-[10px] font-bold text-slate-500">{{ earlyOutRecord.date }}</span>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div class="bg-white/70 rounded-xl p-3 text-center">
              <p class="text-[9px] text-muted-foreground font-bold uppercase tracking-widest mb-1">Clock In</p>
              <p class="text-sm font-black text-slate-900">{{ fmtTime(earlyOutRecord.effective_clock_in_at ?? earlyOutRecord.clock_in) }}</p>
            </div>
            <div class="bg-white/70 rounded-xl p-3 text-center">
              <p class="text-[9px] text-muted-foreground font-bold uppercase tracking-widest mb-1">Clock Out</p>
              <p class="text-sm font-black text-orange-600">{{ fmtTime(earlyOutRecord.clock_out) }}</p>
            </div>
            <div class="bg-white/70 rounded-xl p-3 text-center">
              <p class="text-[9px] text-muted-foreground font-bold uppercase tracking-widest mb-1">Actual Hours</p>
              <p class="text-sm font-black text-slate-900">{{ fmtHours(earlyOutRecord.work_hours) }}</p>
            </div>
          </div>

          <div v-if="earlyOutRecord.notes" class="bg-white/60 rounded-xl p-3">
            <p class="text-[9px] text-muted-foreground font-bold uppercase tracking-widest mb-1">Employee Reason</p>
            <p class="text-xs text-slate-700">{{ earlyOutRecord.notes }}</p>
          </div>
        </div>

        <!-- HR decision form -->
        <div class="space-y-4">
          <div>
            <label class="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1.5 block">Approved Work Hours</label>
            <div class="relative">
              <input
                v-model="earlyOutForm.hours_override"
                type="number"
                step="0.25"
                min="0"
                max="24"
                class="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 pr-12"
                placeholder="e.g. 4.00"
              />
              <span class="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-bold text-slate-400">hrs</span>
            </div>
            <p class="text-[10px] text-muted-foreground mt-1">Override the computed work hours for payroll. Actual hours were {{ fmtHours(earlyOutRecord?.work_hours) }} hrs.</p>
          </div>

          <FormSelect
            label="Decision"
            :modelValue="earlyOutForm.decision"
            @update:modelValue="earlyOutForm.decision = $event as 'early_out' | 'half_day'"
            :options="earlyOutDecisionOptions"
          />

          <FormInput
            label="HR Notes"
            :modelValue="earlyOutForm.notes"
            @update:modelValue="earlyOutForm.notes = $event"
            placeholder="Optional review remarks..."
          />
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="errorMsg" class="text-[11px] text-destructive font-bold uppercase tracking-tight">{{ errorMsg }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="earlyOutDrawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button
              @click="saveEarlyOutReview"
              :disabled="saving"
              class="rounded-full px-8 bg-orange-600 text-white hover:bg-orange-700 shadow-lg shadow-orange-200 dark:shadow-none"
            >
              {{ saving ? 'Saving...' : 'Submit Review' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
