<script setup lang="ts">
import { ref } from 'vue'
import { CheckCircle2Icon, AlertTriangleIcon, InfoIcon, XIcon } from 'lucide-vue-next'
import { useOnboardingStore } from '../../stores/onboarding.store'
import { handleApiError } from '../../utils/handleApiError'
import type { ApplyTemplateResult } from '../../services/onboarding.service'

const emit = defineEmits<{
  applied: [result: ApplyTemplateResult]
  skip: []
}>()

const store = useOnboardingStore()
const selectedRegion = ref<'IN' | 'US' | null>(null)
const applying = ref(false)
const canApply = ref(true)
const errorMsg = ref('')
const result = ref<ApplyTemplateResult | null>(null)

const templates = [
  {
    region: 'IN' as const,
    flag: '🇮🇳',
    name: 'India',
    leaves: ['Casual Leave — 12 days', 'Sick Leave — 10 days', 'Earned Leave — 15 days', 'Maternity Leave — 182 days', 'Paternity Leave — 15 days'],
    salary: 'Basic 50% · HRA 20% · Allowances 15% · PF 12% · ESI 1.75% · PT ₹200',
  },
  {
    region: 'US' as const,
    flag: '🇺🇸',
    name: 'United States',
    leaves: ['PTO — 15 days', 'Sick Leave — 10 days', 'Personal Day — 3 days', 'Parental Leave — 60 days'],
    salary: 'Basic 70% · Allowances 18% · 401k 6% · No ESI/PT',
  },
]

async function applySelected() {
  if (!selectedRegion.value || !canApply.value) return
  applying.value = true
  canApply.value = false
  errorMsg.value = ''
  result.value = null

  try {
    const res = await store.applyRegionTemplate(selectedRegion.value)
    result.value = res

    if (res.status === 'COMPLETED' || res.status === 'ALREADY_APPLIED') {
      setTimeout(() => emit('applied', res), 800)
    }
    // PARTIAL / FAILED — stay open to show saga steps
  } catch (e) {
    errorMsg.value = handleApiError(e)
  } finally {
    applying.value = false
    setTimeout(() => { canApply.value = true }, 2000)
  }
}

function sagaStatusClass(status: string): string {
  if (status === 'COMPLETED') return 'text-emerald-600 bg-emerald-50'
  if (status === 'FAILED') return 'text-rose-600 bg-rose-50'
  return 'text-slate-500 bg-slate-50'
}
</script>

<template>
  <div class="flex items-center justify-center min-h-[70vh]">
    <div class="w-full max-w-2xl">

      <!-- Header -->
      <div class="text-center mb-8">
        <h2 class="text-2xl font-bold text-slate-900 tracking-tight">Quick Start with a Template</h2>
        <p class="text-slate-500 mt-2 text-sm font-medium">
          Apply regional defaults to auto-configure leave policies and salary structure.
          You can customise everything after.
        </p>
      </div>

      <!-- Saga result (PARTIAL / FAILED) -->
      <div v-if="result && (result.status === 'PARTIAL' || result.status === 'FAILED')" class="mb-6">
        <div class="flex items-start space-x-3 p-4 bg-amber-50 border border-amber-200 rounded-[14px] mb-4">
          <AlertTriangleIcon class="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p class="text-sm font-semibold text-amber-800">Template applied partially</p>
            <p class="text-xs text-amber-600 mt-0.5">Some steps failed. Review below and continue manually for failed steps.</p>
          </div>
        </div>
        <div class="space-y-2">
          <div
            v-for="step in result.saga_steps"
            :key="step.step"
            class="flex items-center justify-between px-4 py-2.5 rounded-[10px] border border-slate-100"
          >
            <span class="text-sm font-medium text-slate-700 capitalize">{{ step.step.replace(/_/g, ' ') }}</span>
            <div class="flex items-center space-x-2">
              <span v-if="step.error" class="text-xs text-rose-500">{{ step.error }}</span>
              <span :class="['text-xs font-semibold px-2 py-0.5 rounded-full', sagaStatusClass(step.status)]">
                {{ step.status }}
              </span>
            </div>
          </div>
        </div>
        <button @click="emit('skip')" class="mt-4 w-full px-5 py-2.5 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-colors">
          Continue Setup Manually
        </button>
      </div>

      <!-- Already applied -->
      <div v-else-if="result?.status === 'ALREADY_APPLIED'" class="mb-6">
        <div class="flex items-start space-x-3 p-4 bg-blue-50 border border-blue-200 rounded-[14px]">
          <InfoIcon class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <p class="text-sm text-blue-700 font-medium">A template has already been applied to this workspace.</p>
        </div>
      </div>

      <!-- Template cards -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <button
          v-for="t in templates"
          :key="t.region"
          @click="selectedRegion = t.region"
          :class="[
            'text-left p-6 rounded-[20px] border-2 transition-all duration-200',
            selectedRegion === t.region
              ? 'border-slate-900 bg-slate-900/5 shadow-md'
              : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm',
          ]"
        >
          <div class="flex items-center justify-between mb-4">
            <span class="text-3xl">{{ t.flag }}</span>
            <div v-if="selectedRegion === t.region" class="w-5 h-5 bg-slate-900 rounded-full flex items-center justify-center">
              <CheckCircle2Icon class="w-3.5 h-3.5 text-white" />
            </div>
          </div>
          <p class="font-bold text-slate-900 text-base mb-3">{{ t.name }}</p>
          <div class="space-y-1 mb-4">
            <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide">Leave Types</p>
            <ul class="space-y-0.5">
              <li v-for="leave in t.leaves" :key="leave" class="text-xs text-slate-600">• {{ leave }}</li>
            </ul>
          </div>
          <div>
            <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">Salary Structure</p>
            <p class="text-xs text-slate-600 leading-relaxed">{{ t.salary }}</p>
          </div>
        </button>
      </div>

      <!-- Error -->
      <p v-if="errorMsg" class="text-sm text-rose-600 text-center mb-4">{{ errorMsg }}</p>

      <!-- Actions -->
      <div v-if="!result || (result.status !== 'PARTIAL' && result.status !== 'FAILED')" class="flex flex-col sm:flex-row gap-3">
        <button
          @click="applySelected"
          :disabled="!selectedRegion || applying || !canApply"
          class="flex-1 px-6 py-3 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          <div v-if="applying" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span>{{ applying ? 'Applying template...' : 'Apply Template' }}</span>
        </button>
        <button
          @click="emit('skip')"
          :disabled="applying"
          class="px-6 py-3 border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-full text-sm font-semibold transition-colors disabled:opacity-50"
        >
          Set Up Manually
        </button>
      </div>
    </div>
  </div>
</template>
