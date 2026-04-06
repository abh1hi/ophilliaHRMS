<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import { XCircleIcon } from 'lucide-vue-next'
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
  submitted: 'bg-amber-100 text-amber-700',
  paid: 'bg-emerald-100 text-emerald-700',
  cancelled: 'bg-slate-100 text-slate-500',
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
  <div class="space-y-6">
    <PageHeader title="Leave Encashments" subtitle="Process unused leave encashment requests" action-label="+ New Encashment" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No encashments yet.">
      <template #cell-status="{ value }">
        <span :class="STATUS_CLASSES[value]" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ value }}</span>
      </template>
      <template #actions="{ row }">
        <button v-if="row.status === 'submitted'" @click="cancelTarget = row" class="p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"><XCircleIcon class="w-4 h-4" /></button>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" title="New Leave Encashment" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Employee ID" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" required />
        <FormInput label="Leave Type ID" :modelValue="form.leave_type_id" @update:modelValue="form.leave_type_id = $event" required />
        <FormInput label="Leave Allocation ID" :modelValue="form.leave_allocation_id" @update:modelValue="form.leave_allocation_id = $event" />
        <FormInput label="Encashment Date" type="date" :modelValue="form.encashment_date" @update:modelValue="form.encashment_date = $event" />
        <FormInput label="Encashment Amount" type="number" :modelValue="String(form.encashment_amount ?? 0)" @update:modelValue="form.encashment_amount = Number($event)" />
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="drawerOpen = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="save" :disabled="saving" class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!cancelTarget"
      title="Cancel Encashment?"
      :message="`Cancel encashment for ${cancelTarget?.encashable_days} days?`"
      confirm-label="Yes, Cancel"
      :loading="cancelling"
      @confirm="confirmCancel"
      @cancel="cancelTarget = null"
    />
  </div>
</template>
