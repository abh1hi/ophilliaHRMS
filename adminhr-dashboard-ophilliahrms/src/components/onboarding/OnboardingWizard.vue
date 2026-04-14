<script setup lang="ts">
import { ref, computed } from 'vue'
import { useOnboardingStore } from '../../stores/onboarding.store'
import { useOnboardingController } from '../../composables/useOnboardingController'
import { STEP_CONFIG } from './stepConfig'
import OnboardingStepNav from './OnboardingStepNav.vue'
import TemplatePickerModal from './TemplatePickerModal.vue'
import type { ApplyTemplateResult } from '../../services/onboarding.service'

const store = useOnboardingStore()
const controller = useOnboardingController()

// Show template picker when onboarding is brand new (NOT_STARTED)
const showTemplatePicker = ref(store.status?.status === 'NOT_STARTED')

const currentStepComponent = computed(() => {
  const step = store.currentStep
  if (!step) return null
  return STEP_CONFIG[step.step_key]?.component ?? null
})

function onTemplateApplied(_result: ApplyTemplateResult) {
  showTemplatePicker.value = false
  // Status is already re-fetched inside store.applyRegionTemplate()
}

async function onStepCompleted() {
  await controller.completeCurrentStep(false)
}

async function onStepSkipped() {
  await controller.completeCurrentStep(true)
}
</script>

<template>
  <div class="flex min-h-screen bg-slate-50">
    <!-- Left Sidebar -->
    <OnboardingStepNav />

    <!-- Right Content -->
    <div class="flex-1 overflow-y-auto">
      <!-- Template Picker (first-time) -->
      <div v-if="showTemplatePicker" class="p-10">
        <TemplatePickerModal
          @applied="onTemplateApplied"
          @skip="showTemplatePicker = false"
        />
      </div>

      <!-- Step Content -->
      <div v-else class="p-10 max-w-3xl">
        <!-- Step header bar -->
        <div class="flex items-center justify-between mb-8">
          <div>
            <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">
              Step {{ (store.currentStepIndex ?? 0) + 1 }} of {{ store.status?.steps.length ?? 5 }}
            </p>
          </div>
          <div class="flex items-center space-x-2">
            <span class="text-xs text-slate-400 font-medium">~{{ STEP_CONFIG[store.currentStep?.step_key ?? '']?.estimatedMinutes ?? 1 }} min</span>
          </div>
        </div>

        <!-- Active step component -->
        <component
          v-if="currentStepComponent"
          :is="currentStepComponent"
          :readonly="!controller.canEditCurrentStep.value"
          @completed="onStepCompleted"
          @skipped="onStepSkipped"
        />

        <!-- Fallback: step key not in config (already done / SKIPPED by template) -->
        <div v-else class="flex items-center justify-center min-h-[40vh] text-slate-400 text-sm font-medium">
          Loading step...
        </div>
      </div>
    </div>
  </div>
</template>
