<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { PencilIcon, CheckIcon, XIcon } from 'lucide-vue-next'
import { listShiftRequests, createShiftRequest, reviewShiftRequest, cancelShiftRequest } from '../../services/shift-request.service'
import type { ShiftRequest } from '../../services/shift-request.service'

const rows = ref<ShiftRequest[]>([]); const loading = ref(false)
const drawerOpen = ref(false); const form = ref<Partial<ShiftRequest>>({ request_type: 'change' })
const reviewTarget = ref<ShiftRequest | null>(null); const reviewNote = ref('')
const cancelTarget = ref<ShiftRequest | null>(null)
const saving = ref(false); const reviewing = ref(false); const cancelling = ref(false)
const errorMsg = ref('')

const requestTypeOptions = [
  { value: 'change', label: 'Change Shift' },
  { value: 'swap',   label: 'Swap Shift'   },
  { value: 'leave',  label: 'Leave'        },
]

const statusColors: Record<string, string> = {
  pending:   'bg-amber-100 text-amber-700',
  approved:  'bg-emerald-100 text-emerald-700',
  rejected:  'bg-rose-100 text-rose-600',
  cancelled: 'bg-slate-100 text-slate-500',
}

const typeColors: Record<string, string> = {
  change: 'bg-blue-100 text-blue-700',
  swap:   'bg-violet-100 text-violet-700',
  leave:  'bg-rose-100 text-rose-600',
}

const columns = [
  { key: 'employee_id',   label: 'Employee ID' },
  { key: 'request_type',  label: 'Type'        },
  { key: 'from_date',     label: 'From'        },
  { key: 'to_date',       label: 'To'          },
  { key: 'status',        label: 'Status'      },
]

async function load() { loading.value = true; try { rows.value = await listShiftRequests() } catch {} finally { loading.value = false } }
onMounted(load)

function openCreate() { form.value = { request_type: 'change' }; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  saving.value = true; errorMsg.value = ''
  try { await createShiftRequest(form.value); drawerOpen.value = false; load() }
  catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function approve() {
  if (!reviewTarget.value) return; reviewing.value = true
  try { await reviewShiftRequest(reviewTarget.value.id, { status: 'approved', review_note: reviewNote.value || undefined }); reviewTarget.value = null; load() }
  catch {} finally { reviewing.value = false }
}

async function reject() {
  if (!reviewTarget.value) return; reviewing.value = true
  try { await reviewShiftRequest(reviewTarget.value.id, { status: 'rejected', review_note: reviewNote.value || undefined }); reviewTarget.value = null; load() }
  catch {} finally { reviewing.value = false }
}

async function confirmCancel() {
  if (!cancelTarget.value) return; cancelling.value = true
  try { await cancelShiftRequest(cancelTarget.value.id); cancelTarget.value = null; load() }
  catch {} finally { cancelling.value = false }
}

function openReview(row: ShiftRequest) { reviewTarget.value = row; reviewNote.value = '' }
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Shift Requests" subtitle="Manage employee shift change, swap, and leave requests" action-label="+ New Request" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No shift requests yet.">
      <template #cell-employee_id="{ value }">
        <span class="font-mono text-xs text-slate-500">{{ value?.slice(0, 8) }}…</span>
      </template>
      <template #cell-request_type="{ value }">
        <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize', typeColors[value] ?? 'bg-slate-100 text-slate-600']">{{ value }}</span>
      </template>
      <template #cell-status="{ value }">
        <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize', statusColors[value] ?? 'bg-slate-100 text-slate-600']">{{ value }}</span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end space-x-2">
          <button v-if="row.status === 'pending'" @click="openReview(row)" class="p-2 rounded-[10px] hover:bg-emerald-50 text-slate-400 hover:text-emerald-600 transition-colors" title="Review">
            <CheckIcon class="w-4 h-4" />
          </button>
          <button v-if="row.status === 'pending'" @click="cancelTarget = row" class="p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors" title="Cancel">
            <XIcon class="w-4 h-4" />
          </button>
        </div>
      </template>
    </DataTable>

    <!-- Create Request Drawer -->
    <SlideDrawer :open="drawerOpen" title="New Shift Request" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Employee ID" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" required placeholder="Employee UUID" />
        <FormSelect label="Request Type" :modelValue="form.request_type ?? 'change'" :options="requestTypeOptions" @update:modelValue="form.request_type = $event as any" />
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="From Date" type="date" :modelValue="form.from_date" @update:modelValue="form.from_date = $event" required />
          <FormInput label="To Date" type="date" :modelValue="form.to_date" @update:modelValue="form.to_date = $event" required />
        </div>
        <FormTextarea label="Reason" :modelValue="form.reason" @update:modelValue="form.reason = $event" placeholder="Reason for the request" />
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="drawerOpen = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="save" :disabled="saving" class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">{{ saving ? 'Saving...' : 'Submit' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- Review Drawer -->
    <SlideDrawer :open="!!reviewTarget" title="Review Shift Request" width="w-full max-w-md" @close="reviewTarget = null">
      <div v-if="reviewTarget" class="space-y-5">
        <div class="bg-slate-50 rounded-[16px] p-4 space-y-2 text-sm">
          <div class="flex justify-between"><span class="text-slate-500">Type</span><span class="font-medium capitalize">{{ reviewTarget.request_type }}</span></div>
          <div class="flex justify-between"><span class="text-slate-500">From</span><span class="font-medium">{{ reviewTarget.from_date }}</span></div>
          <div class="flex justify-between"><span class="text-slate-500">To</span><span class="font-medium">{{ reviewTarget.to_date }}</span></div>
          <div v-if="reviewTarget.reason" class="pt-2 border-t border-slate-200"><span class="text-slate-500">Reason: </span>{{ reviewTarget.reason }}</div>
        </div>
        <div class="space-y-2">
          <label class="block text-sm font-semibold text-slate-700">Review Note (optional)</label>
          <textarea v-model="reviewNote" rows="3" placeholder="Add a note for the employee..."
            class="w-full bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-[12px] px-3 py-2.5 outline-none focus:ring-2 focus:ring-slate-900/10 resize-none" />
        </div>
      </div>
      <template #footer>
        <div class="flex space-x-3 justify-end">
          <button @click="reviewTarget = null" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
          <button @click="reject" :disabled="reviewing" class="px-5 py-2.5 bg-rose-600 text-white rounded-full font-medium text-sm hover:bg-rose-700 transition-all disabled:opacity-60">Reject</button>
          <button @click="approve" :disabled="reviewing" class="px-6 py-2.5 bg-emerald-600 text-white rounded-full font-medium text-sm hover:bg-emerald-700 transition-all disabled:opacity-60">Approve</button>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog :open="!!cancelTarget" title="Cancel Request?" message="Cancel this shift request? This cannot be undone." :loading="cancelling" @confirm="confirmCancel" @cancel="cancelTarget = null" />
  </div>
</template>
