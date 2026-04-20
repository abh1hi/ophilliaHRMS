<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { CheckCircle2, XCircle, Clock, Plus } from 'lucide-vue-next'
import {
  listOvertimeRequests,
  submitOvertimeRequest,
  reviewOvertimeRequest,
  cancelOvertimeRequest,
} from '../../services/overtime-request.service'
import type { OvertimeRequest } from '../../services/overtime-request.service'
import { decodeToken } from '../../services/auth.service'
import { getToken } from '../../services/http'

const claims = decodeToken(getToken())
const userRole = claims?.role ?? ''
const isHR = ['hr', 'admin', 'manager'].includes(userRole)

const allRequests = ref<OvertimeRequest[]>([])
const loading = ref(false)
const activeTab = ref<'pending' | 'all'>('pending')

const submitDrawerOpen = ref(false)
const reviewDrawerOpen = ref(false)
const reviewTarget = ref<OvertimeRequest | null>(null)

const submitForm = ref({ date: '', requested_hours: 1, reason: '' })
const reviewForm = ref({ status: 'approved' as 'approved' | 'rejected', review_note: '' })
const saving = ref(false)
const errorMsg = ref('')

const pendingRequests = computed(() => allRequests.value.filter(r => r.status === 'pending'))

const displayedRequests = computed(() =>
  isHR ? (activeTab.value === 'pending' ? pendingRequests.value : allRequests.value)
       : allRequests.value
)

const columns = [
  { key: 'employee_id',    label: 'Employee'   },
  { key: 'date',           label: 'Date'       },
  { key: 'requested_hours', label: 'Hours'     },
  { key: 'reason',         label: 'Reason'     },
  { key: 'status',         label: 'Status'     },
  { key: 'created_at',     label: 'Submitted'  },
]

async function load() {
  loading.value = true
  try { allRequests.value = await listOvertimeRequests() } catch {} finally { loading.value = false }
}

onMounted(load)

function fmtDate(dt: string) {
  return new Date(dt).toLocaleDateString()
}

