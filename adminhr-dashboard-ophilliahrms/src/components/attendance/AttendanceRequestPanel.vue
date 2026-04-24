<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import { Button } from '../ui/button'
import { Checkbox } from '../ui/checkbox'
import { Label } from '../ui/label'
import { Check, X, Ban, Search, Info, Calendar, Clock, Briefcase } from 'lucide-vue-next'
import {
  listAttendanceRequests,
  createAttendanceRequest,
  cancelAttendanceRequest,
  reviewAttendanceRequest,
} from '../../services/attendance-request.service'
import type { AttendanceRequest } from '../../services/attendance-request.service'

// ── Tab state ─────────────────────────────────────────────────────────────────
type Tab = 'general' | 'late_clockin' | 'off_day'
const activeTab = ref<Tab>('general')

// ── Data ──────────────────────────────────────────────────────────────────────
const allRows = ref<AttendanceRequest[]>([])
const loading = ref(false)
const saving = ref(false)
const reviewing = ref(false)
const cancelling = ref(false)
const bulkProcessing = ref(false)
const errorMsg = ref('')

// ── Drawer state ──────────────────────────────────────────────────────────────
const createDrawerOpen = ref(false)
const reviewTarget = ref<AttendanceRequest | null>(null)
const cancelTarget = ref<AttendanceRequest | null>(null)
const selectedIds = ref(new Set<string>())
const form = ref<Partial<AttendanceRequest>>({})

// Review form fields
const reviewNote = ref('')
const reviewMarkAs = ref<'normal_with_late_flag' | 'half_day'>('normal_with_late_flag')
const offDayWorkType = ref<'normal' | 'overtime'>('normal')
const offDayOtRate = ref<string>('1.5')
const customOtRate = ref<string>('')

// Filter
const filterStatus = ref('')

// ── Computed rows per tab ─────────────────────────────────────────────────────
const tabRows = computed(() => {
  if (activeTab.value === 'late_clockin') {
    return allRows.value.filter(r => r.request_type === 'late_clockin' || r.reason === 'late_clockin')
  }
  if (activeTab.value === 'off_day') {
    return allRows.value.filter(r => r.request_type === 'off_day_work' || r.is_off_day_request)
  }
  return allRows.value.filter(
    r => !r.request_type || r.request_type === 'general' || (r.reason !== 'late_clockin' && r.reason !== 'off_day_work')
  )
})

const isLateReview = computed(() => reviewTarget.value?.request_type === 'late_clockin' || reviewTarget.value?.reason === 'late_clockin')
const isOffDayReview = computed(() => reviewTarget.value?.request_type === 'off_day_work' || reviewTarget.value?.is_off_day_request)

const effectiveOtRate = computed(() => {
  if (offDayOtRate.value === 'custom') return parseFloat(customOtRate.value) || 0
  return parseFloat(offDayOtRate.value)
})

// ── Column definitions ────────────────────────────────────────────────────────
const generalColumns = [
  { key: 'employee_id', label: 'Employee' },
  { key: 'from_date',   label: 'Period'   },
  { key: 'reason',      label: 'Reason'   },
  { key: 'status',      label: 'Status'   },
]

const lateColumns = [
  { key: 'employee_id', label: 'Employee'  },
  { key: 'for_date',    label: 'Date'      },
  { key: 'explanation', label: 'Reason'    },
  { key: 'status',      label: 'Status'    },
]

const offDayColumns = [
  { key: 'employee_id',      label: 'Employee'  },
  { key: 'for_date',         label: 'Date'      },
  { key: 'off_day_work_type',label: 'Work Type' },
  { key: 'status',           label: 'Status'    },
]

const activeColumns = computed(() => {
  if (activeTab.value === 'late_clockin') return lateColumns
  if (activeTab.value === 'off_day') return offDayColumns
  return generalColumns
})

// ── Status / option maps ──────────────────────────────────────────────────────
const statusColors: Record<string, string> = {
  pending:   'bg-amber-100/50 text-amber-700 border-amber-200/50',
  approved:  'bg-emerald-100/50 text-emerald-700 border-emerald-200/50',
  rejected:  'bg-rose-100/50 text-rose-600 border-rose-200/50',
  cancelled: 'bg-slate-100/50 text-slate-500 border-slate-200/50',
}

