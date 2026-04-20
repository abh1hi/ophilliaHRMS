<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Button } from '../ui/button'
import { Pencil, PlusCircle } from 'lucide-vue-next'
import { listLeaveAllocations, createLeaveAllocation, adjustLeaveAllocation } from '../../services/leave-allocation.service'
import type { LeaveAllocation } from '../../services/leave-allocation.service'
import { listLeaveTypes } from '../../services/leave-type.service'

const rows = ref<LeaveAllocation[]>([])
const total = ref(0)
const loading = ref(false)
const leaveTypeMap = ref<Record<string, string>>({})
const skip = ref(0)
const limit = ref(50)

const drawerOpen = ref(false)
const form = ref<Partial<LeaveAllocation>>({})
const saving = ref(false)
const errorMsg = ref('')

const adjustDrawerOpen = ref(false)
const adjustTarget = ref<LeaveAllocation | null>(null)
const adjustForm = ref<{ 
  allocation_id: string; 
  adjustment_type: 'allocate' | 'reduce'; 
  adjustment_days: number; 
  reason: string 
}>({ 
  allocation_id: '', 
  adjustment_type: 'allocate', 
  adjustment_days: 0, 
  reason: '' 
})
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
    const [res, types] = await Promise.all([
      listLeaveAllocations({ skip: skip.value, limit: limit.value }),
      listLeaveTypes(),
    ])
    rows.value = res.allocations; total.value = res.total
    leaveTypeMap.value = Object.fromEntries(types.map(t => [t.id, t.name]))
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
  try {
    const payload = { ...form.value }
    await createLeaveAllocation(payload)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function saveAdjust() {
  if (!adjustTarget.value) return
  adjusting.value = true; adjustError.value = ''
  try {
    const payload = { ...adjustForm.value }
    await adjustLeaveAllocation(adjustTarget.value.id, payload)
    adjustDrawerOpen.value = false; load()
  } catch (e: any) { adjustError.value = e.message } finally { adjusting.value = false }
}

const adjustmentOptions = [
  { value: 'allocate', label: 'Allocate (Add)' },
  { value: 'reduce', label: 'Reduce (Deduct)' },
]
</script>

<template>
  <div class="space-y-8">
    <PageHeader 
      title="Leave Allocations" 
      subtitle="View and manage employee leave balances" 
      action-label="New Allocation" 
      @action="openCreate" 
    />
    
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No allocations yet.">
      <template #cell-leave_type_id="{ value }">
        <span class="text-xs font-medium text-slate-700">{{ leaveTypeMap[value] ?? value }}</span>
      </template>
      <template #cell-status="{ value }">
        <span 
          :class="{ 
            'bg-emerald-100/50 text-emerald-700 border-emerald-200/50': value === 'active', 
            'bg-amber-100/50 text-amber-700 border-amber-200/50': value === 'expired', 
            'bg-slate-100/50 text-slate-500 border-slate-200/50': value === 'cancelled' 
          }" 
          class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm"
        >
          {{ value }}
        </span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <Button variant="ghost" size="icon" @click="openAdjust(row)" title="Adjust Balance" class="h-8 w-8 rounded-lg hover:bg-amber-50 text-slate-400 hover:text-amber-600 transition-colors">
            <PlusCircle class="w-4 h-4" />
          </Button>
        </div>
      </template>
    </DataTable>

    <!-- Create allocation drawer -->
    <SlideDrawer :open="drawerOpen" title="Create Leave Allocation" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6">
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Employee ID" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" placeholder="e.g. EMP001" required />
          <FormInput label="Leave Type ID" :modelValue="form.leave_type_id" @update:modelValue="form.leave_type_id = $event" placeholder="e.g. SL, CL" required />
        </div>
        <FormInput label="Leave Period ID" :modelValue="form.leave_period_id" @update:modelValue="form.leave_period_id = $event" placeholder="e.g. FY24" />
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="From Date" type="date" :modelValue="form.from_date" @update:modelValue="form.from_date = $event" required />
          <FormInput label="To Date" type="date" :modelValue="form.to_date" @update:modelValue="form.to_date = $event" required />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="New Leaves" type="number" :modelValue="String(form.new_leaves_allocated ?? 0)" @update:modelValue="form.new_leaves_allocated = Number($event)" />
          <FormInput label="Carry Forward" type="number" :modelValue="String(form.carry_forward_days ?? 0)" @update:modelValue="form.carry_forward_days = Number($event)" />
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
              {{ saving ? 'Saving...' : 'Create Allocation' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- Adjust drawer -->
    <SlideDrawer :open="adjustDrawerOpen" title="Adjust Leave Balance" width="w-full max-w-lg" @close="adjustDrawerOpen = false">
      <div class="space-y-6">
        <FormSelect 
          label="Adjustment Type" 
          :modelValue="adjustForm.adjustment_type" 
          @update:modelValue="adjustForm.adjustment_type = $event as any" 
          :options="adjustmentOptions"
        />
        <FormInput label="Days to Adjust" type="number" :modelValue="String(adjustForm.adjustment_days)" @update:modelValue="adjustForm.adjustment_days = Number($event)" required />
        <FormInput label="Reason for adjustment" :modelValue="adjustForm.reason" @update:modelValue="adjustForm.reason = $event" placeholder="Brief reason..." />
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="adjustError" class="text-xs text-destructive font-medium">{{ adjustError }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="adjustDrawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="saveAdjust" :disabled="adjusting" class="rounded-full px-8 bg-amber-600 text-white hover:bg-amber-700">
              {{ adjusting ? 'Updating...' : 'Adjust Balance' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
