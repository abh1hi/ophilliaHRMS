<script setup lang="ts">
import { computed } from 'vue'
import { LoaderIcon } from 'lucide-vue-next'
import type { ImportJob } from '../../services/employee.service'

const props = defineProps<{ job: ImportJob | null }>()

const progressPct = computed(() => {
  if (!props.job || props.job.total_rows === 0) return 0
  return Math.round(
    ((props.job.succeeded_rows + props.job.failed_rows) / props.job.total_rows) * 100
  )
})
</script>

<template>
  <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
    <div class="flex items-center gap-2 mb-5">
      <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] font-bold shrink-0">5</span>
      <h3 class="text-sm font-semibold text-slate-700">Importing…</h3>
    </div>

    <div class="space-y-4">
      <div class="flex justify-between text-sm text-slate-600">
        <span>
          <LoaderIcon class="inline w-4 h-4 mr-1.5 animate-spin text-slate-400" />
          Processing
          {{ job ? (job.succeeded_rows + job.failed_rows) : 0 }} /
          {{ job?.total_rows ?? '…' }} rows
        </span>
        <span>{{ progressPct }}%</span>
      </div>

      <div class="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          class="h-full bg-slate-700 rounded-full transition-all duration-500"
          :style="{ width: `${progressPct}%` }"
        />
      </div>

      <div v-if="job" class="flex gap-4 text-xs text-slate-500">
        <span class="text-emerald-600">✓ {{ job.succeeded_rows }} imported</span>
        <span class="text-amber-600">↷ {{ job.skipped_rows }} skipped</span>
        <span class="text-rose-600">✗ {{ job.failed_rows }} failed</span>
      </div>
    </div>
  </div>
</template>
