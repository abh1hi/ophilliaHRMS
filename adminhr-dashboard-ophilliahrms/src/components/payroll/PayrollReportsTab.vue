<script setup lang="ts">
import { ref } from 'vue'
import { usePayrollStore } from '@/stores/payroll.store'
import { Button } from '@/components/ui/button'
import BadgeChip from '@/components/ui/BadgeChip.vue'
import { 
  FileText, 
  Landmark, 
  ClipboardCheck, 
  ShieldAlert, 
  CreditCard, 
  BarChart3, 
  Download, 
  Info,
  Clock,
  ExternalLink
} from 'lucide-vue-next'

const payrollStore = usePayrollStore()
const downloadingECR = ref(false)
const downloadingBankAdvice = ref(false)

const formatCurrency = (amount: number) => {
  return amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

const downloadECR = async () => {
  if (!payrollStore.currentRun) return
  try {
    downloadingECR.value = true
    console.log('Downloading ECR for run:', payrollStore.currentRun.id)
  } catch (err) {
    console.error('Failed to download ECR', err)
  } finally {
    downloadingECR.value = false
  }
}

const downloadBankAdvice = async () => {
  if (!payrollStore.currentRun) return
  try {
    downloadingBankAdvice.value = true
    console.log('Downloading Bank Advice for run:', payrollStore.currentRun.id)
  } catch (err) {
    console.error('Failed to download bank advice', err)
  } finally {
    downloadingBankAdvice.value = false
  }
}

const reportTypes = [
  {
    id: 'ecr',
    title: 'EPF Employee Contribution Return (ECR)',
    description: 'EPFO Contribution Return file for monthly submission to the provident fund portal',
    icon: FileText,
    iconColor: 'text-blue-600',
    bgColor: 'bg-blue-50/50',
    action: downloadECR,
    loading: downloadingECR,
    btnText: 'Download ECR',
    comingSoon: false
  },
  {
    id: 'bank-advice',
    title: 'Salary Bank Transfer File',
    description: 'CSV file with employee bank account details and net salary amounts for fund transfer',
    icon: Landmark,
    iconColor: 'text-emerald-600',
    bgColor: 'bg-emerald-50/50',
    action: downloadBankAdvice,
    loading: downloadingBankAdvice,
    btnText: 'Download CSV',
    comingSoon: false
  },
  {
    id: 'form-16',
    title: 'Form 16',
    description: 'Tax deduction certificate for employee annual income tax filing',
    icon: ClipboardCheck,
    iconColor: 'text-indigo-600',
    bgColor: 'bg-indigo-50/50',
    comingSoon: true
  },
  {
    id: 'esic',
    title: 'ESIC Return',
    description: 'Employee State Insurance monthly return data for compliance submission',
    icon: ShieldAlert,
    iconColor: 'text-amber-600',
    bgColor: 'bg-amber-50/50',
    comingSoon: true
  },
  {
    id: 'pt',
    title: 'Professional Tax Challan',
    description: 'Professional Tax payment challan segmented by state for statutory compliance',
    icon: CreditCard,
    iconColor: 'text-rose-600',
    bgColor: 'bg-rose-50/50',
    comingSoon: true
  },
  {
    id: 'lwf',
    title: 'Labour Welfare Fund Report',
    description: 'Labour Welfare Fund monthly contribution summary for statutory filing',
    icon: BarChart3,
    iconColor: 'text-slate-600',
    bgColor: 'bg-slate-50/50',
    comingSoon: true
  }
]
</script>

<template>
  <div class="space-y-10">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="report in reportTypes" 
        :key="report.id"
        class="group bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl border border-white/20 dark:border-white/10 rounded-[28px] p-8 hover:shadow-2xl hover:shadow-slate-200/50 dark:hover:shadow-none transition-all duration-500 overflow-hidden relative"
      >
        <!-- Card Decoration -->
        <div class="absolute -right-8 -top-8 w-24 h-24 bg-slate-900/5 rounded-full blur-2xl group-hover:bg-slate-900/10 transition-colors"></div>

        <div class="flex items-start justify-between mb-6">
          <div :class="['w-12 h-12 rounded-2xl flex items-center justify-center border border-white/40', report.bgColor]">
            <component :is="report.icon" :class="['w-6 h-6', report.iconColor]" />
          </div>
          <BadgeChip v-if="report.comingSoon" variant="secondary" class="font-bold tracking-widest text-[9px] uppercase">Coming Soon</BadgeChip>
          <div v-else-if="!payrollStore.currentRun" class="flex items-center gap-1.5 text-[9px] font-bold text-rose-500 uppercase tracking-widest animate-pulse">
             <Clock class="w-3 h-3" /> Select Cycle
          </div>
        </div>

        <h3 class="font-black text-slate-900 dark:text-slate-100 text-lg tracking-tight mb-2">{{ report.title }}</h3>
        <p class="text-[11px] leading-relaxed text-muted-foreground font-medium mb-8">
          {{ report.description }}
        </p>

        <Button 
          v-if="!report.comingSoon"
          @click="report.action"
          :disabled="!payrollStore.currentRun || report.loading?.value"
          variant="outline"
          class="w-full h-11 rounded-2xl border-slate-200 text-slate-700 hover:bg-slate-50 font-bold uppercase tracking-wider text-[11px] group/btn"
        >
          <Download v-if="!report.loading?.value" class="w-4 h-4 mr-2 group-hover/btn:translate-y-0.5 transition-transform" />
          <div v-else class="w-4 h-4 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin mr-2"></div>
          {{ report.loading?.value ? 'Preparing File...' : report.btnText }}
        </Button>
        <Button 
          v-else
          disabled
          variant="ghost"
          class="w-full h-11 rounded-2xl border border-dashed border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-[11px]"
        >
          Coming Soon
        </Button>
      </div>
    </div>

    <!-- Info Banner -->
    <div class="bg-indigo-50/50 dark:bg-indigo-900/10 border border-indigo-100/50 dark:border-indigo-500/10 rounded-[32px] p-8 flex items-center gap-6 animate-in slide-in-from-bottom-2">
      <div class="h-14 w-14 rounded-[22px] bg-white dark:bg-slate-900 shadow-sm flex items-center justify-center shrink-0">
        <Info class="w-6 h-6 text-indigo-500" />
      </div>
      <div class="flex-1">
        <h4 class="text-sm font-black text-slate-900 dark:text-slate-100 tracking-tight">Compliance Readiness</h4>
        <p class="text-[11px] text-muted-foreground font-medium mt-1">
          To generate specific reports, ensure you have an <span class="text-indigo-600 font-bold">active Payroll Cycle</span> selected. 
          Compliance documents are generated in real-time based on calculated ledger entries.
        </p>
      </div>
      <Button variant="link" class="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-600">
        Go to Cycles <ExternalLink class="w-3 h-3 ml-2" />
      </Button>
    </div>
  </div>
</template>
