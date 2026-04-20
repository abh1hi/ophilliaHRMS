<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { Button } from '../ui/button'
import { Eye, CheckCircle2, XCircle } from 'lucide-vue-next'
import { listCompensatoryLeaveRequests, createCompensatoryLeaveRequest, reviewCompensatoryLeaveRequest } from '../../services/compensatory-leave.service'
import type { CompensatoryLeaveRequest } from '../../services/compensatory-leave.service'
import { listLeaveTypes } from '../../services/leave-type.service'

const rows = ref<CompensatoryLeaveRequest[]>([])
const total = ref(0)
const loading = ref(false)
const leaveTypeMap = ref<Record<string, string>>({})

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
  pending: 'bg-amber-100/50 text-amber-700 border-amber-200/50',
  approved: 'bg-emerald-100/50 text-emerald-700 border-emerald-200/50',
  rejected: 'bg-rose-100/50 text-rose-700 border-rose-200/50',
  cancelled: 'bg-slate-100/50 text-slate-500 border-slate-200/50',
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
    const [res, types] = await Promise.all([
      listCompensatoryLeaveRequests(),
      listLeaveTypes(),
    ])
    rows.value = res.requests; total.value = res.total
    leaveTypeMap.value = Object.fromEntries(types.map(t => [t.id, t.name]))
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

const decisionOptions = [
  { value: 'approved', label: 'Approve Request' },
  { value: 'rejected', label: 'Reject Request' },
]
</script>

<template>
  <div class="space-y-8">
    <PageHeader 
      title="Compensatory Leave" 
      subtitle="Manage claims for leave earned by working on off-days" 
      action-label="New Request" 
      @action="openCreate" 
    />
    
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No compensatory leave requests found.">
      <template #cell-leave_type_id="{ value }">
        <span class="text-xs font-medium text-slate-700">{{ leaveTypeMap[value] ?? value }}</span>
      </template>
      <template #cell-status="{ value }">
        <span 
          :class="STATUS_CLASSES[value]" 
          class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm"
        >
          {{ value }}
        </span>
      </template>
      <template #actions="{ row }">
        <Button 
          v-if="row.status === 'pending'" 
          variant="ghost" 
          size="icon" 
          @click="openReview(row)" 
          class="h-8 w-8 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-900"
        >
          <Eye class="w-4 h-4" />
        </Button>
      </template>
    </DataTable>

    <!-- Create drawer -->
    <SlideDrawer :open="createDrawer" title="New Compensatory Leave Request" width="w-full max-w-lg" @close="createDrawer = false">
      <div class="space-y-6">
        <FormInput label="Leave Type ID" :modelValue="form.leave_type_id" @update:modelValue="form.leave_type_id = $event" placeholder="e.g. C-OFF" required />
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Work Start Date" type="date" :modelValue="form.work_from_date" @update:modelValue="form.work_from_date = $event" required />
          <FormInput label="Work End Date" type="date" :modelValue="form.work_end_date" @update:modelValue="form.work_end_date = $event" required />
        </div>
        <FormTextarea label="Reason / Description" :modelValue="form.reason" @update:modelValue="form.reason = $event" placeholder="Briefly describe the work done..." />
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="saveError" class="text-xs text-destructive font-medium">{{ saveError }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="createDrawer = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
              {{ saving ? 'Submitting...' : 'Submit Request' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- Review drawer -->
    <SlideDrawer :open="reviewDrawer" title="Review Compensatory Request" width="w-full max-w-lg" @close="reviewDrawer = false">
      <div class="space-y-6">
        <div v-if="reviewTarget" class="p-4 rounded-2xl bg-muted/30 border border-dashed text-sm space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Request Details</span>
            <span class="text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200/50 uppercase">Pending Review</span>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-[11px] text-muted-foreground mb-0.5">Employee</p>
              <p class="font-semibold text-slate-900">{{ reviewTarget.employee_id }}</p>
            </div>
            <div>
              <p class="text-[11px] text-muted-foreground mb-0.5">Leave Type</p>
              <p class="font-semibold text-slate-900">{{ leaveTypeMap[reviewTarget.leave_type_id] ?? reviewTarget.leave_type_id }}</p>
            </div>
            <div class="col-span-2">
              <p class="text-[11px] text-muted-foreground mb-0.5">Work Period</p>
              <p class="font-semibold text-slate-900">{{ reviewTarget.work_from_date }} — {{ reviewTarget.work_end_date }}</p>
            </div>
          </div>
        </div>

        <FormSelect 
          label="Review Decision" 
          :modelValue="reviewForm.status" 
          @update:modelValue="reviewForm.status = $event as any" 
          :options="decisionOptions"
        />
        
        <FormTextarea 
          label="Internal Review Note" 
          :modelValue="reviewForm.review_note" 
          @update:modelValue="reviewForm.review_note = $event" 
          placeholder="Add a comment regarding this decision..."
        />
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="reviewError" class="text-xs text-destructive font-medium">{{ reviewError }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="reviewDrawer = false" class="rounded-full px-6">Cancel</Button>
            <Button 
              @click="submitReview" 
              :disabled="reviewing" 
              class="rounded-full px-8 text-white min-w-[140px]"
              :class="reviewForm.status === 'approved' ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-200' : 'bg-destructive hover:bg-destructive/90 shadow-rose-200'"
            >
              <template v-if="reviewing">Processing...</template>
              <template v-else-if="reviewForm.status === 'approved'">
                <CheckCircle2 class="w-4 h-4 mr-2" /> Approve
              </template>
              <template v-else>
                <XCircle class="w-4 h-4 mr-2" /> Reject
              </template>
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
