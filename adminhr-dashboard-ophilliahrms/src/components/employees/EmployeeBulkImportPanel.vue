<script setup lang="ts">
/**
 * EmployeeBulkImportPanel — thin orchestrator for the 6-step bulk import wizard.
 *
 * Steps:
 *  1 = upload     → BulkImportUploadStep  (file + column mapping + duplicate strategy)
 *  2 = preview    → BulkImportPreviewTable (per-row validation, inline fix)
 *  3 = dry-run    → BulkImportDryRunStep   (backend dry-run results, confirm button)
 *  4 = importing  → BulkImportProgressStep (live Celery progress bar)
 *  5 = done       → BulkImportResultStep   (final stats + error table)
 *  6 = history    → ImportHistoryPanel     (audit log of all imports)
 */
import { ref, computed, onUnmounted } from 'vue'
import {
  DownloadIcon, InfoIcon, ChevronDownIcon, ChevronRightIcon,
  HistoryIcon, XCircleIcon, FlaskConicalIcon, UploadIcon, LoaderIcon,
} from 'lucide-vue-next'

import {
  downloadEmployeeTemplate,
  previewImportFile,
  uploadImportFile,
  pollImportJob,
  downloadImportErrors,
} from '../../services/employee.service'
import type { ImportPreviewResult, ImportJob } from '../../services/employee.service'

import BulkImportUploadStep    from './BulkImportUploadStep.vue'
import BulkImportPreviewTable  from './BulkImportPreviewTable.vue'
import BulkImportDryRunStep    from './BulkImportDryRunStep.vue'
import BulkImportProgressStep  from './BulkImportProgressStep.vue'
import BulkImportResultStep    from './BulkImportResultStep.vue'
import ImportHistoryPanel      from './ImportHistoryPanel.vue'

const emit = defineEmits<{ (e: 'navigate', tab: string): void }>()

// ─── Wizard step ──────────────────────────────────────────────────────────────
const step = ref<1 | 2 | 3 | 4 | 5 | 6>(1)

// ─── Shared state ─────────────────────────────────────────────────────────────
const errorMsg            = ref('')
const currentFile         = ref<File | null>(null)
const currentDuplStrat    = ref<'skip' | 'update' | 'fail'>('update')
const uploadValidOnly     = ref(false)

// Preview
const previewLoading  = ref(false)
const previewResult   = ref<ImportPreviewResult | null>(null)

// Dry run
const dryRunLoading   = ref(false)
const dryRunJob       = ref<ImportJob | null>(null)

// Import progress
const liveJob         = ref<ImportJob | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })

// ─── Derived ──────────────────────────────────────────────────────────────────
const hasPreviewErrors = computed(() =>
  (previewResult.value?.summary.errors ?? 0) > 0 ||
  (previewResult.value?.summary.cross_row_duplicates ?? 0) > 0
)

// ─── Field reference accordion (step 1 info) ──────────────────────────────────
const fieldInfoOpen = ref(false)
const requiredFields = [
  { name: 'first_name', desc: "Employee's first name" },
  { name: 'last_name',  desc: "Employee's last name" },
  { name: 'email',      desc: 'Work email (must be unique)' },
]
const optionalFields = [
  { name: 'employee_code', desc: 'Unique code' }, { name: 'phone', desc: 'Phone' },
  { name: 'gender', desc: 'male | female | other' }, { name: 'date_of_birth', desc: 'YYYY-MM-DD' },
  { name: 'date_joined', desc: 'YYYY-MM-DD (default today)' }, { name: 'employment_status', desc: 'active | inactive | terminated' },
  { name: 'designation', desc: 'Job title' }, { name: 'joining_salary', desc: 'Numeric CTC' },
  { name: 'department', desc: 'Department' }, { name: 'pan_number', desc: 'PAN (AAAAA9999A)' },
  { name: 'aadhaar_number', desc: '12-digit Aadhaar' }, { name: 'bank_account_number', desc: 'Bank account' },
]

// ─── Handlers ────────────────────────────────────────────────────────────────

function onFileSelected(file: File) {
  currentFile.value = file
  previewResult.value = null
  dryRunJob.value = null
  liveJob.value = null
  errorMsg.value = ''
}

async function onPreview(file: File, _columnMap: Record<string, string>, strategy: 'skip' | 'update' | 'fail') {
  currentFile.value = file
  currentDuplStrat.value = strategy
  previewLoading.value = true
  errorMsg.value = ''
  try {
    previewResult.value = await previewImportFile(file)
    step.value = 2
  } catch (e: any) {
    errorMsg.value = e.message ?? 'Preview failed'
  } finally {
    previewLoading.value = false
  }
}

