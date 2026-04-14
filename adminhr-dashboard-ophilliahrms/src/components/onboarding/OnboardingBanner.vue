<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useOnboardingStore } from '../../stores/onboarding.store'

const store = useOnboardingStore()

const nextStepLink = computed(() => {
  const key = store.nextPendingStepKey
  return key ? `/onboarding?step=${key}` : '/onboarding'
})

const remainingMinutes = computed(() => {
  // 1 min per pending step as rough estimate
  if (!store.status) return 0
  return store.status.steps.filter(s => s.status === 'PENDING').length
})

onMounted(() => {
  // Silent background fetch — no loading blocker on dashboard
  store.fetchStatus().catch(() => {})
})
</script>

<template>
  <div
    v-if="store.status && store.status.status !== 'FULLY_ONBOARDED'"
    class="mb-6 bg-gradient-to-r from-slate-900 to-slate-700 rounded-[16px] p-5 flex items-center justify-between gap-4"
  >
    <div class="min-w-0">
      <p class="font-semibold text-white text-sm leading-tight">Complete your workspace setup</p>
      <p class="text-white/50 text-xs mt-0.5 font-medium">
        ~{{ remainingMinutes }} min remaining · {{ store.completedCount }}/{{ store.status.steps.length }} steps done
      </p>
      <div class="mt-2.5 h-1.5 w-48 bg-white/20 rounded-full overflow-hidden">
        <div
          class="h-full bg-emerald-400 rounded-full transition-all duration-500"
          :style="`width: ${store.status.progress_percent}%`"
        ></div>
      </div>
    </div>
    <a
      :href="nextStepLink"
      class="flex-shrink-0 px-5 py-2.5 bg-white text-slate-900 rounded-full text-sm font-semibold hover:bg-slate-100 transition-colors whitespace-nowrap"
    >
      Continue Setup →
    </a>
  </div>
</template>
