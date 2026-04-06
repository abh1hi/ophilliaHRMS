<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import FormInput from '../ui/FormInput.vue'
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
  allocation: 'bg-emerald-100 text-emerald-700',
  application: 'bg-blue-100 text-blue-700',
  adjustment: 'bg-amber-100 text-amber-700',
  encashment: 'bg-purple-100 text-purple-700',
  carry_forward: 'bg-cyan-100 text-cyan-700',
}

const columns = [
  { key: 'employee_id', label: 'Employee' },
  { key: 'leave_type_id', label: 'Leave Type' },
  { key: 'from_date', label: 'From' },
  { key: 'to_date', label: 'To' },
  { key: 'leaves', label: 'Days' },
  { key: 'transaction_type', label: 'Type' },
  { key: 'created_at', label: 'Created' },
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
  <div class="space-y-6">
    <PageHeader title="Leave Ledger" subtitle="Immutable audit trail of all leave balance changes" />

    <!-- Filters -->
    <div class="bg-white/70 backdrop-blur-md rounded-[24px] border border-slate-200/50 p-5">
      <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
        <FormInput label="Employee ID" :modelValue="filterEmployeeId" @update:modelValue="filterEmployeeId = $event" />
        <FormInput label="Leave Type ID" :modelValue="filterLeaveTypeId" @update:modelValue="filterLeaveTypeId = $event" />
        <div>
          <label class="block text-xs text-slate-500 mb-1">Transaction Type</label>
          <select v-model="filterTxType" class="w-full bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-[12px] px-3 py-2.5 outline-none">
            <option value="">All</option>
            <option value="allocation">Allocation</option>
            <option value="application">Application</option>
            <option value="adjustment">Adjustment</option>
            <option value="encashment">Encashment</option>
            <option value="carry_forward">Carry Forward</option>
          </select>
        </div>
        <FormInput label="From Date" type="date" :modelValue="filterFromDate" @update:modelValue="filterFromDate = $event" />
        <FormInput label="To Date" type="date" :modelValue="filterToDate" @update:modelValue="filterToDate = $event" />
      </div>
      <div class="mt-3 flex justify-end">
        <button @click="load" class="px-5 py-2 bg-slate-900 text-white text-sm rounded-full font-medium hover:bg-slate-800 transition-colors">Apply Filters</button>
      </div>
    </div>

    <div v-if="total > 0" class="text-sm text-slate-500 px-1">{{ total }} entries found</div>

    <DataTable :columns="columns" :rows="rows" :loading="loading" empty-text="No ledger entries found.">
      <template #cell-leaves="{ value }">
        <span :class="value >= 0 ? 'text-emerald-700 font-semibold' : 'text-rose-600 font-semibold'">{{ value >= 0 ? '+' : '' }}{{ value }}</span>
      </template>
      <template #cell-transaction_type="{ value }">
        <span :class="TX_CLASSES[value] ?? 'bg-slate-100 text-slate-600'" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ value?.replace('_', ' ') }}</span>
      </template>
    </DataTable>
  </div>
</template>