function onCellEdit(rowIndex: number, field: string, newValue: string) {
  if (!previewResult.value?.rows[rowIndex]) return
  previewResult.value.rows[rowIndex].data[field] = newValue
  previewResult.value.rows[rowIndex].issues = previewResult.value.rows[rowIndex].issues.filter(
    i => i.field !== field
  )
  const remaining = previewResult.value.rows[rowIndex].issues
  if (remaining.length === 0) previewResult.value.rows[rowIndex].status = 'valid'
  else if (remaining.every(i => i.is_warning)) previewResult.value.rows[rowIndex].status = 'warning'
}

async function onDryRun() {
  if (!currentFile.value) return
  dryRunLoading.value = true
  errorMsg.value = ''
  try {
    const uploadResult = await uploadImportFile(currentFile.value, true, currentDuplStrat.value)
    let job = await pollImportJob(uploadResult.job_id)
    let tries = 0
    while (['pending', 'processing'].includes(job.status) && tries < 30) {
      await new Promise(r => setTimeout(r, 2000))
      job = await pollImportJob(uploadResult.job_id)
      tries++
    }
    dryRunJob.value = job
    step.value = 3
  } catch (e: any) {
    errorMsg.value = e.message ?? 'Dry run failed'
  } finally {
    dryRunLoading.value = false
  }
}

async function onImport() {
  if (!currentFile.value) return
  errorMsg.value = ''
  step.value = 4
  try {
    const uploadResult = await uploadImportFile(currentFile.value, false, currentDuplStrat.value)
    liveJob.value = await pollImportJob(uploadResult.job_id)
    let polls = 0
    pollTimer = setInterval(async () => {
      try {
        const job = await pollImportJob(uploadResult.job_id)
        liveJob.value = job
        polls++
        if (!['pending', 'processing'].includes(job.status)) {
          if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
          step.value = 5
        } else if (polls >= 150) {  // 150 × 2 s = 5 min timeout
          if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
          errorMsg.value = 'Import is taking too long — the background worker may be down. Check server logs.'
          step.value = 2
        }
      } catch { /* keep polling */ }
    }, 2000)
  } catch (e: any) {
    errorMsg.value = e.message ?? 'Import failed'
    step.value = 2
  }
}

