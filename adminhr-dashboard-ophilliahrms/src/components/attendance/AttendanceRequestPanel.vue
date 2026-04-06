<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import { CheckIcon, XIcon, BanIcon } from 'lucide-vue-next'
import {
  listAttendanceRequests,
  createAttendanceRequest,
  cancelAttendanceRequest,
  reviewAttendanceRequest,
} from '../../services/attendance-request.service'
import type { AttendanceRequest } from '../../services/attendance-request.service'

const rows = ref<AttendanceRequest[]>([])
const loading = ref(false)
const createDrawerOpen = ref(false)
const reviewTarget = ref<AttendanceRequest | null>(null)
const cancelTarget = ref<AttendanceRequest | null>(null)
const form = ref<Partial<AttendanceRequest>>({})
const reviewNote = ref('')
const saving = ref(false)
const cancelling = ref(false)
const reviewing = ref(false)
const errorMsg = ref('')

// Filter
const filterStatus = ref('')

const columns = [
  { key: 'employee_id', label: 'Employee'   },
  { key: 'from_date',   label: 'From'       },
  { key: 'to_date',     label: 'To'         },
  { key: 'reason',      label: 'Reason'     },
  { key: 'status',      label: 'Status'     },
]

const statusColors: Record<string, string> = {
  pending:   'bg-amber-100 text-amber-700',
  approved:  'bg-emerald-100 text-emerald-700',
  rejected:  'bg-rose-100 text-rose-600',
  cancelled: 'bg-slate-100 text-slate-500',
}

const reasonLabels: Record<string, string> = {
  on_site_duty:   'On-site Duty',
  work_from_home: 'Work From Home',
  other:          'Other',
}

async function load() {
  loading.value = true
  try {
    const res = await listAttendanceRequests({ status: filterStatus.value || undefined, limit: 100 })
    rows.value = res.requests
  } catch {}
  finally { loading.value = false }
}

onMounted(load)

function openCreate() {
  form.value = { reason: 'on_site_duty', include_holidays: 0, half_day: 0 }
  errorMsg.value = ''
  createDrawerOpen.value = true
}

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    await createAttendanceRequest(form.value)
    createDrawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { saving.value = false }
}

async function confirmCancel() {
  if (!cancelTarget.value) return
  cancelling.value = true
  try { await cancelAttendanceRequest(cancelTarget.value.id); cancelTarget.value = null; load() }
  catch {} finally { cancelling.value = false }
}

