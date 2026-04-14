<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  DownloadIcon, CheckCircle2Icon, XCircleIcon, AlertTriangleIcon,
  LoaderIcon, ClockIcon, RefreshCwIcon,
} from 'lucide-vue-next'
import { getImportHistory, downloadImportErrors } from '../../services/employee.service'
import type { ImportJob } from '../../services/employee.service'

const jobs   = ref<ImportJob[]>([])
const loading = ref(true)
const error   = ref('')

async function loadHistory() {
  loading.value = true
  error.value = ''
  try {
    jobs.value = await getImportHistory(50)
  } catch (e: any) {
    error.value = e.message ?? 'Failed to load history'
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)

function statusStyle(status: string): { dot: string; label: string; bg: string } {
  switch (status) {
    case 'completed':  return { dot: 'bg-emerald-400', label: 'Completed',  bg: 'bg-emerald-50 text-emerald-700' }
    case 'failed':     return { dot: 'bg-red-500',     label: 'Failed',     bg: 'bg-red-50 text-red-700' }
    case 'processing': return { dot: 'bg-blue-400 animate-pulse', label: 'Processing', bg: 'bg-blue-50 text-blue-700' }
    case 'pending':    return { dot: 'bg-amber-400',   label: 'Pending',    bg: 'bg-amber-50 text-amber-700' }
    case 'dry_run':    return { dot: 'bg-violet-400',  label: 'Dry Run',    bg: 'bg-violet-50 text-violet-700' }
    default:           return { dot: 'bg-slate-400',   label: status,       bg: 'bg-slate-50 text-slate-600' }
  }
}

function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return iso }
}
</script>

<template>
  <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
    <div class="flex items-center justify-between mb-5">
      <div class="flex items-center gap-2">
        <ClockIcon class="w-4 h-4 text-slate-400" />
        <h3 class="text-sm font-semibold text-slate-700">Import History</h3>
        <span class="text-xs text-slate-400">(last 50 imports)</span>
      </div>
      <button @click="loadHistory"
        :disabled="loading"
        class="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-slate-200 text-slate-600 rounded-full hover:bg-slate-50 transition-colors disabled:opacity-50">
        <RefreshCwIcon class="w-3 h-3" :class="loading ? 'animate-spin' : ''" />
        Refresh
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12 text-slate-400">
      <LoaderIcon class="w-5 h-5 animate-spin mr-2" />
      Loading history…
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center gap-2 text-sm text-rose-600 py-6">
      <XCircleIcon class="w-4 h-4 shrink-0" /> {{ error }}
    </div>

    <!-- Empty -->
    <div v-else-if="jobs.length === 0" class="text-center py-12 text-slate-400">
      <ClockIcon class="w-10 h-10 mx-auto mb-3 text-slate-200" />
      <p class="text-sm">No imports yet.</p>
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto rounded-[16px] border border-slate-200/60">
      <table class="w-full text-xs text-left">
        <thead class="border-b border-slate-200/60 bg-white/40">
          <tr>
            <th class="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Date</th>
            <th class="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">File</th>
            <th class="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider text-center">Total</th>
            <th class="px-4 py-3 text-xs font-semibold text-emerald-600 uppercase tracking-wider text-center">✓ OK</th>
            <th class="px-4 py-3 text-xs font-semibold text-amber-600 uppercase tracking-wider text-center">↷ Skip</th>
            <th class="px-4 py-3 text-xs font-semibold text-rose-600 uppercase tracking-wider text-center">✗ Fail</th>
            <th class="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
            <th class="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Version</th>
            <th class="px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="job in jobs"
            :key="job.id"
            class="border-b border-slate-100/60 hover:bg-white/60 transition-colors"
          >
            <td class="px-4 py-3 text-slate-500 whitespace-nowrap">{{ fmtDate(job.created_at) }}</td>
            <td class="px-4 py-3 text-slate-700 max-w-[180px] truncate" :title="job.file_name">
              {{ job.file_name }}
            </td>
            <td class="px-4 py-3 text-center font-medium text-slate-700">{{ job.total_rows }}</td>
            <td class="px-4 py-3 text-center font-medium text-emerald-700">{{ job.succeeded_rows }}</td>
            <td class="px-4 py-3 text-center font-medium text-amber-600">{{ job.skipped_rows }}</td>
            <td class="px-4 py-3 text-center font-medium text-rose-600">{{ job.failed_rows }}</td>
            <td class="px-4 py-3">
              <span :class="['inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium', statusStyle(job.status).bg]">
                <span :class="['w-1.5 h-1.5 rounded-full', statusStyle(job.status).dot]" />
                {{ statusStyle(job.status).label }}
              </span>
            </td>
            <td class="px-4 py-3 text-slate-400 font-mono">{{ job.schema_version }}</td>
            <td class="px-4 py-3 text-right">
              <button
                v-if="job.failed_rows > 0 || job.status === 'failed'"
                @click="downloadImportErrors(job.id)"
                class="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-slate-200 text-slate-600 rounded-full hover:bg-slate-50 transition-colors ml-auto"
                title="Download error CSV"
              >
                <DownloadIcon class="w-3 h-3" />
                Errors
              </button>
              <span v-else class="text-slate-300 text-xs">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
