<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Button } from '../ui/button'
import { Filter, Search } from 'lucide-vue-next'
import { listLeaveLedgerEntries } from '../../services/leave-ledger.service'
import type { LeaveLedgerEntry } from '../../services/leave-ledger.service'

const rows = ref<LeaveLedgerEntry[]>([])
const total = ref(0)
const loading = ref(false)

const filterEmployeeId = ref('')
const filterLeaveTypeId = ref('')
const filterTxType = ref('')
const filterFromDate = ref('')
const filterToDate = ref('')

const TX_CLASSES: Record<string, string> = {
  allocation: 'bg-emerald-100/50 text-emerald-700 border-emerald-200/50',
  application: 'bg-blue-100/50 text-blue-700 border-blue-200/50',
  adjustment: 'bg-amber-100/50 text-amber-700 border-amber-200/50',
  encashment: 'bg-purple-100/50 text-purple-700 border-purple-200/50',
  carry_forward: 'bg-cyan-100/50 text-cyan-700 border-cyan-200/50',
}

const columns = [
  { key: 'employee_id', label: 'Employee' },
  { key: 'leave_type_id', label: 'Leave Type' },
  { key: 'from_date', label: 'From' },
  { key: 'to_date', label: 'To' },
  { key: 'leaves', label: 'Days Change' },
  { key: 'transaction_type', label: 'Type' },
  { key: 'created_at', label: 'Created' },
]

const txTypeOptions = [
  { value: '', label: 'All Types' },
  { value: 'allocation', label: 'Allocation' },
  { value: 'application', label: 'Application' },
  { value: 'adjustment', label: 'Adjustment' },
  { value: 'encashment', label: 'Encashment' },
  { value: 'carry_forward', label: 'Carry Forward' },
]

async function load() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (filterEmployeeId.value) params.employee_id = filterEmployeeId.value
    if (filterLeaveTypeId.value) params.leave_type_id = filterLeaveTypeId.value
    if (filterTxType.value) params.transaction_type = filterTxType.value
    if (filterFromDate.value) params.from_date = filterFromDate.value
    if (filterToDate.value) params.to_date = filterToDate.value
    const res = await listLeaveLedgerEntries(params)
    rows.value = res.entries; total.value = res.total
  } catch {} finally { loading.value = false }
}
onMounted(load)
</script>

<template>
  <div class="space-y-8">
    <PageHeader title="Leave Ledger" subtitle="Immutable audit trail of all leave balance changes" />

    <!-- Filters -->
    <div class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-8 shadow-sm">
      <div class="flex items-center gap-2 mb-6 text-slate-900 dark:text-slate-50">
        <Filter class="w-4 h-4 text-muted-foreground" />
        <h3 class="text-sm font-bold uppercase tracking-widest">Transaction Filters</h3>
      </div>
      
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
        <FormInput label="Employee ID" :modelValue="filterEmployeeId" @update:modelValue="filterEmployeeId = $event" placeholder="Search ID..." />
        <FormInput label="Leave Type" :modelValue="filterLeaveTypeId" @update:modelValue="filterLeaveTypeId = $event" placeholder="e.g. SL" />
        <FormSelect 
          label="Type" 
          :modelValue="filterTxType" 
          @update:modelValue="filterTxType = $event" 
          :options="txTypeOptions"
        />
        <FormInput label="From Date" type="date" :modelValue="filterFromDate" @update:modelValue="filterFromDate = $event" />
        <FormInput label="To Date" type="date" :modelValue="filterToDate" @update:modelValue="filterToDate = $event" />
      </div>
      
      <div class="mt-8 flex items-center justify-between">
        <p v-if="total > 0" class="text-xs font-medium text-muted-foreground">
          Showing <span class="text-slate-900 dark:text-slate-100 font-bold border-b border-slate-200 pb-0.5">{{ total }}</span> entries
        </p>
        <div v-else></div>
        <Button @click="load" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800 shadow-lg shadow-slate-200 dark:shadow-none">
          <Search class="w-4 h-4 mr-2" /> Apply Filters
        </Button>
      </div>
    </div>

    <DataTable :columns="columns" :rows="rows" :loading="loading" empty-text="No ledger entries found.">
      <template #cell-leaves="{ value }">
        <div class="flex items-center gap-1 font-mono text-[13px]">
          <span 
            :class="value >= 0 ? 'text-emerald-600 bg-emerald-50 px-2 rounded-md' : 'text-rose-600 bg-rose-50 px-2 rounded-md'" 
            class="font-bold py-0.5"
          >
            {{ value >= 0 ? '+' : '' }}{{ value }}
          </span>
        </div>
      </template>
      <template #cell-transaction_type="{ value }">
        <span 
          :class="TX_CLASSES[value] ?? 'bg-slate-100 text-slate-600 border-slate-200'" 
          class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm"
        >
          {{ value?.replace('_', ' ') }}
        </span>
      </template>
    </DataTable>
  </div>
</template>
