<script setup lang="ts">
import {
  CheckCircle2Icon, AlertTriangleIcon, DownloadIcon, UsersIcon, ClockIcon,
} from 'lucide-vue-next'
import type { ImportJob } from '../../services/employee.service'

const props = defineProps<{ job: ImportJob }>()
const emit = defineEmits<{
  (e: 'navigate', tab: string): void
  (e: 'import-another'): void
  (e: 'view-history'): void
  (e: 'download-errors'): void
}>()
</script>

<template>
  <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
    <div class="flex items-center gap-2 mb-5">
      <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-600 text-white shrink-0">
        <CheckCircle2Icon class="w-3 h-3" />
      </span>
      <h3 class="text-sm font-semibold text-slate-700">Import Complete</h3>
    </div>

    <!-- Stats grid -->
    <div class="grid grid-cols-4 gap-3 mb-5">
      <div class="text-center p-4 bg-slate-50 rounded-[16px]">
        <p class="text-3xl font-bold text-slate-900">{{ job.total_rows }}</p>
        <p class="text-xs text-slate-500 mt-1">Total</p>
      </div>
      <div class="text-center p-4 bg-emerald-50 rounded-[16px]">
        <p class="text-3xl font-bold text-emerald-700">{{ job.succeeded_rows }}</p>
        <p class="text-xs text-emerald-600 mt-1">Imported</p>
      </div>
      <div class="text-center p-4 bg-amber-50 rounded-[16px]">
        <p class="text-3xl font-bold text-amber-600">{{ job.skipped_rows }}</p>
        <p class="text-xs text-amber-500 mt-1">Skipped</p>
      </div>
      <div class="text-center p-4 bg-rose-50 rounded-[16px]">
        <p class="text-3xl font-bold text-rose-600">{{ job.failed_rows }}</p>
        <p class="text-xs text-rose-500 mt-1">Failed</p>
      </div>
    </div>

    <!-- Success banner -->
    <div v-if="job.failed_rows === 0"
         class="flex items-center justify-between gap-3 bg-emerald-50 border border-emerald-200 rounded-[14px] px-4 py-3 mb-4">
      <div class="flex items-center gap-2">
        <CheckCircle2Icon class="w-4 h-4 text-emerald-600 shrink-0" />
        <p class="text-sm text-emerald-700 font-medium">All records imported! Go to the directory to send invite links.</p>
      </div>
      <button @click="emit('navigate', 'employees')"
        class="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-700 text-white rounded-full text-xs font-semibold hover:bg-emerald-800 transition-colors shrink-0">
        <UsersIcon class="w-3.5 h-3.5" /> Directory → Send Invites
      </button>
    </div>

    <!-- Partial failure banner -->
    <div v-else class="flex items-center justify-between gap-3 bg-amber-50 border border-amber-200 rounded-[14px] px-4 py-3 mb-4">
      <div class="flex items-center gap-2">
        <AlertTriangleIcon class="w-4 h-4 text-amber-500 shrink-0" />
        <p class="text-sm text-amber-700 font-medium">
          {{ job.failed_rows }} row{{ job.failed_rows !== 1 ? 's' : '' }} failed.
          Download the error report and re-import those rows.
        </p>
      </div>
    </div>

    <!-- Error log table (first 50 rows) -->
    <div v-if="(job.error_log ?? []).length > 0" class="space-y-3 mb-5">
      <div class="flex items-center justify-between">
        <p class="text-sm font-semibold text-slate-600">{{ job.error_log!.length }} issues</p>
        <button @click="emit('download-errors')"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-slate-200 text-slate-600 rounded-full hover:bg-slate-50 transition-colors">
          <DownloadIcon class="w-3.5 h-3.5" /> Download Error Report
        </button>
      </div>
      <div class="rounded-[14px] border border-slate-200 overflow-hidden">
        <div class="grid grid-cols-[56px_100px_1fr_1fr] text-xs font-semibold text-slate-500 bg-slate-50 px-4 py-2 border-b border-slate-200">
          <span>Row</span><span>Field</span><span>Error</span><span>Fix</span>
        </div>
        <div
          v-for="(err, i) in (job.error_log ?? []).slice(0, 50)" :key="i"
          class="grid grid-cols-[56px_100px_1fr_1fr] text-xs py-2.5 px-4 border-b border-slate-100 last:border-0 hover:bg-slate-50/60"
        >
          <span class="font-mono font-semibold text-slate-500">{{ (err.row ?? 0) + 2 }}</span>
          <span class="text-slate-500">{{ err.field ?? '—' }}</span>
          <span class="text-rose-600">{{ err.error ?? '' }}</span>
          <span class="text-slate-400 italic">{{ err.suggested_fix ?? '' }}</span>
        </div>
        <div v-if="(job.error_log?.length ?? 0) > 50"
             class="px-4 py-2 text-xs text-slate-400 text-center">
          … and {{ (job.error_log?.length ?? 0) - 50 }} more. Download the full report.
        </div>
      </div>
    </div>

    <!-- Footer actions -->
    <div class="flex items-center gap-3 flex-wrap">
      <button @click="emit('import-another')"
        class="px-4 py-2.5 border border-slate-200 text-slate-600 rounded-full text-sm hover:bg-slate-50 transition-colors">
        Import Another File
      </button>
      <button @click="emit('view-history')"
        class="flex items-center gap-2 px-4 py-2.5 border border-slate-200 text-slate-600 rounded-full text-sm hover:bg-slate-50 transition-colors">
        <ClockIcon class="w-3.5 h-3.5" /> View Import History
      </button>
    </div>
  </div>
</template>
