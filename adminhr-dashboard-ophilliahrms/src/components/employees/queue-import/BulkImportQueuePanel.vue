<script setup lang="ts">
import { ref } from 'vue'
import { UploadCloudIcon, FileSpreadsheetIcon, XCircleIcon, PlayIcon, LoaderIcon } from 'lucide-vue-next'
import { previewImportFile } from '../../../services/employee.service'
import type { ImportPreviewResult } from '../../../services/employee.service'
import { listDepartments } from '../../../services/department.service'
import type { Department } from '../../../services/department.service'
import BulkImportQueueModal from './BulkImportQueueModal.vue'

// ─── State ────────────────────────────────────────────────────────────────────
const file        = ref<File | null>(null)
const loading     = ref(false)
const errorMsg    = ref('')
const preview     = ref<ImportPreviewResult | null>(null)
const departments = ref<Department[]>([])
const modalOpen   = ref(false)
const dragging    = ref(false)

// ─── File handling ────────────────────────────────────────────────────────────
function onDrop(e: DragEvent) {
  dragging.value = false
  const f = e.dataTransfer?.files[0]
  if (f) selectFile(f)
}

function onPick(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) selectFile(f)
}

function selectFile(f: File) {
  file.value = f
  preview.value = null
  errorMsg.value = ''
}

function clearFile() {
  file.value = null
  preview.value = null
  errorMsg.value = ''
}

async function runPreview() {
  if (!file.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    const [p, depts] = await Promise.all([
      previewImportFile(file.value),
      listDepartments().catch(() => [] as Department[]),
    ])
    preview.value = p
    departments.value = depts
  } catch (e: any) {
    errorMsg.value = e.message ?? 'Failed to parse file'
  } finally {
    loading.value = false
  }
}

function startQueue() {
  if (!preview.value?.rows.length) return
  modalOpen.value = true
}

function onModalClose() {
  modalOpen.value = false
  // reset after import session
  file.value = null
  preview.value = null
}
</script>

<template>
  <div class="space-y-6 max-w-2xl">

    <!-- Header -->
    <div>
      <h2 class="text-xl font-bold text-slate-900">Queue-Mode Bulk Import</h2>
      <p class="text-sm text-slate-500 mt-0.5">
        Review and submit employees one-by-one. Each employee is sanitized, corrected, and confirmed before being created.
      </p>
    </div>

    <!-- Drop zone -->
    <div
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
      :class="[
        'relative border-2 border-dashed rounded-[20px] p-10 text-center transition-all',
        dragging ? 'border-slate-500 bg-slate-50' : 'border-slate-200 bg-white/60',
        file ? 'border-emerald-300 bg-emerald-50/40' : '',
      ]"
    >
      <input
        type="file"
        accept=".csv,.xlsx"
        class="absolute inset-0 opacity-0 cursor-pointer"
        @change="onPick"
      />

      <div v-if="!file" class="space-y-2">
        <UploadCloudIcon class="w-10 h-10 text-slate-300 mx-auto" />
        <p class="text-sm font-medium text-slate-600">Drop a CSV or XLSX file here</p>
        <p class="text-xs text-slate-400">or click to browse</p>
      </div>

      <div v-else class="flex items-center justify-center gap-3">
        <FileSpreadsheetIcon class="w-8 h-8 text-emerald-600 shrink-0" />
        <div class="text-left">
          <p class="text-sm font-semibold text-slate-800">{{ file.name }}</p>
          <p class="text-xs text-slate-400">{{ (file.size / 1024).toFixed(1) }} KB</p>
        </div>
        <button
          @click.stop="clearFile"
          class="ml-2 text-slate-400 hover:text-slate-600 transition-colors"
        >
          <XCircleIcon class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- Parse button -->
    <button
      v-if="file && !preview"
      @click="runPreview"
      :disabled="loading"
      class="flex items-center gap-2 px-6 py-2.5 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 disabled:opacity-50 transition-all"
    >
      <LoaderIcon v-if="loading" class="w-4 h-4 animate-spin" />
      <FileSpreadsheetIcon v-else class="w-4 h-4" />
      {{ loading ? 'Parsing file…' : 'Parse & Validate' }}
    </button>

    <!-- Error -->
    <p v-if="errorMsg" class="flex items-center gap-2 text-sm text-rose-600">
      <XCircleIcon class="w-4 h-4 shrink-0" /> {{ errorMsg }}
    </p>

    <!-- Preview summary + start -->
    <div
      v-if="preview"
      class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[20px] p-5 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)] space-y-4"
    >
      <h3 class="text-sm font-semibold text-slate-700">File Summary</h3>
      <div class="grid grid-cols-4 gap-3">
        <div class="text-center p-3 bg-slate-50 rounded-[14px]">
          <p class="text-2xl font-bold text-slate-900">{{ preview.rows.length }}</p>
          <p class="text-xs text-slate-500 mt-0.5">Total</p>
        </div>
        <div class="text-center p-3 bg-emerald-50 rounded-[14px]">
          <p class="text-2xl font-bold text-emerald-700">
            {{ preview.rows.filter(r => r.status === 'valid').length }}
          </p>
          <p class="text-xs text-emerald-600 mt-0.5">Clean</p>
        </div>
        <div class="text-center p-3 bg-amber-50 rounded-[14px]">
          <p class="text-2xl font-bold text-amber-700">
            {{ preview.rows.filter(r => r.status === 'warning').length }}
          </p>
          <p class="text-xs text-amber-600 mt-0.5">Warnings</p>
        </div>
        <div class="text-center p-3 bg-rose-50 rounded-[14px]">
          <p class="text-2xl font-bold text-rose-700">
            {{ preview.rows.filter(r => r.status === 'error' || r.status === 'cross_row').length }}
          </p>
          <p class="text-xs text-rose-600 mt-0.5">Errors</p>
        </div>
      </div>

      <div v-if="preview.summary.auto_corrections > 0" class="text-xs text-slate-500">
        ✓ {{ preview.summary.auto_corrections }} fields were auto-corrected (dates, PAN, Aadhaar spaces, etc.)
      </div>

      <button
        @click="startQueue"
        class="flex items-center gap-2 px-6 py-3 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-all"
      >
        <PlayIcon class="w-4 h-4" />
        Start Processing Queue ({{ preview.rows.length }} employees)
      </button>
    </div>

    <!-- The modal (teleported to body) -->
    <Teleport to="body">
      <BulkImportQueueModal
        v-if="modalOpen && preview"
        :rows="preview.rows"
        :departments="departments"
        @close="onModalClose"
      />
    </Teleport>
  </div>
</template>
