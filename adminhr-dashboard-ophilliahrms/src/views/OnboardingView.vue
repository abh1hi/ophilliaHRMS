<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useOnboardingStore } from '../stores/onboarding.store'
import OnboardingWizard from '../components/onboarding/OnboardingWizard.vue'

const router = useRouter()
const route = useRoute()
const store = useOnboardingStore()

let pollTimer: ReturnType<typeof setInterval>

onMounted(async () => {
  // Retry once on failure — handles transient gateway 503 at cold start
  await store.fetchStatus()
  if (store.error && !store.status) {
    await new Promise(r => setTimeout(r, 1500))
    await store.fetchStatus()
  }

  if (store.isComplete) {
    router.push('/dashboard')
    return
  }

  // Deep-link support: /onboarding?step=attendance_policy
  const stepParam = route.query.step as string
  if (stepParam && store.status) {
    const idx = store.status.steps.findIndex(s => s.step_key === stepParam)
    if (idx >= 0) store.setActiveIndex(idx)
  }

  // Poll every 30s while tab is visible — handles multi-tab concurrency
  pollTimer = setInterval(async () => {
    if (!document.hidden) await store.fetchStatus()
  }, 30_000)
})

onUnmounted(() => clearInterval(pollTimer))
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <!-- Loading state -->
    <div v-if="store.loading && !store.status" class="flex items-center justify-center min-h-screen">
      <div class="text-center space-y-3">
        <div class="w-10 h-10 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p class="text-slate-500 text-sm font-medium">Loading workspace setup...</p>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="store.error && !store.status" class="flex items-center justify-center min-h-screen">
      <div class="text-center space-y-4 max-w-sm">
        <p class="text-rose-600 font-medium">{{ store.error }}</p>
        <button @click="store.fetchStatus()" class="px-5 py-2.5 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition-colors">
          Retry
        </button>
      </div>
    </div>

    <!-- Wizard -->
    <OnboardingWizard v-else-if="store.status" />
  </div>
</template>