function onClear() {
  currentFile.value = null
  previewResult.value = null
  dryRunJob.value = null
  liveJob.value = null
  errorMsg.value = ''
  step.value = 1
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

function handleDownloadErrors() {
  if (liveJob.value?.id) downloadImportErrors(liveJob.value.id)
}
</script>

<template>
  <div class="space-y-6 max-w-4xl">

    <!-- Header -->
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-900">Bulk Import Employees</h2>
        <p class="text-sm text-slate-500 mt-0.5">
          Import multiple employees at once from a CSV or Excel file.
        </p>
      </div>
      <button
        @click="step = step === 6 ? 1 : 6"
        class="flex items-center gap-2 px-4 py-2 text-xs font-medium border border-slate-200 text-slate-600 rounded-full hover:bg-slate-50 transition-colors shrink-0"
      >
        <HistoryIcon class="w-3.5 h-3.5" />
        Import History
      </button>
    </div>

    <!-- Info banner -->
    <div class="flex gap-3 bg-blue-50 border border-blue-200/60 rounded-[18px] p-4">
      <InfoIcon class="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
      <p class="text-sm text-blue-700">
        Upload a <strong>.csv</strong> or <strong>.xlsx</strong> file. Every row is validated and
        previewed before any data is written. Duplicate emails update the existing record by default.
        No login accounts are created — use the Employee Directory to send invite links.
      </p>
    </div>

    <!-- ── History Panel ── -->
    <ImportHistoryPanel v-if="step === 6" />

    <template v-else>

      <!-- ── Step 1: Download Template ── -->
      <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] font-bold shrink-0">1</span>
              <h3 class="text-sm font-semibold text-slate-700">Download Template</h3>
            </div>
            <p class="text-sm text-slate-500 mb-4 pl-7">
              Fill in your data and save as
              <code class="bg-slate-100 px-1.5 py-0.5 rounded text-xs">.csv</code> or
              <code class="bg-slate-100 px-1.5 py-0.5 rounded text-xs">.xlsx</code>.
            </p>
            <div class="pl-7">
              <button @click="downloadEmployeeTemplate()"
                class="flex items-center gap-2 px-5 py-2.5 border border-slate-200 text-slate-700 rounded-full font-medium text-sm hover:bg-slate-50 transition-all">
                <DownloadIcon class="w-4 h-4" />
                Download employee_import_template.csv
              </button>
            </div>
          </div>
        </div>

        <!-- Field reference accordion -->
        <div class="mt-5 border-t border-slate-100 pt-4">
          <button @click="fieldInfoOpen = !fieldInfoOpen"
            class="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors">
            <component :is="fieldInfoOpen ? ChevronDownIcon : ChevronRightIcon" class="w-4 h-4" />
            View column reference
          </button>
          <Transition name="accordion">
            <div v-if="fieldInfoOpen" class="mt-4 space-y-4">
              <div>
                <p class="text-xs font-semibold text-rose-600 uppercase tracking-wider mb-2">Required</p>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                  <div v-for="f in requiredFields" :key="f.name"
                       class="flex gap-2 bg-rose-50 border border-rose-100 rounded-[10px] px-3 py-2">
                    <code class="text-xs font-mono font-semibold text-rose-700 shrink-0">{{ f.name }}</code>
                    <span class="text-xs text-rose-600">{{ f.desc }}</span>
                  </div>
                </div>
              </div>
              <div>
                <p class="text-xs font-semibold text-amber-600 uppercase tracking-wider mb-2">Optional (sample)</p>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                  <div v-for="f in optionalFields" :key="f.name"
                       class="flex gap-2 bg-amber-50 border border-amber-100 rounded-[10px] px-3 py-2">
                    <code class="text-xs font-mono font-semibold text-amber-700 shrink-0">{{ f.name }}</code>
                    <span class="text-xs text-amber-700">{{ f.desc }}</span>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>

      <!-- ── Step 2: Upload ── -->
      <BulkImportUploadStep
        :loading="previewLoading"
        :error-msg="step === 1 ? errorMsg : ''"
        @file-selected="(file) => onFileSelected(file)"
        @preview="onPreview"
        @clear="onClear"
      />

      <!-- ── Step 3: Preview Table ── -->
      <div v-if="step >= 2 && previewResult"
           class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
        <div class="flex items-center gap-2 mb-5">
          <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] font-bold shrink-0">3</span>
          <h3 class="text-sm font-semibold text-slate-700">Preview &amp; Fix</h3>
        </div>

        <BulkImportPreviewTable
          :rows="previewResult.rows"
          :summary="previewResult.summary"
          :auto-corrections="previewResult.auto_corrections"
          @cell-edit="onCellEdit"
          @download-errors="handleDownloadErrors"
        />

        <!-- Upload valid only toggle -->
        <div v-if="hasPreviewErrors" class="mt-4 flex items-center gap-3">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="uploadValidOnly"
              class="w-4 h-4 rounded border-slate-300 accent-slate-900" />
            <span class="text-sm text-slate-600">Skip rows with errors, import valid rows only</span>
          </label>
        </div>

        <!-- Preview action buttons -->
        <div class="mt-5 flex items-center gap-3 flex-wrap">
          <button
            @click="onDryRun"
            :disabled="dryRunLoading || (hasPreviewErrors && !uploadValidOnly)"
            class="flex items-center gap-2 px-5 py-2.5 border border-slate-900 text-slate-900 rounded-full font-medium text-sm hover:bg-slate-50 transition-all disabled:opacity-50"
          >
            <LoaderIcon v-if="dryRunLoading" class="w-4 h-4 animate-spin" />
            <FlaskConicalIcon v-else class="w-4 h-4" />
            {{ dryRunLoading ? 'Running dry run…' : 'Dry Run (no DB writes)' }}
          </button>
          <button
            @click="onImport"
            :disabled="hasPreviewErrors && !uploadValidOnly"
            class="flex items-center gap-2 px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-50"
          >
            <UploadIcon class="w-4 h-4" />
            Import Now
          </button>
          <span v-if="hasPreviewErrors && !uploadValidOnly" class="text-xs text-slate-400">
            Fix errors or enable "skip rows" to proceed.
          </span>
        </div>

        <p v-if="errorMsg && step === 2" class="mt-3 flex items-center gap-2 text-sm text-rose-600">
          <XCircleIcon class="w-4 h-4 shrink-0" /> {{ errorMsg }}
        </p>
      </div>

      <!-- ── Step 4: Dry Run Results ── -->
      <BulkImportDryRunStep
        v-if="step >= 3 && dryRunJob"
        :job="dryRunJob"
        @confirm="onImport"
        @back="step = 2"
      />

      <!-- ── Step 5: Importing (progress) ── -->
      <BulkImportProgressStep
        v-if="step === 4"
        :job="liveJob"
      />

      <!-- ── Step 6: Done ── -->
      <BulkImportResultStep
        v-if="step === 5 && liveJob"
        :job="liveJob"
        @navigate="(tab) => emit('navigate', tab)"
        @import-another="onClear"
        @view-history="step = 6"
        @download-errors="handleDownloadErrors"
      />

    </template>

  </div>
</template>

<style scoped>
.accordion-enter-active, .accordion-leave-active { transition: all 0.25s ease; overflow: hidden; }
.accordion-enter-from, .accordion-leave-to { opacity: 0; max-height: 0; }
.accordion-enter-to, .accordion-leave-from { opacity: 1; max-height: 2000px; }
</style>
