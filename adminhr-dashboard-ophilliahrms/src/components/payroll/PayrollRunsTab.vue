<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePayrollStore } from '@/stores/payroll.store'
import type { PayrollRun } from '@/types/payroll.types'

const payrollStore = usePayrollStore()
const showDialog = ref(false)

const form = ref({
  period_start: '',
  period_end: '',
  run_type: 'REGULAR',
})

const formatPeriod = (start: string, end: string) => {
  const startDate = new Date(start)
  const endDate = new Date(end)
  return `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`
}

const formatCurrency = (amount: number) => {
  return amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

const formatDate = (date?: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString()
}

const selectRun = (run: PayrollRun) => {
  payrollStore.currentRun = run
}

const handleCreate = async () => {
  try {
    await payrollStore.createPayrollRun({
      period_start: form.value.period_start,
      period_end: form.value.period_end,
      run_type: form.value.run_type,
    })
    showDialog.value = false
    form.value = {
      period_start: '',
      period_end: '',
      run_type: 'REGULAR',
    }
  } catch (err) {
    console.error('Failed to create payroll run', err)
  }
}

onMounted(() => {
  payrollStore.fetchPayrollRuns()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Create Dialog -->
    <div v-if="showDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
        <h3 class="text-lg font-bold text-slate-900 mb-4">Create New Payroll Run</h3>

        <div class="space-y-4 mb-6">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Period Start</label>
            <input
              v-model="form.period_start"
              type="date"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Period End</label>
            <input
              v-model="form.period_end"
              type="date"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Run Type</label>
            <select
              v-model="form.run_type"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            >
              <option>REGULAR</option>
              <option>OFF_CYCLE</option>
              <option>BONUS</option>
              <option>FNF</option>
            </select>
          </div>
        </div>

        <div class="flex gap-3 justify-end">
          <button
            @click="showDialog = false"
            class="px-4 py-2 text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            @click="handleCreate"
            :disabled="payrollStore.isLoading"
            class="px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 font-medium transition-colors disabled:opacity-50"
          >
            {{ payrollStore.isLoading ? 'Creating...' : 'Create' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Payroll Runs Grid -->
    <div v-if="payrollStore.isLoading && !payrollStore.payrollRuns?.length" class="text-center py-12">
      <div class="inline-block">
        <div class="w-8 h-8 border-4 border-slate-200 border-t-slate-900 rounded-full animate-spin"></div>
      </div>
    </div>

    <div v-else-if="!payrollStore.payrollRuns?.length" class="text-center py-12">
      <p class="text-slate-500">No payroll runs yet</p>
      <button
        @click="showDialog = true"
        class="mt-4 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 font-medium transition-colors"
      >
        Create First Payroll Run
      </button>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="run in payrollStore.payrollRuns"
        :key="run.id"
        @click="selectRun(run)"
        class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-2xl p-6 hover:shadow-md transition-all cursor-pointer"
      >
        <!-- Status Badge -->
        <div class="flex items-center justify-between mb-4">
          <span class="px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-900">
            {{ run.status }}
          </span>
        </div>

        <!-- Period Info -->
        <h3 class="font-bold text-slate-900 mb-1">{{ formatPeriod(run.period_start, run.period_end) }}</h3>
        <p class="text-sm text-slate-500 mb-4">{{ run.run_type || 'REGULAR' }} • {{ run.total_employees }} employees</p>

        <!-- Financials -->
        <div class="bg-slate-50 rounded-xl p-3 mb-4 space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-slate-600">Gross</span>
            <span class="font-semibold text-slate-900">₹{{ formatCurrency(run.total_gross) }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-slate-600">Deductions</span>
            <span class="font-semibold text-slate-900">₹{{ formatCurrency(run.total_deductions) }}</span>
          </div>
          <div class="flex justify-between text-sm border-t border-slate-200 pt-2">
            <span class="text-slate-600">Net</span>
            <span class="font-bold text-slate-900">₹{{ formatCurrency(run.total_net) }}</span>
          </div>
        </div>

        <!-- Timeline -->
        <p class="text-xs text-slate-500">Created: {{ formatDate(run.created_at) }}</p>
      </div>
    </div>
  </div>
</template>