async function doReview(status: 'approved' | 'rejected') {
  if (!reviewTarget.value) return
  reviewing.value = true
  try {
    await reviewAttendanceRequest(reviewTarget.value.id, { status, review_note: reviewNote.value || undefined })
    reviewTarget.value = null; reviewNote.value = ''; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { reviewing.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Attendance Requests" subtitle="Employee regularization requests" action-label="+ New Request" @action="openCreate" />

    <!-- Filter -->
    <div class="flex flex-wrap gap-3 bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[20px] px-5 py-4">
      <select v-model="filterStatus" class="text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none">
        <option value="">All Status</option>
        <option value="pending">Pending</option>
        <option value="approved">Approved</option>
        <option value="rejected">Rejected</option>
        <option value="cancelled">Cancelled</option>
      </select>
      <button @click="load" class="px-5 py-2 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition-colors">Filter</button>
    </div>

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="false" empty-text="No requests found.">
      <template #cell-employee_id="{ value }">
        <span class="font-mono text-xs text-slate-400">{{ String(value).slice(0, 8) }}…</span>
      </template>
      <template #cell-reason="{ value }">
        <span class="text-sm text-slate-600">{{ reasonLabels[value] ?? value }}</span>
      </template>
      <template #cell-status="{ value }">
        <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize', statusColors[value] ?? 'bg-slate-100 text-slate-500']">{{ value }}</span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <template v-if="row.status === 'pending'">
            <button @click="reviewTarget = row; reviewNote = ''; errorMsg = ''" class="p-2 rounded-[10px] hover:bg-emerald-50 text-slate-400 hover:text-emerald-700 transition-colors" title="Review">
              <CheckIcon class="w-4 h-4" />
            </button>
            <button @click="cancelTarget = row" class="p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors" title="Cancel">
              <BanIcon class="w-4 h-4" />
            </button>
          </template>
        </div>
      </template>
    </DataTable>

    <!-- Create Drawer -->
    <SlideDrawer :open="createDrawerOpen" title="New Attendance Request" width="w-full max-w-lg" @close="createDrawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Employee ID (UUID)" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" required placeholder="00000000-…" />
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="From Date" type="date" :modelValue="form.from_date" @update:modelValue="form.from_date = $event || undefined" required />
          <FormInput label="To Date" type="date" :modelValue="form.to_date" @update:modelValue="form.to_date = $event || undefined" required />
        </div>
        <div>
          <p class="text-xs font-semibold text-slate-500 mb-1">Reason</p>
          <select v-model="form.reason" class="w-full text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none focus:ring-2 focus:ring-slate-200">
            <option value="on_site_duty">On-site Duty</option>
            <option value="work_from_home">Work From Home</option>
            <option value="other">Other</option>
          </select>
        </div>
        <FormTextarea label="Explanation (optional)" :modelValue="form.explanation" @update:modelValue="form.explanation = $event" placeholder="Additional context..." />
        <div class="flex gap-6">
          <label class="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
            <input type="checkbox" :checked="!!form.include_holidays" @change="form.include_holidays = ($event.target as HTMLInputElement).checked ? 1 : 0" class="accent-slate-900 w-4 h-4" />
            Include Weekends
          </label>
          <label class="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
            <input type="checkbox" :checked="!!form.half_day" @change="form.half_day = ($event.target as HTMLInputElement).checked ? 1 : 0" class="accent-slate-900 w-4 h-4" />
            Half Day
          </label>
        </div>
        <FormInput v-if="form.half_day" label="Half Day Date" type="date" :modelValue="form.half_day_date" @update:modelValue="form.half_day_date = $event || undefined" />
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="createDrawerOpen = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="save" :disabled="saving" class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">{{ saving ? 'Submitting...' : 'Submit' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- Review Drawer -->
    <SlideDrawer :open="!!reviewTarget" title="Review Request" width="w-full max-w-md" @close="reviewTarget = null">
      <div v-if="reviewTarget" class="space-y-5">
        <div class="bg-slate-50 rounded-[16px] p-4 space-y-2 text-sm">
          <p><span class="font-medium text-slate-500">Employee:</span> <span class="font-mono text-xs">{{ reviewTarget.employee_id }}</span></p>
          <p><span class="font-medium text-slate-500">Period:</span> {{ reviewTarget.from_date }} → {{ reviewTarget.to_date }}</p>
          <p><span class="font-medium text-slate-500">Reason:</span> {{ reasonLabels[reviewTarget.reason] ?? reviewTarget.reason }}</p>
          <p v-if="reviewTarget.explanation"><span class="font-medium text-slate-500">Explanation:</span> {{ reviewTarget.explanation }}</p>
        </div>
        <div>
          <label class="text-xs font-semibold text-slate-500 block mb-1">Review Note (optional)</label>
          <textarea v-model="reviewNote" rows="3" placeholder="Add a note..." class="w-full text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none focus:ring-2 focus:ring-slate-200 resize-none"></textarea>
        </div>
        <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p>
        <div class="flex gap-3">
          <button @click="doReview('approved')" :disabled="reviewing" class="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-full font-medium text-sm hover:bg-emerald-700 transition-all disabled:opacity-60">
            <CheckIcon class="w-4 h-4" /> {{ reviewing ? '...' : 'Approve' }}
          </button>
          <button @click="doReview('rejected')" :disabled="reviewing" class="flex-1 flex items-center justify-center gap-2 py-2.5 bg-rose-600 text-white rounded-full font-medium text-sm hover:bg-rose-700 transition-all disabled:opacity-60">
            <XIcon class="w-4 h-4" /> {{ reviewing ? '...' : 'Reject' }}
          </button>
        </div>
      </div>
    </SlideDrawer>

    <ConfirmDialog :open="!!cancelTarget" title="Cancel Request?" :message="`Cancel this attendance request?`" :loading="cancelling" @confirm="confirmCancel" @cancel="cancelTarget = null" />
  </div>
</template>
