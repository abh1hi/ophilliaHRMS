<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePayrollStore } from '@/stores/payroll.store'
import type { PayrollRun } from '@/types/payroll.types'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import FormInput from '@/components/ui/FormInput.vue'
import FormSelect from '@/components/ui/FormSelect.vue'
import { 
  Plus, 
  Calendar, 
  IndianRupee, 
  Users, 
  ArrowRight, 
  Clock, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-vue-next'

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
  return `${startDate.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })} - ${endDate.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}`
}

const formatCurrency = (amount: number) => {
  return amount.toLocaleString('en-IN', { 
    style: 'currency', 
    currency: 'INR', 
    maximumFractionDigits: 0 
  })
}

const formatDate = (date?: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
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

const runTypeOptions = [
  { value: 'REGULAR', label: 'Regular' },
  { value: 'OFF_CYCLE', label: 'Off-Cycle' },
  { value: 'BONUS', label: 'Bonus' },
  { value: 'FNF', label: 'Full & Final' },
]

const getStatusStyles = (status: string) => {
  switch (status.toLowerCase()) {
    case 'open': return 'bg-blue-100/50 text-blue-700 border-blue-200/50'
    case 'processed': return 'bg-emerald-100/50 text-emerald-700 border-emerald-200/50'
    case 'paid': return 'bg-indigo-100/50 text-indigo-700 border-indigo-200/50'
    default: return 'bg-slate-100/50 text-slate-500 border-slate-200/50'
  }
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-xs font-bold uppercase tracking-widest text-muted-foreground">Recent Cycles</h3>
      </div>
      <Button @click="showDialog = true" class="rounded-full px-6 bg-slate-900 text-white hover:bg-slate-800 shadow-lg shadow-slate-200">
        <Plus class="w-4 h-4 mr-2" /> New Payroll Run
      </Button>
    </div>

    <!-- Create Dialog -->
    <Dialog :open="showDialog" @update:open="showDialog = $event">
      <DialogContent class="sm:max-w-md rounded-[32px] border-white/20 backdrop-blur-2xl">
        <DialogHeader>
          <DialogTitle>Initiate Payroll Run</DialogTitle>
          <DialogDescription>
            Specify the period and type for this calculation cycle.
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-6 py-4">
          <div class="grid grid-cols-2 gap-4">
            <FormInput v-model="form.period_start" label="Period Start" type="date" required />
            <FormInput v-model="form.period_end" label="Period End" type="date" required />
          </div>
          <FormSelect v-model="form.run_type" label="Run Type" :options="runTypeOptions" />
        </div>

        <DialogFooter>
          <Button variant="outline" @click="showDialog = false" class="rounded-full px-6">Cancel</Button>
          <Button 
            @click="handleCreate" 
            :disabled="payrollStore.isLoading" 
            class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800"
          >
            {{ payrollStore.isLoading ? 'Processing...' : 'Start Cycle' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Loading State -->
    <div v-if="payrollStore.isLoading && !payrollStore.payrollRuns?.length" class="flex flex-col items-center justify-center py-20 gap-4">
      <div class="w-10 h-10 border-4 border-slate-200 border-t-slate-900 rounded-full animate-spin"></div>
      <p class="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">Synchronizing Payroll Data...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!payrollStore.payrollRuns?.length" class="flex flex-col items-center justify-center py-20 bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl border border-dashed rounded-[32px]">
      <div class="h-16 w-16 rounded-full bg-slate-50 flex items-center justify-center mb-4">
        <IndianRupee class="w-8 h-8 text-slate-300" />
      </div>
      <h3 class="text-sm font-bold text-slate-900">No Payroll Runs Initiated</h3>
      <p class="text-[11px] text-muted-foreground mt-1 mb-6">Start your first payroll cycle to see insights here.</p>
      <Button @click="showDialog = true" variant="outline" class="rounded-full px-8">
        <Plus class="w-4 h-4 mr-2" /> Create First Run
      </Button>
    </div>

    <!-- Payroll Runs Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="run in payrollStore.payrollRuns"
        :key="run.id"
        @click="selectRun(run)"
        class="group bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl border border-white/20 dark:border-white/10 rounded-[28px] p-8 hover:shadow-2xl hover:shadow-slate-200/50 dark:hover:shadow-none transition-all duration-500 cursor-pointer relative overflow-hidden"
      >
        <!-- Background Accent -->
        <div class="absolute -right-12 -top-12 w-32 h-32 bg-slate-900/5 rounded-full blur-3xl group-hover:bg-slate-900/10 transition-colors"></div>

        <div class="flex items-center justify-between mb-6">
          <span 
            :class="[
              'px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm', 
              getStatusStyles(run.status)
            ]"
          >
            {{ run.status }}
          </span>
          <ArrowRight class="w-4 h-4 text-slate-300 group-hover:translate-x-1 group-hover:text-slate-900 transition-all" />
        </div>

        <h3 class="font-black text-slate-900 dark:text-slate-100 text-lg tracking-tight mb-1">{{ formatPeriod(run.period_start, run.period_end) }}</h3>
        
        <div class="flex items-center gap-3 text-[11px] font-bold text-muted-foreground uppercase tracking-widest mb-6 border-b border-white/10 pb-4">
           <span>{{ run.run_type || 'REGULAR' }}</span>
           <span class="h-1 w-1 rounded-full bg-slate-300"></span>
           <span class="flex items-center gap-1"><Users class="w-3.5 h-3.5" /> {{ run.total_employees }}</span>
        </div>

        <!-- Financial Summary -->
        <div class="space-y-3.5 mb-8">
          <div class="flex justify-between items-end">
            <span class="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Gross Payout</span>
            <span class="font-bold text-slate-900">{{ formatCurrency(run.total_gross) }}</span>
          </div>
          <div class="flex justify-between items-end">
            <span class="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Deductions</span>
            <span class="font-bold text-rose-600">-{{ formatCurrency(run.total_deductions) }}</span>
          </div>
          <div class="pt-4 border-t border-slate-100/50 flex justify-between items-baseline">
            <span class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Net Payout</span>
            <span class="text-2xl font-black text-slate-900 tracking-tighter">{{ formatCurrency(run.total_net) }}</span>
          </div>
        </div>

        <!-- Meta -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5 text-[10px] font-bold text-muted-foreground uppercase">
             <Clock class="w-3 h-3" />
             <span>Created {{ formatDate(run.created_at) }}</span>
          </div>
          <div v-if="run.status === 'PAID'" class="flex items-center gap-1 text-[10px] font-bold text-emerald-600 uppercase">
             <CheckCircle2 class="w-3 h-3" />
             <span>Settled</span>
          </div>
          <div v-else class="flex items-center gap-1 text-[10px] font-bold text-amber-600 uppercase">
             <AlertCircle class="w-3 h-3" />
             <span>Processing</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
