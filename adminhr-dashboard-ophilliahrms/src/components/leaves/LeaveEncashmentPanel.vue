<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import { Button } from '../ui/button'
import { CircleX } from 'lucide-vue-next'
import { listLeaveEncashments, createLeaveEncashment, cancelLeaveEncashment } from '../../services/leave-encashment.service'
import type { LeaveEncashment } from '../../services/leave-encashment.service'

const rows = ref<LeaveEncashment[]>([])
const total = ref(0)
const loading = ref(false)
const drawerOpen = ref(false)
const form = ref<Partial<LeaveEncashment>>({})
const saving = ref(false)
const errorMsg = ref('')
const cancelTarget = ref<LeaveEncashment | null>(null)
const cancelling = ref(false)

const STATUS_CLASSES: Record<string, string> = {
  submitted: 'bg-amber-100/50 text-amber-700 border-amber-200/50',
  paid: 'bg-emerald-100/50 text-emerald-700 border-emerald-200/50',
  cancelled: 'bg-slate-100/50 text-slate-500 border-slate-200/50',
}

const columns = [
  { key: 'employee_id', label: 'Employee' },
  { key: 'leave_type_id', label: 'Leave Type' },
  { key: 'encashable_days', label: 'Days' },
  { key: 'encashment_amount', label: 'Amount' },
  { key: 'encashment_date', label: 'Date' },
  { key: 'status', label: 'Status' },
]

async function load() {
  loading.value = true
  try {
    const res = await listLeaveEncashments()
    rows.value = res.encashments; total.value = res.total
  } catch {} finally { loading.value = false }
}
onMounted(load)

function openCreate() { form.value = { encashment_amount: 0 }; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  saving.value = true; errorMsg.value = ''
  try { await createLeaveEncashment(form.value); drawerOpen.value = false; load() }
  catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function confirmCancel() {
  if (!cancelTarget.value) return
  cancelling.value = true
  try { await cancelLeaveEncashment(cancelTarget.value.id); cancelTarget.value = null; load() }
  catch {} finally { cancelling.value = false }
}
</script>

<template>
  <div class="space-y-8">
    <PageHeader 
      title="Leave Encashments" 
      subtitle="Process unused leave encashment requests" 
      action-label="New Encashment" 
      @action="openCreate" 
    />
    
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No leave encashments found.">
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
          v-if="row.status === 'submitted'" 
          variant="ghost" 
          size="icon" 
          @click="cancelTarget = row" 
          class="h-8 w-8 rounded-lg hover:bg-destructive/10 text-slate-400 hover:text-destructive"
        >
          <CircleX class="w-4 h-4" />
        </Button>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" title="New Leave Encashment" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6">
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Employee ID" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" placeholder="e.g. EMP001" required />
          <FormInput label="Leave Type ID" :modelValue="form.leave_type_id" @update:modelValue="form.leave_type_id = $event" placeholder="e.g. AL" required />
        </div>
        <FormInput label="Leave Allocation ID" :modelValue="form.leave_allocation_id" @update:modelValue="form.leave_allocation_id = $event" placeholder="Policy allocation reference..." />
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Encashment Date" type="date" :modelValue="form.encashment_date" @update:modelValue="form.encashment_date = $event" />
          <FormInput label="Encashment Amount" type="number" :modelValue="String(form.encashment_amount ?? 0)" @update:modelValue="form.encashment_amount = Number($event)" />
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
              {{ saving ? 'Saving...' : 'Save Encashment' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!cancelTarget"
      title="Cancel Encashment?"
      :message="`Are you sure you want to cancel the encashment for ${cancelTarget?.encashable_days} days?`"
      confirm-label="Yes, Cancel"
      :loading="cancelling"
      @confirm="confirmCancel"
      @cancel="cancelTarget = null"
    />
  </div>
</template>
