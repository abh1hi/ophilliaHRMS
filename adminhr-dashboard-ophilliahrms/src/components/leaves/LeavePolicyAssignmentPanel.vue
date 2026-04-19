<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import { Button } from '../ui/button'
import { CircleX } from 'lucide-vue-next'
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
  <div class="space-y-8">
    <PageHeader 
      title="Policy Assignments" 
      subtitle="Assign leave policies to employees" 
      action-label="Assign Policy" 
      @action="openCreate" 
    />
    
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No assignments yet.">
      <template #cell-status="{ value }">
        <span 
          :class="value === 'active' ? 'bg-emerald-100/50 text-emerald-700 border-emerald-200/50' : 'bg-slate-100/50 text-slate-500 border-slate-200/50'" 
          class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm"
        >
          {{ value }}
        </span>
      </template>
      <template #actions="{ row }">
        <Button 
          v-if="row.status === 'active'" 
          variant="ghost" 
          size="icon" 
          @click="cancelTarget = row" 
          class="h-8 w-8 rounded-lg hover:bg-destructive/10 text-slate-400 hover:text-destructive"
        >
          <CircleX class="w-4 h-4" />
        </Button>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" title="Assign Leave Policy" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6">
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Employee ID" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" placeholder="e.g. EMP001" required />
          <FormInput label="Policy ID" :modelValue="form.policy_id" @update:modelValue="form.policy_id = $event" placeholder="e.g. LP001" required />
        </div>
        <FormInput label="Leave Period ID" :modelValue="form.leave_period_id" @update:modelValue="form.leave_period_id = $event" placeholder="e.g. FY24" />
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Effective From" type="date" :modelValue="form.effective_from" @update:modelValue="form.effective_from = $event" />
          <FormInput label="Effective To" type="date" :modelValue="form.effective_to" @update:modelValue="form.effective_to = $event" />
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
              {{ saving ? 'Saving...' : 'Assign Policy' }}
            </Button>
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
