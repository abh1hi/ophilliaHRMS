<script setup lang="ts">
import { UploadIcon, ChevronLeftIcon } from 'lucide-vue-next'
import type { ImportJob } from '../../services/employee.service'

defineProps<{ job: ImportJob }>()
const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'back'): void
}>()
</script>

<template>
  <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
    <div class="flex items-center justify-between gap-2 mb-5">
      <div class="flex items-center gap-2">
        <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] font-bold shrink-0">4</span>
        <h3 class="text-sm font-semibold text-slate-700">
          Dry Run Results
          <span class="text-slate-400 font-normal text-xs ml-1">(no data written)</span>
        </h3>
      </div>
      <button @click="emit('back')"
        class="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1">
        <ChevronLeftIcon class="w-3.5 h-3.5" /> Back
      </button>
    </div>

    <div class="grid grid-cols-4 gap-3 mb-5">
      <div class="text-center p-4 bg-slate-50 rounded-[16px]">
        <p class="text-2xl font-bold text-slate-900">{{ job.total_rows }}</p>
        <p class="text-xs text-slate-500 mt-1">Total</p>
      </div>
      <div class="text-center p-4 bg-emerald-50 rounded-[16px]">
        <p class="text-2xl font-bold text-emerald-700">{{ job.succeeded_rows }}</p>
        <p class="text-xs text-emerald-600 mt-1">Would Import</p>
      </div>
      <div class="text-center p-4 bg-amber-50 rounded-[16px]">
        <p class="text-2xl font-bold text-amber-600">{{ job.skipped_rows }}</p>
        <p class="text-xs text-amber-500 mt-1">Would Skip</p>
      </div>
      <div class="text-center p-4 bg-rose-50 rounded-[16px]">
        <p class="text-2xl font-bold text-rose-600">{{ job.failed_rows }}</p>
        <p class="text-xs text-rose-500 mt-1">Would Fail</p>
      </div>
    </div>

    <div class="flex items-center gap-3">
      <button @click="emit('confirm')"
        class="flex items-center gap-2 px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all">
        <UploadIcon class="w-4 h-4" />
        Confirm Import
      </button>
      <button @click="emit('back')"
        class="px-4 py-2.5 border border-slate-200 text-slate-600 rounded-full text-sm hover:bg-slate-50 transition-colors">
        Back to Preview
      </button>
    </div>
  </div>
</template>
