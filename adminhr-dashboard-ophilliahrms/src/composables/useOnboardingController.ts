import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useOnboardingStore } from '../stores/onboarding.store'
import { decodeToken } from '../services/auth.service'
import { getToken } from '../services/http'
import { trackEvent } from '../utils/trackEvent'

export function useOnboardingController() {
  const store = useOnboardingStore()
  const router = useRouter()
  const userRole = decodeToken(getToken())?.role ?? ''

  // ─── Computed ───────────────────────────────────────────────────────────────
  const activeStep = computed(() => store.currentStep)

  const canAccessStep = (stepKey: string): boolean => {
    // Permissions enforced per-step in stepConfig.ts
    // attendance_policy and salary_structure are admin-only
    const adminOnly = ['attendance_policy', 'salary_structure']
    if (adminOnly.includes(stepKey) && userRole === 'hr') return false
    return true
  }

  const canEditCurrentStep = computed(() => {
    if (!activeStep.value) return false
    return canAccessStep(activeStep.value.step_key)
  })

  // ─── Navigation ─────────────────────────────────────────────────────────────
  function goToStep(index: number): void {
    const step = store.status?.steps[index]
    if (step) {
      trackEvent('onboarding.step_started', { step_key: step.step_key })
    }
    store.setActiveIndex(index)
  }

  // ─── Step Completion ─────────────────────────────────────────────────────────
  async function completeCurrentStep(skipped = false): Promise<void> {
    if (!activeStep.value) return

    const stepKey = activeStep.value.step_key

    try {
      await store.markStep(stepKey, skipped)

      if (skipped) {
        trackEvent('onboarding.step_skipped', { step_key: stepKey })
      } else {
        trackEvent('onboarding.step_completed', { step_key: stepKey })
      }

      if (store.isComplete) {
        await store.finishWizard()
        router.push('/dashboard?tab=employees')
        return
      }

      // Advance to next PENDING step
      const steps = store.status?.steps ?? []
      const nextIdx = steps.findIndex(
        (s, i) => i > store.currentStepIndex && s.status === 'PENDING'
      )
      if (nextIdx >= 0) {
        goToStep(nextIdx)
      }
    } catch (e) {
      trackEvent('onboarding.step_failed', { step_key: stepKey })
      throw e
    }
  }

  // ─── Exit ────────────────────────────────────────────────────────────────────
  function saveAndExit(): void {
    trackEvent('onboarding.wizard_abandoned', {
      progress_percent: store.status?.progress_percent ?? 0,
    })
    router.push('/dashboard')
  }

  return {
    activeStep,
    userRole,
    canAccessStep,
    canEditCurrentStep,
    goToStep,
    completeCurrentStep,
    saveAndExit,
  }
}
