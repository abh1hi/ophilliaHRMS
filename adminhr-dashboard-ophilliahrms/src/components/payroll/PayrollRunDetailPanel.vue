<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import SlideDrawer from '@/components/ui/SlideDrawer.vue'
import { Button } from '@/components/ui/button'
import { usePayrollStore } from '@/stores/payroll.store'
import type { PayrollRun, Payslip } from '@/types/payroll.types'
import {
  Calculator,
  CheckCircle2,
  CreditCard,
  Banknote,
  Download,
  Users,
  IndianRupee,
  ChevronLeft
} from 'lucide-vue-next'

interface Props {
  open: boolean
  run: PayrollRun | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updated'): void
}>()

const payrollStore = usePayrollStore()
const payslips = ref<Payslip[]>([])
const loadingPayslips = ref(false)
const actionLoading = ref(false)
const actionError = ref<string | null>(null)

watch(() => props.open, async (val) => {
  if (val && props.run) {
    loadingPayslips.value = true
    actionError.value = null
    try {
      payslips.value = await payrollStore.fetchPayslips(props.run.id) ?? []
    } catch {
      payslips.value = []
    } finally {
      loadingPayslips.value = false
    }
  }
})

const statusStyles: Record<string, string> = {
  draft: 'bg-blue-100/50 text-blue-700 border-blue-200',
  open: 'bg-blue-100/50 text-blue-700 border-blue-200',
  computed: 'bg-yellow-100/50 text-yellow-700 border-yellow-200',
  approved: 'bg-teal-100/50 text-teal-700 border-teal-200',
  processing: 'bg-indigo-100/50 text-indigo-700 border-indigo-200',
  processed: 'bg-emerald-100/50 text-emerald-700 border-emerald-200',
  paid: 'bg-slate-100/50 text-slate-700 border-slate-200',
  locked: 'bg-slate-100/50 text-slate-500 border-slate-200',
  failed: 'bg-rose-100/50 text-rose-700 border-rose-200',
}

const formatCurrency = (n?: number) =>
  (n ?? 0).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })

const formatDate = (d: string) =>
  new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })

const lifecycleActions = computed(() => {
  if (!props.run) return []
  const s = props.run.status.toLowerCase()
  const actions = []
  if (s === 'draft' || s === 'open') {
    actions.push({ label: 'Compute', icon: Calculator, handler: () => doAction('compute') })
  }
  if (s === 'computed') {
    actions.push({ label: 'Approve', icon: CheckCircle2, handler: () => doAction('approve') })
  }
  if (s === 'approved') {
    actions.push({ label: 'Process', icon: CreditCard, handler: () => doAction('process') })
  }
  if (s === 'processed') {
    actions.push({ label: 'Mark Paid', icon: Banknote, handler: () => doAction('markPaid') })
  }
  return actions
})

async function doAction(action: string) {
  if (!props.run) return
  actionLoading.value = true
  actionError.value = null
  try {
    if (action === 'compute') await payrollStore.computePayroll(props.run.id)
    else if (action === 'approve') await payrollStore.approvePayroll(props.run.id)
    else if (action === 'process') await payrollStore.processPayroll(props.run.id)
    else if (action === 'markPaid') await payrollStore.markPayrollPaid(props.run.id)
    emit('updated')
  } catch (e: unknown) {
    actionError.value = e instanceof Error ? e.message : 'Action failed'
  } finally {
    actionLoading.value = false
  }
}