const reasonLabels: Record<string, string> = {
  on_site_duty:   'On-site Duty',
  work_from_home: 'Work From Home',
  other:          'Other',
  late_clockin:   'Late Clock-in',
  off_day_work:   'Off-day Work',
}

const workTypeLabels: Record<string, string> = {
  normal:   'Normal Pay',
  overtime: 'Overtime Pay',
}

const statusOptions = [
  { value: '',          label: 'All Status'  },
  { value: 'pending',   label: 'Pending'     },
  { value: 'approved',  label: 'Approved'    },
  { value: 'rejected',  label: 'Rejected'    },
  { value: 'cancelled', label: 'Cancelled'   },
]

const reasonOptions = [
  { value: 'on_site_duty',   label: 'On-site Duty'   },
  { value: 'work_from_home', label: 'Work From Home'  },
  { value: 'other',          label: 'Other'           },
]

const markAsOptions = [
  { value: 'normal_with_late_flag', label: 'Normal Attendance (with Late flag)' },
  { value: 'half_day',              label: 'Mark as Half Day'                   },
]

const offDayWorkTypeOptions = [
  { value: 'normal',   label: 'Normal Attendance'  },
  { value: 'overtime', label: 'Overtime'            },
]

const otRateOptions = [
  { value: '1',      label: '1× (Regular Pay)'   },
  { value: '1.5',    label: '1.5× (Time & Half)' },
  { value: '2',      label: '2× (Double Pay)'    },
  { value: 'custom', label: 'Custom Rate…'        },
]

// ── Load ──────────────────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const res = await listAttendanceRequests({ status: filterStatus.value || undefined, limit: 200 })
    allRows.value = res.requests
  } catch {}
  finally { loading.value = false }
}

onMounted(load)

// ── Create ────────────────────────────────────────────────────────────────────
function openCreate() {
  form.value = { reason: 'on_site_duty', include_holidays: 0, half_day: 0 }
  errorMsg.value = ''
  createDrawerOpen.value = true
}

