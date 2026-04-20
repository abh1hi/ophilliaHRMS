<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import EntitySearchSelect from '../ui/EntitySearchSelect.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { Button } from '@/components/ui/button'
import {
  Check,
  X,
  CheckCircle2,
  XCircle,
  Info,
  Clock,
  Calendar,
  Shuffle,
  FileQuestion,
  MessageSquare,
  ArrowRight,
  User
} from 'lucide-vue-next'
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
  { value: 'swap',   label: 'Swap Shift' },
  { value: 'leave',  label: 'Time Off Request' },
]

const statusColors: Record<string, string> = {
  pending:   'bg-amber-50 text-amber-700 border-amber-100',
  approved:  'bg-emerald-50 text-emerald-700 border-emerald-100',
  rejected:  'bg-rose-50 text-rose-700 border-rose-100',
  cancelled: 'bg-slate-50 text-slate-400 border-slate-100',
}

const typeLabels: Record<string, string> = {
  change: 'Change Shift',
  swap:   'Swap Shift',
  leave:  'Time Off Request',
}

const typeIcons: Record<string, any> = {
  change: Clock,
  swap:   Shuffle,
  leave:  Calendar,
}

const columns = [
  { key: 'employee_id',   label: 'Employee'    },
  { key: 'request_type',  label: 'Type'        },
  { key: 'from_date',     label: 'Start Date'  },
  { key: 'to_date',       label: 'End Date'    },
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
  <div class="space-y-10">
    <PageHeader
      title="Shift Requests"
      subtitle="Review and approve employee shift change, swap, and time off requests"
      action-label="New Request"
      @action="openCreate"
    />

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No shift requests found.">
      <template #cell-employee_id="{ value }">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-lg bg-slate-900 flex items-center justify-center text-[10px] font-black text-white shrink-0">
            {{ value?.slice(0, 2).toUpperCase() }}
          </div>
          <span class="font-mono text-[11px] font-bold text-slate-500">{{ value?.slice(0, 8) }}…</span>
        </div>
      </template>
      <template #cell-request_type="{ value }">
        <div class="flex items-center gap-2">
          <component :is="typeIcons[value] || FileQuestion" class="w-3.5 h-3.5 text-slate-400" />
          <span class="text-[11px] font-bold text-slate-900">{{ typeLabels[value] ?? value }}</span>
        </div>
      </template>
      <template #cell-status="{ value }">
        <span :class="['inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm capitalize', statusColors[value] ?? 'bg-slate-50 text-slate-400 border-slate-100']">
          <CheckCircle2 v-if="value === 'approved'" class="w-3 h-3 mr-1.5" />
          <XCircle v-else-if="value === 'rejected' || value === 'cancelled'" class="w-3 h-3 mr-1.5" />
          <Clock v-else class="w-3 h-3 mr-1.5" />
          {{ value }}
        </span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <Button
            v-if="row.status === 'pending'"
            variant="ghost"
            size="icon"
            @click="openReview(row)"
            class="h-9 w-9 rounded-xl text-slate-400 hover:text-emerald-600 hover:bg-emerald-50"
          >
            <Check class="w-4 h-4" />
          </Button>
          <Button
            v-if="row.status === 'pending'"
            variant="ghost"
            size="icon"
            @click="cancelTarget = row"
            class="h-9 w-9 rounded-xl text-slate-400 hover:text-destructive hover:bg-destructive/10"
          >
            <X class="w-4 h-4" />
          </Button>
        </div>
      </template>
    </DataTable>

    <!-- Create Request Drawer -->
    <SlideDrawer :open="drawerOpen" title="New Shift Request" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6 py-4">
        <EntitySearchSelect
          :modelValue="form.employee_id ?? ''"
          @update:modelValue="form.employee_id = $event as string"
          label="Employee"
          entity="employee"
          placeholder="Search employee…"
          required
        />
        <FormSelect label="Request Type" v-model="form.request_type" :options="requestTypeOptions" />
        <div class="grid grid-cols-2 gap-4 p-5 bg-slate-50/50 rounded-2xl border border-slate-100">
          <FormInput label="Start Date" type="date" v-model="form.from_date" required />
          <FormInput label="End Date" type="date" v-model="form.to_date" required />
        </div>
        <FormTextarea label="Reason" v-model="form.reason" placeholder="Briefly describe the reason for this request…" />
      </div>
      <template #footer>
        <div class="flex items-center justify-between gap-4 w-full">
          <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
          <div v-else />
          <div class="flex gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6 h-10">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800">
              {{ saving ? 'Submitting…' : 'Submit Request' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- Review Drawer -->
    <SlideDrawer :open="!!reviewTarget" title="Review Shift Request" width="w-full max-w-md" @close="reviewTarget = null">
      <div v-if="reviewTarget" class="space-y-6 py-4">
        <div class="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Request Details</span>
            <span class="text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-100 uppercase">Pending Review</span>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <p class="text-[10px] text-slate-400 mb-0.5">Type</p>
              <div class="flex items-center gap-1.5">
                <component :is="typeIcons[reviewTarget.request_type] || FileQuestion" class="w-3.5 h-3.5 text-slate-600" />
                <p class="font-semibold text-slate-900 text-sm">{{ typeLabels[reviewTarget.request_type] ?? reviewTarget.request_type }}</p>
              </div>
            </div>
            <div>
              <p class="text-[10px] text-slate-400 mb-0.5">Period</p>
              <p class="font-semibold text-slate-900 text-sm">{{ reviewTarget.from_date }} — {{ reviewTarget.to_date }}</p>
            </div>
          </div>
          <div v-if="reviewTarget.reason">
            <p class="text-[10px] text-slate-400 mb-0.5">Reason</p>
            <p class="text-sm text-slate-700 italic">"{{ reviewTarget.reason }}"</p>
          </div>
        </div>

        <FormTextarea label="Review Note (optional)" v-model="reviewNote" placeholder="Add a comment about your decision…" />
      </div>
      <template #footer>
        <div class="flex gap-3 justify-end w-full">
          <Button variant="outline" @click="reviewTarget = null" class="rounded-full px-6 h-10">Close</Button>
          <Button @click="reject" :disabled="reviewing" variant="ghost" class="rounded-full px-6 h-10 text-destructive hover:bg-destructive/10 font-bold">Reject</Button>
          <Button @click="approve" :disabled="reviewing" class="rounded-full px-8 h-10 bg-emerald-600 text-white hover:bg-emerald-700 font-bold">
            {{ reviewing ? 'Processing…' : 'Approve' }}
          </Button>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!cancelTarget"
      title="Cancel Request?"
      message="Are you sure you want to cancel this shift request? This cannot be undone."
      :loading="cancelling"
      @confirm="confirmCancel"
      @cancel="cancelTarget = null"
    />
  </div>
</template>