async function downloadECR() {
  if (!props.run) return
  try {
    const blob = await import('@/services/payroll.service').then(m => m.payrollService.downloadECR(props.run!.id))
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ecr-${props.run.id}.txt`
    a.click()
    URL.revokeObjectURL(url)
  } catch { /* silent */ }
}

async function downloadBankAdvice() {
  if (!props.run) return
  try {
    const blob = await import('@/services/payroll.service').then(m => m.payrollService.downloadBankAdvice(props.run!.id))
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `bank-advice-${props.run.id}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch { /* silent */ }
}
</script>

<template>
  <SlideDrawer
    :open="open"
    title="Payroll Run Details"
    width="w-full max-w-2xl"
    @close="emit('close')"
  >
    <div v-if="run" class="space-y-8 py-4">
      <!-- Header -->
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Period</p>
          <h3 class="text-xl font-black text-slate-900 tracking-tight">
            {{ formatDate(run.period_start) }} — {{ formatDate(run.period_end) }}
          </h3>
          <p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mt-1">{{ run.run_type || 'REGULAR' }}</p>
        </div>
        <span :class="['px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm shrink-0', statusStyles[run.status.toLowerCase()] ?? 'bg-slate-100 text-slate-500 border-slate-200']">
          {{ run.status }}
        </span>
      </div>

      <!-- Summary Cards -->
      <div class="grid grid-cols-3 gap-4">
        <div class="bg-slate-50/50 rounded-[22px] border border-white/10 p-5 text-center">
          <Users class="w-4 h-4 text-slate-400 mx-auto mb-2" />
          <p class="text-xl font-black text-slate-900">{{ run.total_employees ?? '—' }}</p>
          <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-1">Employees</p>
        </div>
        <div class="bg-slate-50/50 rounded-[22px] border border-white/10 p-5 text-center">
          <IndianRupee class="w-4 h-4 text-slate-400 mx-auto mb-2" />
          <p class="text-xl font-black text-slate-900">{{ formatCurrency(run.total_amount) }}</p>
          <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-1">Net Payout</p>
        </div>
        <div class="bg-slate-50/50 rounded-[22px] border border-white/10 p-5 text-center">
          <p class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Created</p>
          <p class="text-sm font-black text-slate-900">{{ formatDate(run.created_at) }}</p>
        </div>
      </div>

      <!-- Lifecycle Actions -->
      <div v-if="lifecycleActions.length" class="space-y-3">
        <p class="text-[10px] font-black uppercase tracking-widest text-slate-400">Next Action</p>
        <div class="flex gap-3 flex-wrap">
          <Button
            v-for="action in lifecycleActions"
            :key="action.label"
            :disabled="actionLoading"
            @click="action.handler"
            class="rounded-full px-6 h-10 bg-slate-900 text-white hover:bg-slate-800 font-bold uppercase tracking-widest text-[11px]"
          >
            <component :is="action.icon" class="w-4 h-4 mr-2" />
            {{ actionLoading ? 'Processing…' : action.label }}
          </Button>
        </div>
        <p v-if="actionError" class="text-[10px] font-bold text-destructive animate-in fade-in">{{ actionError }}</p>
      </div>

      <!-- Download Buttons -->
      <div class="flex gap-3 flex-wrap">
        <Button variant="outline" @click="downloadECR" class="rounded-full px-5 h-9 font-bold uppercase tracking-widest text-[10px]">
          <Download class="w-3.5 h-3.5 mr-2" /> ECR File
        </Button>
        <Button variant="outline" @click="downloadBankAdvice" class="rounded-full px-5 h-9 font-bold uppercase tracking-widest text-[10px]">
          <Download class="w-3.5 h-3.5 mr-2" /> Bank Advice
        </Button>
      </div>

      <!-- Payslips Table -->
      <div class="space-y-4">
        <p class="text-[10px] font-black uppercase tracking-widest text-slate-400">Payslips</p>

        <div v-if="loadingPayslips" class="flex items-center justify-center py-10 gap-3">
          <div class="w-6 h-6 border-2 border-slate-200 border-t-slate-900 rounded-full animate-spin" />
          <p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Loading payslips…</p>
        </div>

        <div v-else-if="!payslips.length" class="py-10 border border-dashed border-slate-200 rounded-[22px] text-center">
          <p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest">No payslips yet. Compute the run to generate them.</p>
        </div>

        <div v-else class="overflow-hidden rounded-[22px] border border-slate-100">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-slate-50/80 border-b border-slate-100">
                <th class="text-left px-5 py-3 text-[10px] font-black uppercase tracking-widest text-slate-400">Employee</th>
                <th class="text-right px-5 py-3 text-[10px] font-black uppercase tracking-widest text-slate-400">Gross</th>
                <th class="text-right px-5 py-3 text-[10px] font-black uppercase tracking-widest text-slate-400">Deductions</th>
                <th class="text-right px-5 py-3 text-[10px] font-black uppercase tracking-widest text-slate-400">Net</th>
                <th class="text-center px-5 py-3 text-[10px] font-black uppercase tracking-widest text-slate-400">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="slip in payslips"
                :key="slip.id"
                class="border-b border-slate-50 hover:bg-slate-50/50 transition-colors"
              >
                <td class="px-5 py-3 font-bold text-slate-900 text-[12px]">{{ slip.employee_name ?? slip.employee_id }}</td>
                <td class="px-5 py-3 text-right text-[12px] font-bold text-slate-700">{{ formatCurrency(slip.gross_salary) }}</td>
                <td class="px-5 py-3 text-right text-[12px] font-bold text-rose-600">-{{ formatCurrency(slip.deductions) }}</td>
                <td class="px-5 py-3 text-right text-[12px] font-black text-slate-900">{{ formatCurrency(slip.net_salary) }}</td>
                <td class="px-5 py-3 text-center">
                  <span class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-widest bg-slate-100 text-slate-600 border border-slate-200">
                    {{ slip.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <template #footer>
      <Button variant="outline" @click="emit('close')" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">
        <ChevronLeft class="w-4 h-4 mr-1" /> Back to Runs
      </Button>
    </template>
  </SlideDrawer>
</template>
