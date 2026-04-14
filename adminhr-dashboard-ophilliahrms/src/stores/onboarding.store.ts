import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getOnboardingStatus,
  completeStep,
  completeWizard,
  applyTemplate,
} from '../services/onboarding.service'
import type { OnboardingStatus, ApplyTemplateResult } from '../services/onboarding.service'
import { handleApiError } from '../utils/handleApiError'

export const useOnboardingStore = defineStore('onboarding', () => {
  const status = ref<OnboardingStatus | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const activeIndex = ref(0)

  // ─── Computed ───────────────────────────────────────────────────────────────
  const currentStepIndex = computed(() => activeIndex.value)

  const isComplete = computed(() => status.value?.status === 'FULLY_ONBOARDED')

  const currentStep = computed(() =>
    status.value?.steps[activeIndex.value] ?? null
  )

  const nextPendingStepKey = computed(() => {
    if (!status.value) return null
    const pending = status.value.steps.find(s => s.status === 'PENDING')
    return pending?.step_key ?? null
  })

  const completedCount = computed(() =>
    status.value?.steps.filter(s =>
      s.status === 'COMPLETED' || s.status === 'SKIPPED'
    ).length ?? 0
  )

  // ─── Actions ────────────────────────────────────────────────────────────────
  function setActiveIndex(i: number) {
    activeIndex.value = i
  }

  async function fetchStatus(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      status.value = await getOnboardingStatus()
    } catch (e) {
      error.value = handleApiError(e)
    } finally {
      loading.value = false
    }
  }

  async function markStep(key: string, skipped = false): Promise<void> {
    // Optimistic update — rollback on failure
    const step = status.value?.steps.find(s => s.step_key === key)
    const prevStatus = step?.status
    if (step) step.status = skipped ? 'SKIPPED' : 'COMPLETED'

    try {
      await completeStep(key, skipped)
      await fetchStatus() // authoritative re-sync
    } catch (e) {
      // Rollback optimistic update
      if (step && prevStatus) step.status = prevStatus
      throw e
    }
  }

  async function finishWizard(): Promise<void> {
    await completeWizard()
    await fetchStatus()
  }

  async function applyRegionTemplate(region: string): Promise<ApplyTemplateResult> {
    const result = await applyTemplate(region)
    await fetchStatus() // always re-sync after template application
    return result
  }

  return {
    status,
    loading,
    error,
    activeIndex,
    currentStepIndex,
    isComplete,
    currentStep,
    nextPendingStepKey,
    completedCount,
    setActiveIndex,
    fetchStatus,
    markStep,
    finishWizard,
    applyRegionTemplate,
  }
})
