<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import { PencilIcon, PlusCircleIcon } from 'lucide-vue-next'
import { listLeaveAllocations, createLeaveAllocation, adjustLeaveAllocation } from '../../services/leave-allocation.service'
import type { LeaveAllocation } from '../../services/leave-allocation.service'

const rows = ref<LeaveAllocation[]>([])
const total = ref(0)
const loading = ref(false)
const skip = ref(0)
const limit = ref(50)

const drawerOpen = ref(false)
const form = ref<Partial<LeaveAllocation>>({})
const saving = ref(false)
const errorMsg = ref('')

const adjustDrawerOpen = ref(false)
const adjustTarget = ref<LeaveAllocation | null>(null)
const adjustForm = ref<{ allocation_id: string; adjustment_type: 'allocate' | 'reduce'; adjustment_days: number; reason: string }>({ allocation_id: '', adjustment_type: 'allocate', adjustment_days: 0, reason: '' })
const adjusting = ref(false)
const adjustError = ref('')

const columns = [
  { key: 'employee_id', label: 'Employee' },
  { key: 'leave_type_id', label: 'Leave Type' },
  { key: 'from_date', label: 'From' },
  { key: 'to_date', label: 'To' },
  { key: 'total_leaves_allocated', label: 'Total' },
  { key: 'used_leaves', label: 'Used' },
  { key: 'status', label: 'Status' },
]

async function load() {
  loading.value = true
  try {
    const res = await listLeaveAllocations({ skip: skip.value, limit: limit.value })
    rows.value = res.allocations; total.value = res.total
  } catch {} finally { loading.value = false }
}
onMounted(load)

function openCreate() { form.value = { new_leaves_allocated: 0, carry_forward_days: 0 }; errorMsg.value = ''; drawerOpen.value = true }
function openAdjust(row: LeaveAllocation) {
  adjustTarget.value = row
  adjustForm.value = { allocation_id: row.id, adjustment_type: 'allocate', adjustment_days: 0, reason: '' }
  adjustError.value = ''; adjustDrawerOpen.value = true
}

async function save() {
  saving.value = true; errorMsg.value = ''
  try { await createLeaveAllocation(form.value); drawerOpen.value = false; load() }
  catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function saveAdjust() {
  if (!adjustTarget.value) return
  adjusting.value = true; adjustError.value = ''
  try { await adjustLeaveAllocation(adjustTarget.value.id, adjustForm.value); adjustDrawerOpen.value = false; load() }
  catch (e: any) { adjustError.value = e.message } finally { adjusting.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Leave Allocations" subtitle="View and manage employee leave balances" action-label="+ New Allocation" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No allocations yet.">
      <template #cell-status="{ value }">
        <span :class="{ 'bg-emerald-100 text-emerald-700': value === 'active', 'bg-amber-100 text-amber-700': value === 'expired', 'bg-slate-100 text-slate-500': value === 'cancelled' }" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ value }}</span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end space-x-2">
          <button @click="openAdjust(row)" title="Adjust" class="p-2 rounded-[10px] hover:bg-amber-50 text-slate-400 hover:text-amber-600 transition-colors"><PlusCircleIcon class="w-4 h-4" /></button>
        </div>
      </template>
    </DataTable>

    <!-- Create allocation drawer -->
    <SlideDrawer :open="drawerOpen" title="New Leave Allocation" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Employee ID" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" required />
        <FormInput label="Leave Type ID" :modelValue="form.leave_type_id" @update:modelValue="form.leave_type_id = $event" required />
        <FormInput label="Leave Period ID" :modelValue="form.leave_period_id" @update:modelValue="form.leave_period_id = $event" />
        <FormInput label="From Date" type="date" :modelValue="form.from_date" @update:modelValue="form.from_date = $event" required />
        <FormInput label="To Date" type="date" :modelValue="form.to_date" @update:modelValue="form.to_date = $event" required />
        <FormInput label="New Leaves" type="number" :modelValue="String(form.new_leaves_allocated ?? 0)" @update:modelValue="form.new_leaves_allocated = Number($event)" />
        <FormInput label="Carry Forward Days" type="number" :modelValue="String(form.carry_forward_days ?? 0)" @update:modelValue="form.carry_forward_days = Number($event)" />
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

    <!-- Adjust drawer -->
    <SlideDrawer :open="adjustDrawerOpen" :title="`Adjust Allocation`" width="w-full max-w-md" @close="adjustDrawerOpen = false">
      <div class="space-y-5">
        <div>
          <label class="block text-xs text-slate-500 mb-1">Type</label>
          <select v-model="adjustForm.adjustment_type" class="w-full bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-[12px] px-3 py-2.5 outline-none focus:ring-2 focus:ring-slate-900/10">
            <option value="allocate">Allocate (Add)</option>
            <option value="reduce">Reduce (Deduct)</option>
          </select>
        </div>
        <FormInput label="Days" type="number" :modelValue="String(adjustForm.adjustment_days)" @update:modelValue="adjustForm.adjustment_days = Number($event)" required />
        <FormInput label="Reason" :modelValue="adjustForm.reason" @update:modelValue="adjustForm.reason = $event" />
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="adjustError" class="text-sm text-rose-600">{{ adjustError }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="adjustDrawerOpen = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="saveAdjust" :disabled="adjusting" class="px-6 py-2.5 bg-amber-600 text-white rounded-full font-medium text-sm hover:bg-amber-700 transition-all disabled:opacity-60">{{ adjusting ? 'Saving...' : 'Adjust' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
