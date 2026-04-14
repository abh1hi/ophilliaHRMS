<script setup lang="ts">
import { computed } from 'vue'
import {
  CheckCircle2Icon,
  SkipForwardIcon,
  XCircleIcon,
  CircleIcon,
  LogOutIcon,
} from 'lucide-vue-next'
import { useOnboardingStore } from '../../stores/onboarding.store'
import { useOnboardingController } from '../../composables/useOnboardingController'
import { STEP_CONFIG, TOTAL_ESTIMATED_MINUTES } from './stepConfig'
import type { OnboardingStep } from '../../services/onboarding.service'

const store = useOnboardingStore()
const controller = useOnboardingController()

const remainingMinutes = computed(() => {
  if (!store.status) return TOTAL_ESTIMATED_MINUTES
  const pending = store.status.steps.filter(
    s => s.status === 'PENDING' || s.status === 'IN_PROGRESS'
  )
  return pending.reduce((sum, s) => sum + (STEP_CONFIG[s.step_key]?.estimatedMinutes ?? 1), 0)
})

function statusIcon(step: OnboardingStep, index: number) {
  if (step.status === 'COMPLETED') return CheckCircle2Icon
  if (step.status === 'SKIPPED') return SkipForwardIcon
  if (step.status === 'FAILED') return XCircleIcon
  return CircleIcon
}

function stepClass(step: OnboardingStep, index: number): string {
  const isActive = index === store.currentStepIndex
  if (isActive) return 'bg-slate-900 text-white'
  if (step.status === 'COMPLETED') return 'text-emerald-600'
  if (step.status === 'SKIPPED') return 'text-slate-400'
  if (step.status === 'FAILED') return 'text-rose-500'
  return 'text-slate-400 hover:text-slate-700'
}

function iconClass(step: OnboardingStep, index: number): string {
  const isActive = index === store.currentStepIndex
  if (isActive) return 'text-white'
  if (step.status === 'COMPLETED') return 'text-emerald-500'
  if (step.status === 'FAILED') return 'text-rose-500'
  if (step.status === 'SKIPPED') return 'text-slate-300'
  return 'text-slate-300'
}
</script>

<template>
  <aside class="w-72 min-h-screen bg-white border-r border-slate-200/70 flex flex-col">
    <!-- Header -->
    <div class="p-7 border-b border-slate-100">
      <div class="flex items-center space-x-3 mb-5">
        <div class="w-9 h-9 bg-slate-900 rounded-[12px] flex items-center justify-center shadow-sm flex-shrink-0">
          <span class="text-white text-base font-bold font-serif italic leading-none">O</span>
        </div>
        <div>
          <p class="text-sm font-bold text-slate-900 leading-tight">Workspace Setup</p>
          <p class="text-xs text-slate-400 font-medium">~{{ remainingMinutes }} min remaining</p>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="space-y-1.5">
        <div class="flex justify-between items-center">
          <span class="text-xs font-semibold text-slate-600">{{ store.status?.progress_percent ?? 0 }}% complete</span>
          <span class="text-xs text-slate-400">{{ store.completedCount }}/{{ store.status?.steps.length ?? 5 }} steps</span>
        </div>
        <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            class="h-full bg-emerald-500 rounded-full transition-all duration-500"
            :style="`width: ${store.status?.progress_percent ?? 0}%`"
          ></div>
        </div>
      </div>
    </div>

    <!-- Steps -->
    <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
      <button
        v-for="(step, index) in (store.status?.steps ?? [])"
        :key="step.step_key"
        @click="controller.goToStep(index)"
        :class="[
          'w-full text-left flex items-start space-x-3 px-3 py-3 rounded-[12px] transition-all duration-200 group',
          index === store.currentStepIndex
            ? 'bg-slate-900 shadow-sm'
            : 'hover:bg-slate-50',
        ]"
      >
        <!-- Step icon -->
        <div :class="['flex-shrink-0 mt-0.5', iconClass(step, index)]">
          <component :is="statusIcon(step, index)" class="w-5 h-5" />
        </div>

        <!-- Step info -->
        <div class="flex-1 min-w-0">
          <p :class="[
            'text-sm font-semibold leading-tight truncate',
            index === store.currentStepIndex ? 'text-white' : 'text-slate-700',
          ]">
            {{ step.label }}
          </p>
          <p :class="[
            'text-xs mt-0.5 truncate',
            index === store.currentStepIndex ? 'text-white/60' : 'text-slate-400',
          ]">
            {{ STEP_CONFIG[step.step_key]?.description }}
          </p>
        </div>

        <!-- Status badge for non-active -->
        <span
          v-if="index !== store.currentStepIndex && step.status !== 'PENDING'"
          :class="[
            'flex-shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded-full uppercase tracking-wide mt-0.5',
            step.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-600' :
            step.status === 'SKIPPED'   ? 'bg-slate-100 text-slate-400' :
            step.status === 'FAILED'    ? 'bg-rose-100 text-rose-600' : '',
          ]"
        >
          {{ step.status === 'COMPLETED' ? 'Done' : step.status === 'SKIPPED' ? 'Skip' : 'Fail' }}
        </span>
      </button>
    </nav>

    <!-- Save & Exit -->
    <div class="p-4 border-t border-slate-100">
      <button
        @click="controller.saveAndExit()"
        class="w-full flex items-center justify-center space-x-2 px-4 py-2.5 text-slate-500 hover:text-slate-800 hover:bg-slate-50 rounded-[10px] text-sm font-medium transition-colors"
      >
        <LogOutIcon class="w-4 h-4" />
        <span>Save & Exit</span>
      </button>
    </div>
  </aside>
</template>
