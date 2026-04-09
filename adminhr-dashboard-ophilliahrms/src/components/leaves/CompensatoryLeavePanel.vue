<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { EyeIcon } from 'lucide-vue-next'
import { listCompensatoryLeaveRequests, createCompensatoryLeaveRequest, reviewCompensatoryLeaveRequest } from '../../services/compensatory-leave.service'
import type { CompensatoryLeaveRequest } from '../../services/compensatory-leave.service'

const rows = ref<CompensatoryLeaveRequest[]>([])
const total = ref(0)
const loading = ref(false)

const createDrawer = ref(false)
const form = ref<Partial<CompensatoryLeaveRequest>>({})
const saving = ref(false)
const saveError = ref('')

const reviewDrawer = ref(false)
const reviewTarget = ref<CompensatoryLeaveRequest | null>(null)
const reviewForm = ref<{ status: 'approved' | 'rejected'; review_note: string }>({ status: 'approved', review_note: '' })
const reviewing = ref(false)
const reviewError = ref('')

const STATUS_CLASSES: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-700',
  approved: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-rose-100 text-rose-700',
  cancelled: 'bg-slate-100 text-slate-500',
}

const columns = [
  { key: 'employee_id', label: 'Employee' },
  { key: 'work_from_date', label: 'Work From' },
  { key: 'work_end_date', label: 'Work To' },
  { key: 'leave_type_id', label: 'Leave Type' },
  { key: 'status', label: 'Status' },
]

async function load() {
  loading.value = true
  try {
    const res = await listCompensatoryLeaveRequests()
    rows.value = res.requests; total.value = res.total
  } catch {} finally { loading.value = false }
}
onMounted(load)

function openCreate() { form.value = {}; saveError.value = ''; createDrawer.value = true }
function openReview(row: CompensatoryLeaveRequest) { reviewTarget.value = row; reviewForm.value = { status: 'approved', review_note: '' }; reviewError.value = ''; reviewDrawer.value = true }

async function save() {
  saving.value = true; saveError.value = ''
  try { await createCompensatoryLeaveRequest(form.value); createDrawer.value = false; load() }
  catch (e: any) { saveError.value = e.message } finally { saving.value = false }
}

async function submitReview() {
  if (!reviewTarget.value) return
  reviewing.value = true; reviewError.value = ''
  try { await reviewCompensatoryLeaveRequest(reviewTarget.value.id, reviewForm.value); reviewDrawer.value = false; load() }
  catch (e: any) { reviewError.value = e.message } finally { reviewing.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Compensatory Leave Requests" subtitle="Employees claim leave for working on off-days" action-label="+ New Request" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No requests yet.">
      <template #cell-status="{ value }">
        <span :class="STATUS_CLASSES[value]" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ value }}</span>
      </template>
      <template #actions="{ row }">
        <button v-if="row.status === 'pending'" @click="openReview(row)" class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"><EyeIcon class="w-4 h-4" /></button>
      </template>
    </DataTable>

    <!-- Create drawer -->
    <SlideDrawer :open="createDrawer" title="New Compensatory Leave Request" width="w-full max-w-lg" @close="createDrawer = false">
      <div class="space-y-5">
        <FormInput label="Leave Type ID" :modelValue="form.leave_type_id" @update:modelValue="form.leave_type_id = $event" required />
        <FormInput label="Work From Date" type="date" :modelValue="form.work_from_date" @update:modelValue="form.work_from_date = $event" required />
        <FormInput label="Work End Date" type="date" :modelValue="form.work_end_date" @update:modelValue="form.work_end_date = $event" required />
        <FormTextarea label="Reason" :modelValue="form.reason" @update:modelValue="form.reason = $event" />
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="saveError" class="text-sm text-rose-600">{{ saveError }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="createDrawer = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="save" :disabled="saving" class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">{{ saving ? 'Submitting...' : 'Submit' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- Review drawer -->
    <SlideDrawer :open="reviewDrawer" title="Review Request" width="w-full max-w-md" @close="reviewDrawer = false">
      <div class="space-y-4">
        <div v-if="reviewTarget" class="rounded-[16px] bg-slate-50 p-4 text-sm space-y-1">
          <div class="text-slate-500">Employee: <span class="text-slate-900 font-medium">{{ reviewTarget.employee_id }}</span></div>
          <div class="text-slate-500">Period: <span class="text-slate-900 font-medium">{{ reviewTarget.work_from_date }} → {{ reviewTarget.work_end_date }}</span></div>
        </div>
        <div>
          <label class="block text-xs text-slate-500 mb-1">Decision</label>
          <select v-model="reviewForm.status" class="w-full bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-[12px] px-3 py-2.5 outline-none focus:ring-2 focus:ring-slate-900/10">
            <option value="approved">Approve</option>
            <option value="rejected">Reject</option>
          </select>
        </div>
        <FormInput label="Review Note" :modelValue="reviewForm.review_note" @update:modelValue="reviewForm.review_note = $event" />
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="reviewError" class="text-sm text-rose-600">{{ reviewError }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="reviewDrawer = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="submitReview" :disabled="reviewing" :class="reviewForm.status === 'approved' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-rose-600 hover:bg-rose-700'" class="px-6 py-2.5 text-white rounded-full font-medium text-sm transition-all disabled:opacity-60">{{ reviewing ? 'Submitting...' : reviewForm.status === 'approved' ? 'Approve' : 'Reject' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