async function saveCreate() {
  saving.value = true; errorMsg.value = ''
  try {
    await createAttendanceRequest(form.value)
    createDrawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { saving.value = false }
}

// ── Cancel ────────────────────────────────────────────────────────────────────
async function confirmCancel() {
  if (!cancelTarget.value) return
  cancelling.value = true
  try { await cancelAttendanceRequest(cancelTarget.value.id); cancelTarget.value = null; load() }
  catch {} finally { cancelling.value = false }
}

// ── Review ────────────────────────────────────────────────────────────────────
function openReview(row: AttendanceRequest) {
  reviewTarget.value = row
  reviewNote.value = ''
  reviewMarkAs.value = 'normal_with_late_flag'
  offDayWorkType.value = 'normal'
  offDayOtRate.value = '1.5'
  customOtRate.value = ''
  errorMsg.value = ''
}

async function doReview(status: 'approved' | 'rejected') {
  if (!reviewTarget.value) return
  reviewing.value = true; errorMsg.value = ''
  try {
    const payload: Parameters<typeof reviewAttendanceRequest>[1] = {
      status,
      review_note: reviewNote.value || undefined,
    }
    if (isLateReview.value && status === 'approved') {
      payload.mark_as = reviewMarkAs.value
    }
    if (isOffDayReview.value && status === 'approved') {
      payload.off_day_work_type = offDayWorkType.value
      if (offDayWorkType.value === 'overtime') {
        payload.off_day_ot_rate = effectiveOtRate.value
      }
    }
    await reviewAttendanceRequest(reviewTarget.value.id, payload)
    reviewTarget.value = null; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { reviewing.value = false }
}

// ── Bulk ──────────────────────────────────────────────────────────────────────
function toggleSelect(id: string) {
  if (selectedIds.value.has(id)) selectedIds.value.delete(id)
  else selectedIds.value.add(id)
  selectedIds.value = new Set(selectedIds.value)
}

async function bulkReview(status: 'approved' | 'rejected') {
  bulkProcessing.value = true
  try {
    for (const id of selectedIds.value) {
      await reviewAttendanceRequest(id, { status })
    }
    selectedIds.value = new Set(); load()
  } catch {} finally { bulkProcessing.value = false }
}
</script>

<template>
  <div class="space-y-8">
    <PageHeader
      title="Attendance Adjustments"
      subtitle="Submit and review attendance correction requests"
      action-label="New Request"
      @action="openCreate"
    />

    <!-- Tab Bar -->
    <div class="flex items-center gap-1 bg-slate-100 rounded-2xl p-1 w-fit">
      <button
        v-for="tab in ([
          { key: 'general',     label: 'General',          icon: Info    },
          { key: 'late_clockin',label: 'Late Clock-in',    icon: Clock   },
          { key: 'off_day',     label: 'Off Day Requests', icon: Briefcase },
        ] as const)"
        :key="tab.key"
        @click="activeTab = tab.key"
        :class="[
          'flex items-center gap-2 px-4 py-2 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all',
          activeTab === tab.key
            ? 'bg-white text-slate-900 shadow-sm'
            : 'text-slate-400 hover:text-slate-700'
        ]"
      >
        <component :is="tab.icon" class="w-3.5 h-3.5" />
        {{ tab.label }}
      </button>
    </div>

    <!-- Filter -->
    <div class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-6 shadow-sm">
      <div class="flex items-end gap-4">
        <div class="w-48">
          <FormSelect label="Filter Status" v-model="filterStatus" :options="statusOptions" />
        </div>
        <Button @click="load" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
          <Search class="w-4 h-4 mr-2" /> Apply Filter
        </Button>
      </div>
    </div>

    <!-- Bulk action toolbar -->
    <div v-if="selectedIds.size > 0" class="flex items-center gap-3 px-5 py-3 bg-white border border-slate-200 rounded-2xl shadow-md">
      <span class="text-sm font-semibold text-slate-700">{{ selectedIds.size }} selected</span>
      <Button @click="bulkReview('approved')" :disabled="bulkProcessing" class="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white h-8 text-[11px] font-bold uppercase tracking-widest px-4">
        Approve All
      </Button>
      <Button @click="bulkReview('rejected')" :disabled="bulkProcessing" variant="destructive" class="rounded-xl h-8 text-[11px] font-bold uppercase tracking-widest px-4">
        Reject All
      </Button>
      <Button @click="selectedIds = new Set()" variant="ghost" class="rounded-xl h-8 text-[11px] font-bold uppercase tracking-widest px-4 text-slate-500">
        Clear
      </Button>
    </div>

    <!-- Table -->
    <DataTable :columns="activeColumns" :rows="tabRows" :loading="loading" :searchable="false" empty-text="No requests found.">
      <template #cell-employee_id="{ value }">
        <span class="font-mono text-[10px] text-muted-foreground bg-muted/30 px-2 py-0.5 rounded border border-dashed">{{ String(value).slice(0, 13) }}…</span>
      </template>
      <template #cell-from_date="{ row }">
        <div class="flex items-center gap-2 text-[11px] font-bold text-slate-900">
          <Calendar class="w-3.5 h-3.5 text-muted-foreground" />
          <span>{{ row.from_date }}</span>
          <span class="text-slate-300 font-normal">→</span>
          <span>{{ row.to_date }}</span>
        </div>
      </template>
      <template #cell-for_date="{ value }">
        <div class="flex items-center gap-2 text-[11px] font-bold text-slate-900">
          <Calendar class="w-3.5 h-3.5 text-muted-foreground" />
          <span>{{ value || '—' }}</span>
        </div>
      </template>
      <template #cell-reason="{ value }">
        <span class="text-xs font-medium text-slate-600 dark:text-slate-400">{{ reasonLabels[value] ?? value }}</span>
      </template>
      <template #cell-explanation="{ value }">
        <span class="text-xs text-slate-600 truncate max-w-[200px] block">{{ value || '—' }}</span>
      </template>
      <template #cell-off_day_work_type="{ value }">
        <span class="text-[10px] font-bold uppercase tracking-widest"
          :class="value === 'overtime' ? 'text-amber-600' : 'text-slate-600'">
          {{ workTypeLabels[value] ?? value ?? '—' }}
        </span>
      </template>
      <template #cell-status="{ value }">
        <span
          :class="[
            'inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm',
            statusColors[value] ?? 'bg-slate-100 text-slate-500 border-slate-200'
          ]"
        >
          {{ value }}
        </span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <Checkbox
            v-if="row.status === 'pending'"
            :checked="selectedIds.has(row.id)"
            @update:checked="toggleSelect(row.id)"
            class="mr-1"
          />
          <template v-if="row.status === 'pending'">
            <Button
              variant="ghost"
              size="icon"
              @click="openReview(row)"
              class="h-8 w-8 rounded-lg hover:bg-emerald-50 text-slate-400 hover:text-emerald-700"
              title="Review"
            >
              <Check class="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              @click="cancelTarget = row"
              class="h-8 w-8 rounded-lg hover:bg-rose-50 text-slate-400 hover:text-rose-600"
              title="Cancel"
            >
              <Ban class="w-4 h-4" />
            </Button>
          </template>
        </div>
      </template>
    </DataTable>

    <!-- ── Create Drawer ──────────────────────────────────────────────────── -->
    <SlideDrawer :open="createDrawerOpen" title="New Attendance Request" width="w-full max-w-lg" @close="createDrawerOpen = false">
      <div class="space-y-6">
        <FormInput label="Employee ID" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" required placeholder="Employee UUID" />
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Start Date" type="date" :modelValue="form.from_date" @update:modelValue="form.from_date = $event || undefined" required />
          <FormInput label="End Date" type="date" :modelValue="form.to_date" @update:modelValue="form.to_date = $event || undefined" required />
        </div>
        <FormSelect label="Request Reason" v-model="form.reason" :options="reasonOptions" />
        <FormTextarea label="Explanation" :modelValue="form.explanation" @update:modelValue="form.explanation = $event" placeholder="Provide context for this request..." />
        <div class="grid grid-cols-2 gap-6 bg-muted/30 p-5 rounded-3xl border border-dashed">
          <div class="flex items-center space-x-2">
            <Checkbox id="req-hol" :checked="!!form.include_holidays" @update:checked="form.include_holidays = $event ? 1 : 0" />
            <Label for="req-hol" class="text-[11px] font-bold uppercase tracking-wider text-muted-foreground cursor-pointer">Include Holidays</Label>
          </div>
          <div class="flex items-center space-x-2">
            <Checkbox id="req-half" :checked="!!form.half_day" @update:checked="form.half_day = $event ? 1 : 0" />
            <Label for="req-half" class="text-[11px] font-bold uppercase tracking-wider text-muted-foreground cursor-pointer">Half Day Request</Label>
          </div>
        </div>
        <div v-if="form.half_day" class="animate-in fade-in slide-in-from-top-2">
          <FormInput label="Specific Half-Day Date" type="date" :modelValue="form.half_day_date" @update:modelValue="form.half_day_date = $event || undefined" />
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="errorMsg" class="text-[11px] text-destructive font-bold uppercase tracking-tight">{{ errorMsg }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="createDrawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="saveCreate" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800 shadow-lg shadow-slate-200">
              {{ saving ? 'Submitting...' : 'Submit Request' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- ── Review Drawer ──────────────────────────────────────────────────── -->
    <SlideDrawer :open="!!reviewTarget" title="Process Request" width="w-full max-w-lg" @close="reviewTarget = null">
      <div v-if="reviewTarget" class="space-y-6">
        <!-- Summary -->
        <div class="p-5 rounded-3xl bg-muted/30 border border-dashed text-sm space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-1.5">
              <Info class="w-3 h-3" /> Application Details
            </span>
            <span class="text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200/50 uppercase">Decision Pending</span>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-[11px] text-muted-foreground mb-0.5">Employee</p>
              <p class="font-bold text-slate-900 truncate font-mono text-xs">{{ reviewTarget.employee_id }}</p>
            </div>
            <div>
              <p class="text-[11px] text-muted-foreground mb-0.5">Request Type</p>
              <p class="font-bold text-slate-900">{{ reasonLabels[reviewTarget.reason] ?? reviewTarget.reason }}</p>
            </div>
            <div class="col-span-2">
              <p class="text-[11px] text-muted-foreground mb-0.5">Period / Date</p>
              <p class="font-bold text-slate-900">
                {{ reviewTarget.for_date || `${reviewTarget.from_date} → ${reviewTarget.to_date}` }}
              </p>
            </div>
          </div>
          <div v-if="reviewTarget.explanation" class="pt-2 border-t border-slate-200/60">
            <p class="text-[11px] text-muted-foreground mb-1">Employee Reason</p>
            <p class="text-slate-700 leading-relaxed italic">"{{ reviewTarget.explanation }}"</p>
          </div>
        </div>

        <!-- Late clock-in options -->
        <div v-if="isLateReview" class="space-y-4 p-4 bg-amber-50/50 rounded-2xl border border-amber-200/50">
          <p class="text-[10px] font-black text-amber-700 uppercase tracking-widest">Late Arrival — Attendance Decision</p>
          <FormSelect
            label="Mark Attendance As"
            :modelValue="reviewMarkAs"
            @update:modelValue="reviewMarkAs = $event as typeof reviewMarkAs"
            :options="markAsOptions"
          />
          <p class="text-[10px] text-amber-600">
            <strong>Normal with Late Flag</strong> — counts as a full present day, late flag visible in reports.<br/>
            <strong>Half Day</strong> — recorded as 0.5 day, deducted from leave balance.
          </p>
        </div>

        <!-- Off-day work options -->
        <div v-if="isOffDayReview" class="space-y-4 p-4 bg-slate-50 rounded-2xl border border-slate-200/60">
          <p class="text-[10px] font-black text-slate-700 uppercase tracking-widest">Off Day Work — Pay Structure</p>
          <FormSelect
            label="Work Type"
            :modelValue="offDayWorkType"
            @update:modelValue="offDayWorkType = $event as typeof offDayWorkType"
            :options="offDayWorkTypeOptions"
          />
          <div v-if="offDayWorkType === 'overtime'" class="space-y-3 animate-in fade-in slide-in-from-top-2">
            <FormSelect
              label="OT Rate"
              :modelValue="offDayOtRate"
              @update:modelValue="offDayOtRate = $event"
              :options="otRateOptions"
            />
            <div v-if="offDayOtRate === 'custom'" class="animate-in fade-in slide-in-from-top-2">
              <label class="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1.5 block">Custom Multiplier</label>
              <div class="relative">
                <input
                  v-model="customOtRate"
                  type="number"
                  step="0.1"
                  min="1"
                  class="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 pr-8"
                  placeholder="e.g. 1.75"
                />
                <span class="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-bold text-slate-400">×</span>
              </div>
            </div>
          </div>
        </div>

        <!-- HR notes -->
        <FormTextarea
          label="Internal Review Note"
          v-model="reviewNote"
          placeholder="Add comments for the audit trail..."
          :rows="3"
        />

        <p v-if="errorMsg" class="text-xs text-destructive font-bold uppercase">{{ errorMsg }}</p>

        <!-- Action buttons -->
        <div class="grid grid-cols-2 gap-4 pt-2">
          <Button
            @click="doReview('approved')"
            :disabled="reviewing"
            class="h-12 rounded-2xl bg-emerald-600 text-white hover:bg-emerald-700 shadow-lg shadow-emerald-200"
          >
            <Check class="w-4 h-4 mr-2" /> {{ reviewing ? 'Applying…' : 'Approve' }}
          </Button>
          <Button
            @click="doReview('rejected')"
            :disabled="reviewing"
            variant="destructive"
            class="h-12 rounded-2xl shadow-lg shadow-rose-200"
          >
            <X class="w-4 h-4 mr-2" /> {{ reviewing ? 'Applying…' : 'Reject' }}
          </Button>
        </div>
      </div>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!cancelTarget"
      title="Cancel Request?"
      message="Are you sure you want to cancel this attendance request? This action cannot be undone."
      confirm-label="Confirm Cancellation"
      :loading="cancelling"
      @confirm="confirmCancel"
      @cancel="cancelTarget = null"
    />
  </div>
</template>