async function submitRequest() {
  saving.value = true; errorMsg.value = ''
  try {
    await submitOvertimeRequest(submitForm.value)
    submitDrawerOpen.value = false
    submitForm.value = { date: '', requested_hours: 1, reason: '' }
    load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

function openReview(row: OvertimeRequest) {
  reviewTarget.value = row
  reviewForm.value = { status: 'approved', review_note: '' }
  reviewDrawerOpen.value = true
}

async function submitReview() {
  if (!reviewTarget.value) return
  saving.value = true; errorMsg.value = ''
  try {
    await reviewOvertimeRequest(reviewTarget.value.id, reviewForm.value.status, reviewForm.value.review_note)
    reviewDrawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function cancel(row: OvertimeRequest) {
  try { await cancelOvertimeRequest(row.id); load() } catch {}
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">Overtime Requests</h2>
        <p class="text-sm text-slate-500 mt-0.5">
          {{ isHR ? 'Review and approve employee overtime requests' : 'Submit and track your overtime requests' }}
        </p>
      </div>
      <Button v-if="!isHR" @click="submitDrawerOpen = true" class="rounded-xl bg-slate-900 text-white hover:bg-slate-800 h-10 text-xs font-bold uppercase tracking-widest flex items-center gap-2">
        <Plus class="w-4 h-4" /> Submit OT Request
      </Button>
    </div>

    <!-- HR tabs -->
    <div v-if="isHR" class="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
      <button
        v-for="tab in [{ key: 'pending', label: `Pending (${pendingRequests.length})` }, { key: 'all', label: 'All Requests' }]"
        :key="tab.key"
        @click="activeTab = tab.key as 'pending' | 'all'"
        :class="['px-5 py-2 rounded-lg text-[11px] font-bold uppercase tracking-widest transition-all', activeTab === tab.key ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900']"
      >{{ tab.label }}</button>
    </div>

    <DataTable :columns="columns" :rows="displayedRequests" :loading="loading" empty-text="No overtime requests found.">
      <template #cell-date="{ value }">{{ fmtDate(value) }}</template>
      <template #cell-requested_hours="{ value }">
        <span class="font-semibold text-indigo-700">{{ value }}h</span>
      </template>
      <template #cell-reason="{ value }">
        <span class="text-sm text-slate-600 truncate max-w-xs block">{{ value }}</span>
      </template>
      <template #cell-status="{ value }">
        <Badge :class="[
          'text-[10px] font-bold',
          value === 'approved' ? 'bg-emerald-100 text-emerald-700 border-emerald-200' :
          value === 'rejected' ? 'bg-rose-100 text-rose-700 border-rose-200' :
          'bg-amber-100 text-amber-700 border-amber-200'
        ]">{{ value }}</Badge>
      </template>
      <template #cell-created_at="{ value }">{{ fmtDate(value) }}</template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <template v-if="isHR && row.status === 'pending'">
            <Button variant="ghost" size="icon" @click="openReview(row)" class="h-8 w-8 rounded-xl text-emerald-600 hover:bg-emerald-50">
              <CheckCircle2 class="w-4 h-4" />
            </Button>
          </template>
          <template v-else-if="!isHR && row.status === 'pending'">
            <Button variant="ghost" size="icon" @click="cancel(row)" class="h-8 w-8 rounded-xl text-slate-400 hover:text-destructive hover:bg-destructive/10">
              <XCircle class="w-4 h-4" />
            </Button>
          </template>
        </div>
      </template>
    </DataTable>

    <!-- Submit OT Request drawer -->
    <SlideDrawer :open="submitDrawerOpen" title="Submit Overtime Request" width="w-full max-w-md" @close="submitDrawerOpen = false">
      <div class="space-y-6 py-4">
        <FormInput label="Date" type="date" v-model="submitForm.date" required />
        <div class="space-y-1">
          <label class="text-xs font-bold uppercase tracking-widest text-slate-500">Overtime Hours</label>
          <input
            type="number" min="0.5" max="12" step="0.5"
            v-model.number="submitForm.requested_hours"
            class="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm bg-white"
          />
        </div>
        <FormTextarea label="Reason" v-model="submitForm.reason" required placeholder="Describe why overtime was required..." />
      </div>
      <template #footer>
        <div class="flex items-center justify-between gap-4">
          <p v-if="errorMsg" class="text-[10px] font-bold text-destructive">{{ errorMsg }}</p>
          <div class="flex gap-3 ml-auto">
            <Button variant="outline" @click="submitDrawerOpen = false" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">Cancel</Button>
            <Button @click="submitRequest" :disabled="saving" class="rounded-full px-8 h-10 bg-slate-900 text-white font-bold uppercase tracking-widest text-[11px]">
              {{ saving ? 'Submitting...' : 'Submit Request' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- Review drawer -->
    <SlideDrawer :open="reviewDrawerOpen" title="Review OT Request" width="w-full max-w-md" @close="reviewDrawerOpen = false">
      <div class="space-y-6 py-4" v-if="reviewTarget">
        <div class="bg-slate-50 rounded-2xl p-4 space-y-2 text-sm">
          <div class="flex justify-between"><span class="text-slate-500">Employee</span><span class="font-medium">{{ reviewTarget.employee_id.slice(0, 8) }}...</span></div>
          <div class="flex justify-between"><span class="text-slate-500">Date</span><span class="font-medium">{{ fmtDate(reviewTarget.date) }}</span></div>
          <div class="flex justify-between"><span class="text-slate-500">Hours Requested</span><span class="font-semibold text-indigo-700">{{ reviewTarget.requested_hours }}h</span></div>
          <div class="flex justify-between"><span class="text-slate-500">Reason</span><span class="font-medium text-right max-w-xs">{{ reviewTarget.reason }}</span></div>
        </div>
        <div class="flex gap-3">
          <button
            v-for="s in [{ key: 'approved', label: 'Approve', color: 'emerald' }, { key: 'rejected', label: 'Reject', color: 'rose' }]"
            :key="s.key"
            @click="reviewForm.status = s.key as 'approved' | 'rejected'"
            :class="['flex-1 py-2.5 rounded-xl text-[11px] font-bold uppercase tracking-widest transition-all border-2', reviewForm.status === s.key ? `bg-${s.color}-600 text-white border-${s.color}-600` : `border-slate-200 text-slate-500 hover:border-${s.color}-300`]"
          >{{ s.label }}</button>
        </div>
        <FormTextarea label="Note (optional)" v-model="reviewForm.review_note" placeholder="Add a comment for the employee..." />
      </div>
      <template #footer>
        <div class="flex items-center justify-between gap-4">
          <p v-if="errorMsg" class="text-[10px] font-bold text-destructive">{{ errorMsg }}</p>
          <div class="flex gap-3 ml-auto">
            <Button variant="outline" @click="reviewDrawerOpen = false" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">Cancel</Button>
            <Button @click="submitReview" :disabled="saving" class="rounded-full px-8 h-10 bg-slate-900 text-white font-bold uppercase tracking-widest text-[11px]">
              {{ saving ? 'Saving...' : 'Confirm Review' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
