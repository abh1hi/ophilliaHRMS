<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import { XCircleIcon } from 'lucide-vue-next'
import { listLeavePolicyAssignments, assignLeavePolicy, cancelLeavePolicyAssignment } from '../../services/leave-policy.service'
import type { LeavePolicyAssignment } from '../../services/leave-policy.service'

const rows = ref<LeavePolicyAssignment[]>([])
const loading = ref(false)
const drawerOpen = ref(false)
const form = ref<Partial<LeavePolicyAssignment>>({})
const saving = ref(false)
const errorMsg = ref('')
const cancelTarget = ref<LeavePolicyAssignment | null>(null)
const cancelling = ref(false)

const columns = [
  { key: 'employee_id', label: 'Employee ID' },
  { key: 'policy_id', label: 'Policy ID' },
  { key: 'effective_from', label: 'Effective From' },
  { key: 'effective_to', label: 'Effective To' },
  { key: 'status', label: 'Status' },
]

async function load() {
  loading.value = true
  try { rows.value = await listLeavePolicyAssignments() } catch {} finally { loading.value = false }
}
onMounted(load)

function openCreate() { form.value = {}; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  saving.value = true; errorMsg.value = ''
  try { await assignLeavePolicy(form.value); drawerOpen.value = false; load() }
  catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function confirmCancel() {
  if (!cancelTarget.value) return
  cancelling.value = true
  try { await cancelLeavePolicyAssignment(cancelTarget.value.id); cancelTarget.value = null; load() }
  catch {} finally { cancelling.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Policy Assignments" subtitle="Assign leave policies to employees" action-label="+ Assign Policy" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No assignments yet.">
      <template #cell-status="{ value }">
        <span :class="value === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ value }}</span>
      </template>
      <template #actions="{ row }">
        <button v-if="row.status === 'active'" @click="cancelTarget = row" class="p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"><XCircleIcon class="w-4 h-4" /></button>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" title="Assign Leave Policy" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Employee ID" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" required />
        <FormInput label="Policy ID" :modelValue="form.policy_id" @update:modelValue="form.policy_id = $event" required />
        <FormInput label="Leave Period ID" :modelValue="form.leave_period_id" @update:modelValue="form.leave_period_id = $event" />
        <FormInput label="Effective From" type="date" :modelValue="form.effective_from" @update:modelValue="form.effective_from = $event" />
        <FormInput label="Effective To" type="date" :modelValue="form.effective_to" @update:modelValue="form.effective_to = $event" />
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="drawerOpen = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="save" :disabled="saving" class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">{{ saving ? 'Saving...' : 'Assign' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!cancelTarget"
      title="Cancel Assignment?"
      :message="`Cancel policy assignment for employee ${cancelTarget?.employee_id?.slice(0, 8)}...?`"
      confirm-label="Yes, Cancel"
      :loading="cancelling"
      @confirm="confirmCancel"
      @cancel="cancelTarget = null"
    />
  </div>
</template>
