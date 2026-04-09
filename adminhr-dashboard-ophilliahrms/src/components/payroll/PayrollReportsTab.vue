<script setup lang="ts">
import { ref } from 'vue'
import { usePayrollStore } from '@/stores/payroll.store'

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
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- ECR Export -->
      <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <span class="text-lg">📄</span>
          </div>
          <h3 class="font-bold text-slate-900">ECR File</h3>
        </div>
        <p class="text-sm text-slate-600 mb-4">EPFO Contribution Return file for monthly submission</p>
        <button
          @click="downloadECR"
          :disabled="!payrollStore.currentRun || downloadingECR"
          class="w-full px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium transition-colors disabled:opacity-50"
        >
          {{ downloadingECR ? 'Downloading...' : 'Download ECR' }}
        </button>
      </div>

      <!-- Bank Advice -->
      <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
            <span class="text-lg">🏦</span>
          </div>
          <h3 class="font-bold text-slate-900">Bank Advice</h3>
        </div>
        <p class="text-sm text-slate-600 mb-4">CSV file with employee bank account details for fund transfer</p>
        <button
          @click="downloadBankAdvice"
          :disabled="!payrollStore.currentRun || downloadingBankAdvice"
          class="w-full px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium transition-colors disabled:opacity-50"
        >
          {{ downloadingBankAdvice ? 'Downloading...' : 'Download CSV' }}
        </button>
      </div>

      <!-- Form 16 -->
      <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <span class="text-lg">📋</span>
          </div>
          <h3 class="font-bold text-slate-900">Form 16</h3>
        </div>
        <p class="text-sm text-slate-600 mb-4">Tax deduction certificate for employee annual tax filing</p>
        <button
          disabled
          class="w-full px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium transition-colors disabled:opacity-50"
        >
          Coming Soon
        </button>
      </div>

      <!-- ESIC Return -->
      <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
            <span class="text-lg">🛡️</span>
          </div>
          <h3 class="font-bold text-slate-900">ESIC Return</h3>
        </div>
        <p class="text-sm text-slate-600 mb-4">ESIC monthly return data for compliance</p>
        <button
          disabled
          class="w-full px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium transition-colors disabled:opacity-50"
        >
          Coming Soon
        </button>
      </div>

      <!-- PT Challan -->
      <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-pink-100 rounded-lg flex items-center justify-center">
            <span class="text-lg">💳</span>
          </div>
          <h3 class="font-bold text-slate-900">PT Challan</h3>
        </div>
        <p class="text-sm text-slate-600 mb-4">Professional Tax payment details by state</p>
        <button
          disabled
          class="w-full px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium transition-colors disabled:opacity-50"
        >
          Coming Soon
        </button>
      </div>

      <!-- LWF Summary -->
      <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
            <span class="text-lg">📊</span>
          </div>
          <h3 class="font-bold text-slate-900">LWF Summary</h3>
        </div>
        <p class="text-sm text-slate-600 mb-4">Labour Welfare Fund contribution summary</p>
        <button
          disabled
          class="w-full px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium transition-colors disabled:opacity-50"
        >
          Coming Soon
        </button>
      </div>
    </div>

    <!-- Info Message -->
    <div class="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-900">
      <strong>Note:</strong> Select a payroll run to enable download options for reports and compliance documents.
    </div>
  </div>
</template>
