<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { Button } from '@/components/ui/button'
import { 
  Check, 
  X, 
  Plus, 
  FileQuestion, 
  Calendar, 
  Shuffle, 
  Reply, 
  CheckCircle2, 
  XCircle, 
  Info,
  Clock,
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
  { value: 'change', label: 'Framework Modification' },
  { value: 'swap',   label: 'Resource Exchange' },
  { value: 'leave',  label: 'Operational Absence' },
]

const statusColors: Record<string, string> = {
  pending:   'bg-amber-50 text-amber-700 border-amber-100',
  approved:  'bg-emerald-50 text-emerald-700 border-emerald-100',
  rejected:  'bg-rose-50 text-rose-700 border-rose-100',
  cancelled: 'bg-slate-50 text-slate-400 border-slate-100',
}

const typeIcons: Record<string, any> = {
  change: Clock,
  swap:   Shuffle,
  leave:  Calendar,
}

const columns = [
  { key: 'employee_id',   label: 'Petitioner' },
  { key: 'request_type',  label: 'Protocol'   },
  { key: 'from_date',     label: 'Commence'   },
  { key: 'to_date',       label: 'Conclude'   },
  { key: 'status',        label: 'Status'     },
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
      title="Temporal Petitions" 
      subtitle="Evaluate and synchronize operational framework modification requests" 
      action-label="File Petition" 
      @action="openCreate" 
    />

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No active petitions identified.">
      <template #cell-employee_id="{ value }">
        <div class="flex items-center gap-3">
           <div class="h-8 w-8 rounded-lg bg-slate-900 flex items-center justify-center text-[10px] font-black text-white shrink-0 shadow-sm">
              {{ value?.slice(0, 2).toUpperCase() }}
           </div>
           <span class="font-mono text-[11px] font-bold text-slate-500 uppercase tracking-tight">{{ value?.slice(0, 8) }}…</span>
        </div>
      </template>
      <template #cell-request_type="{ value }">
        <div class="flex items-center gap-2">
           <component :is="typeIcons[value] || FileQuestion" class="w-3.5 h-3.5 text-slate-400" />
           <span class="text-[11px] font-bold text-slate-900 uppercase tracking-wide capitalize">{{ value }}</span>
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
            class="h-9 w-9 rounded-xl text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 transition-all"
          >
            <Check class="w-4 h-4" />
          </Button>
          <Button 
            v-if="row.status === 'pending'" 
            variant="ghost" 
            size="icon" 
            @click="cancelTarget = row" 
            class="h-9 w-9 rounded-xl text-slate-400 hover:text-destructive hover:bg-destructive/10 transition-all"
          >
            <X class="w-4 h-4" />
          </Button>
        </div>
      </template>
    </DataTable>

    <!-- Create Request Drawer -->
    <SlideDrawer :open="drawerOpen" title="Initialize Temporal Petition" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-8 py-4">
        <div class="bg-indigo-50/30 p-4 rounded-2xl flex items-start gap-3 border border-indigo-100/50 mb-2">
           <Info class="w-4 h-4 text-indigo-500 mt-0.5" />
           <p class="text-[11px] text-indigo-700 font-medium leading-relaxed">
             Specify the required temporal adjustment. All petitions are evaluated against current operational framework density.
           </p>
        </div>

        <FormInput label="Petitioner Hardware ID" v-model="form.employee_id" required placeholder="Paste Individual UUID" />
        <FormSelect label="Adjust Protocol" v-model="form.request_type" :options="requestTypeOptions" />
        
        <div class="grid grid-cols-2 gap-6 p-6 bg-slate-50/50 rounded-[32px] border border-white/10">
          <FormInput label="Temporal Commencement" type="date" v-model="form.from_date" required />
          <FormInput label="Temporal Conclusion" type="date" v-model="form.to_date" required />
        </div>

        <FormTextarea label="Contextual Reason" v-model="form.reason" placeholder="Detail the necessity for this operational variance..." />
      </div>
      <template #footer>
        <div class="flex items-center justify-between gap-4">
          <div class="flex-1">
             <p v-if="errorMsg" class="text-[10px] font-bold text-destructive uppercase tracking-tight animate-in fade-in">{{ errorMsg }}</p>
          </div>
          <div class="flex gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 font-bold uppercase tracking-widest text-[11px]">
              {{ saving ? 'Syncing...' : 'File Petition' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- Review Drawer -->
    <SlideDrawer :open="!!reviewTarget" title="Petition Evaluation" width="w-full max-w-md" @close="reviewTarget = null">
      <div v-if="reviewTarget" class="space-y-8 py-4">
        <div class="bg-slate-900 dark:bg-white rounded-[40px] p-8 text-white dark:text-slate-900 shadow-2xl shadow-slate-200 dark:shadow-none relative overflow-hidden group">
           <div class="absolute -right-10 -top-10 w-32 h-32 bg-white/10 rounded-full blur-3xl group-hover:scale-125 transition-transform duration-700"></div>
           
           <div class="flex items-center gap-3 mb-6">
              <div class="h-10 w-10 rounded-2xl bg-white/20 flex items-center justify-center">
                 <User class="w-5 h-5" />
              </div>
              <div>
                 <p class="text-[10px] font-bold uppercase tracking-widest opacity-60">Petitioner Interface</p>
                 <p class="text-sm font-black tracking-tight">{{ reviewTarget.employee_id.slice(0, 16) }}…</p>
              </div>
           </div>

           <div class="grid grid-cols-2 gap-6 mb-8">
              <div>
                 <p class="text-[9px] font-black uppercase tracking-widest opacity-50 mb-1">Protocol</p>
                 <div class="flex items-center gap-2">
                    <component :is="typeIcons[reviewTarget.request_type] || FileQuestion" class="w-4 h-4" />
                    <span class="text-xs font-bold capitalize">{{ reviewTarget.request_type }}</span>
                 </div>
              </div>
              <div class="text-right">
                 <p class="text-[9px] font-black uppercase tracking-widest opacity-50 mb-1">Status</p>
                 <span class="text-xs font-bold uppercase tracking-tighter bg-white/20 px-3 py-1 rounded-full">Active Review</span>
              </div>
           </div>

           <div class="flex items-center justify-between p-4 bg-white/5 rounded-3xl border border-white/10">
              <div class="text-center flex-1">
                 <p class="text-[9px] font-black uppercase tracking-widest opacity-50 mb-1">Commence</p>
                 <p class="text-xs font-bold">{{ reviewTarget.from_date }}</p>
              </div>
              <ArrowRight class="w-4 h-4 opacity-20" />
              <div class="text-center flex-1">
                 <p class="text-[9px] font-black uppercase tracking-widest opacity-50 mb-1">Conclude</p>
                 <p class="text-xs font-bold">{{ reviewTarget.to_date }}</p>
              </div>
           </div>

           <div v-if="reviewTarget.reason" class="mt-8 pt-6 border-t border-white/10">
              <p class="text-[9px] font-black uppercase tracking-widest opacity-50 mb-2 flex items-center gap-2">
                 <MessageSquare class="w-3 h-3" /> Declaration
              </p>
              <p class="text-xs font-medium leading-relaxed italic opacity-80">"{{ reviewTarget.reason }}"</p>
           </div>
        </div>

        <FormTextarea label="Evaluation Feedback" v-model="reviewNote" placeholder="Acknowledge or dispute the operational variance..." />
      </div>
      <template #footer>
        <div class="flex gap-4 justify-end">
          <Button variant="outline" @click="reviewTarget = null" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">Defer</Button>
          <div class="flex gap-2">
             <Button @click="reject" :disabled="reviewing" variant="ghost" class="rounded-full px-6 h-10 text-destructive hover:bg-destructive/10 font-black uppercase tracking-widest text-[11px]">Reject</Button>
             <Button @click="approve" :disabled="reviewing" class="rounded-full px-10 h-10 bg-emerald-600 text-white hover:bg-emerald-700 shadow-xl shadow-emerald-100 font-bold uppercase tracking-widest text-[11px]">Synchronize</Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog 
      :open="!!cancelTarget" 
      title="Retract Petition?" 
      message="Are you certain you want to nullify this temporal request? This action is immutable." 
      :loading="cancelling" 
      @confirm="confirmCancel" 
      @cancel="cancelTarget = null" 
    />
  </div>
</template>
