<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
import { Check, X, Ban, Search, Info, Calendar } from 'lucide-vue-next'
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
  { key: 'from_date',   label: 'Period'       }, // Combined date range
  { key: 'reason',      label: 'Reason'     },
  { key: 'status',      label: 'Status'     },
]

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

const statusOptions = [
  { value: '', label: 'All Status' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'cancelled', label: 'Cancelled' },
]

const reasonOptions = [
  { value: 'on_site_duty', label: 'On-site Duty' },
  { value: 'work_from_home', label: 'Work From Home' },
  { value: 'other', label: 'Other' },
]
</script>

<template>
  <div class="space-y-8">
    <PageHeader 
      title="Attendance Requests" 
      subtitle="Regularization and remote work applications" 
      action-label="New Request" 
      @action="openCreate" 
    />

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

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="false" empty-text="No requests found.">
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
      <template #cell-reason="{ value }">
        <span class="text-xs font-medium text-slate-600 dark:text-slate-400">{{ reasonLabels[value] ?? value }}</span>
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
        <div class="flex items-center justify-end gap-1">
          <template v-if="row.status === 'pending'">
            <Button 
              variant="ghost" 
              size="icon" 
              @click="reviewTarget = row; reviewNote = ''; errorMsg = ''" 
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

    <!-- Create Drawer -->
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
            <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800 shadow-lg shadow-slate-200">
              {{ saving ? 'Submitting...' : 'Submit Request' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- Review Drawer -->
    <SlideDrawer :open="!!reviewTarget" title="Process Request" width="w-full max-w-lg" @close="reviewTarget = null">
      <div v-if="reviewTarget" class="space-y-6">
        <div class="p-5 rounded-3xl bg-muted/30 border border-dashed text-sm space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-1.5"><Info class="w-3 h-3" /> Application Details</span>
            <span class="text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200/50 uppercase">Decision Pending</span>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-[11px] text-muted-foreground mb-0.5">Employee</p>
              <p class="font-bold text-slate-900 truncate">{{ reviewTarget.employee_id }}</p>
            </div>
            <div>
              <p class="text-[11px] text-muted-foreground mb-0.5">Request Type</p>
              <p class="font-bold text-slate-900">{{ reasonLabels[reviewTarget.reason] ?? reviewTarget.reason }}</p>
            </div>
            <div class="col-span-2">
              <p class="text-[11px] text-muted-foreground mb-0.5">Validity Period</p>
              <p class="font-bold text-slate-900">{{ reviewTarget.from_date }} to {{ reviewTarget.to_date }}</p>
            </div>
          </div>
          <div v-if="reviewTarget.explanation" class="pt-2 border-t border-slate-200/60">
            <p class="text-[11px] text-muted-foreground mb-1">Employee Explanation</p>
            <p class="text-slate-700 leading-relaxed italic">"{{ reviewTarget.explanation }}"</p>
          </div>
        </div>

        <FormTextarea 
          label="Internal Review Note" 
          v-model="reviewNote" 
          placeholder="Add comments for the audit trail..." 
          :rows="4"
        />

        <p v-if="errorMsg" class="text-xs text-destructive font-bold uppercase">{{ errorMsg }}</p>

        <div class="grid grid-cols-2 gap-4 pt-4">
          <Button 
            @click="doReview('approved')" 
            :disabled="reviewing" 
            class="h-12 rounded-2xl bg-emerald-600 text-white hover:bg-emerald-700 shadow-lg shadow-emerald-200"
          >
            <Check class="w-4 h-4 mr-2" /> {{ reviewing ? 'Applying...' : 'Approve' }}
          </Button>
          <Button 
            @click="doReview('rejected')" 
            :disabled="reviewing" 
            variant="destructive"
            class="h-12 rounded-2xl shadow-lg shadow-rose-200"
          >
            <X class="w-4 h-4 mr-2" /> {{ reviewing ? 'Applying...' : 'Reject' }}
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
