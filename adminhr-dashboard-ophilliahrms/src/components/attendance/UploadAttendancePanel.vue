<script setup lang="ts">
import { ref } from 'vue'
import { DownloadIcon, UploadIcon } from 'lucide-vue-next'
import { downloadAttendanceTemplate, uploadAttendanceCsv } from '../../services/attendance.service'
import type { UploadResult } from '../../services/attendance.service'

const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const downloading = ref(false)
const result = ref<UploadResult | null>(null)
const errorMsg = ref('')

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  result.value = null
  errorMsg.value = ''
}

async function handleDownload() {
  downloading.value = true
  try { await downloadAttendanceTemplate() }
  catch (e: any) { errorMsg.value = e.message }
  finally { downloading.value = false }
}

async function handleUpload() {
  if (!selectedFile.value) return
  uploading.value = true; errorMsg.value = ''; result.value = null
  try {
    result.value = await uploadAttendanceCsv(selectedFile.value)
  } catch (e: any) { errorMsg.value = e.message }
  finally { uploading.value = false }
}
</script>

<template>
  <div class="space-y-6 max-w-2xl">
    <div>
      <h2 class="text-xl font-bold text-slate-900">Upload Attendance</h2>
      <p class="text-sm text-slate-500 mt-0.5">Bulk-import attendance records via CSV file</p>
    </div>

    <!-- Template download -->
    <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
      <h3 class="text-sm font-semibold text-slate-700 mb-2">Step 1 — Download Template</h3>
      <p class="text-sm text-slate-500 mb-4">Download the CSV template and fill in your attendance data. Required columns: <code class="bg-slate-100 px-1.5 py-0.5 rounded text-xs">employee_id, date, status, clock_in, clock_out, notes</code></p>
      <button @click="handleDownload" :disabled="downloading" class="flex items-center gap-2 px-6 py-2.5 border border-slate-200 text-slate-700 rounded-full font-medium text-sm hover:bg-slate-50 transition-all disabled:opacity-60">
        <DownloadIcon class="w-4 h-4" /> {{ downloading ? 'Downloading…' : 'Download Template' }}
      </button>
    </div>

    <!-- File upload -->
    <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
      <h3 class="text-sm font-semibold text-slate-700 mb-4">Step 2 — Upload CSV</h3>
      <label class="block w-full cursor-pointer">
        <div :class="['border-2 border-dashed rounded-[18px] p-8 text-center transition-colors', selectedFile ? 'border-slate-300 bg-slate-50' : 'border-slate-200 hover:border-slate-300']">
          <UploadIcon class="w-8 h-8 text-slate-300 mx-auto mb-3" />
          <p class="text-sm font-medium text-slate-600">{{ selectedFile ? selectedFile.name : 'Click to browse or drop a CSV file' }}</p>
          <p class="text-xs text-slate-400 mt-1">{{ selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : '.csv files only' }}</p>
        </div>
        <input type="file" accept=".csv" class="hidden" @change="onFileChange" />
      </label>

      <div class="mt-4 flex items-center gap-3">
        <button
          @click="handleUpload"
          :disabled="!selectedFile || uploading"
          class="flex items-center gap-2 px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60"
        >
          <UploadIcon class="w-4 h-4" /> {{ uploading ? 'Uploading…' : 'Upload & Import' }}
        </button>
        <button v-if="selectedFile" @click="selectedFile = null; result = null" class="px-4 py-2.5 border border-slate-200 text-slate-600 rounded-full text-sm hover:bg-slate-50 transition-colors">Clear</button>
      </div>

      <p v-if="errorMsg" class="mt-3 text-sm text-rose-600">{{ errorMsg }}</p>
    </div>

    <!-- Results -->
    <div v-if="result" class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
      <h3 class="text-sm font-semibold text-slate-700 mb-4">Import Results</h3>
      <div class="grid grid-cols-3 gap-4 mb-5">
        <div class="text-center p-3 bg-slate-50 rounded-[14px]">
          <p class="text-2xl font-bold text-slate-900">{{ result.total }}</p>
          <p class="text-xs text-slate-500 mt-0.5">Total Rows</p>
        </div>
        <div class="text-center p-3 bg-emerald-50 rounded-[14px]">
          <p class="text-2xl font-bold text-emerald-700">{{ result.succeeded }}</p>
          <p class="text-xs text-emerald-600 mt-0.5">Imported</p>
        </div>
        <div class="text-center p-3 bg-rose-50 rounded-[14px]">
          <p class="text-2xl font-bold text-rose-600">{{ result.failed }}</p>
          <p class="text-xs text-rose-500 mt-0.5">Failed</p>
        </div>
      </div>
      <div v-if="result.errors.length > 0" class="space-y-1">
        <p class="text-xs font-semibold text-slate-500 mb-2">Errors:</p>
        <div v-for="err in result.errors" :key="err.row" class="flex gap-3 text-xs py-1.5 border-b border-slate-100">
          <span class="font-medium text-slate-500 w-16 shrink-0">Row {{ err.row }}</span>
          <span class="text-rose-600">{{ err.error }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
