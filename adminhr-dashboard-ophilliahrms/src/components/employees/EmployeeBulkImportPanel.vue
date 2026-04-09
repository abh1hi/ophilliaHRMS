<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  DownloadIcon, UploadIcon, FileSpreadsheetIcon, CheckCircle2Icon,
  XCircleIcon, AlertTriangleIcon, InfoIcon, ChevronDownIcon, ChevronRightIcon,
  ArrowRightIcon, RefreshCwIcon, UsersIcon,
} from 'lucide-vue-next'
import {
  downloadEmployeeTemplate,
  uploadEmployeeCsv,
  parseCsvHeaders,
  EMPLOYEE_SYSTEM_FIELDS,
} from '../../services/employee.service'
import type { EmployeeImportResult, ImportProgress } from '../../services/employee.service'

const emit = defineEmits<{ (e: 'navigate', tab: string): void }>()

// ─── State ────────────────────────────────────────────────────────────────────
const selectedFile   = ref<File | null>(null)
const uploading      = ref(false)
const result         = ref<EmployeeImportResult | null>(null)
const errorMsg       = ref('')
const dragOver       = ref(false)
const fieldInfoOpen  = ref(false)
const progressDone     = ref(0)
const progressTotal    = ref(0)

// Column mapping
const csvHeaders        = ref<string[]>([])          // headers detected from the uploaded CSV
const columnMap         = ref<Record<string, string>>({}) // systemField → csvHeader
const mappingOpen       = ref(false)
const mappingConfirmed  = ref(false)

// ─── Field reference ──────────────────────────────────────────────────────────
const requiredFields = [
  { name: 'first_name', desc: "Employee's first name"              },
  { name: 'last_name',  desc: "Employee's last name"               },
  { name: 'email',      desc: 'Work email address (must be unique)' },
]

const optionalFields = [
  { name: 'employee_code',     desc: 'Unique employee code / ID'                            },
  { name: 'phone',             desc: 'Primary contact number'                               },
  { name: 'phone_2',           desc: 'Secondary contact number'                             },
  { name: 'gender',            desc: 'male | female | other (case-insensitive)'             },
  { name: 'date_of_birth',     desc: 'YYYY-MM-DD format'                                   },
  { name: 'date_joined',       desc: 'YYYY-MM-DD – defaults to today if blank'              },
  { name: 'employment_status', desc: 'active | inactive | terminated (defaults to active)'  },
  { name: 'designation',       desc: 'Designation / job title'                              },
  { name: 'joining_salary',    desc: 'Numeric monthly CTC'                                  },
  { name: 'role',              desc: 'System role (employee | manager etc.)'                },
  { name: 'project',           desc: 'Project assignment'                                   },
  { name: 'department',        desc: 'Department name (informational)'                      },
  { name: 'bank_account_number', desc: 'Bank account number'                                },
  { name: 'bank_name',         desc: 'Bank name'                                            },
  { name: 'bank_branch',       desc: 'Bank branch'                                          },
  { name: 'ifsc_code',         desc: 'Bank IFSC code'                                       },
  { name: 'pan_number',        desc: 'PAN card number (format: AAAAA9999A)'                 },
  { name: 'aadhaar_number',    desc: 'Exactly 12-digit Aadhaar number'                      },
  { name: 'uan_number',        desc: 'Universal Account Number (PF)'                        },
  { name: 'esi_number',        desc: 'ESI card number'                                      },
  { name: 'driving_license_number', desc: 'Driving license number'                          },
  { name: 'emergency_contact_name',     desc: 'Emergency contact person'                    },
  { name: 'emergency_contact_number',   desc: 'Emergency contact phone'                     },
  { name: 'emergency_contact_relation', desc: 'Relationship (e.g. Spouse, Parent)'          },
  { name: 'highest_qualification', desc: 'Highest education qualification'                  },
  { name: 'institute_name',    desc: 'Institution / university name'                        },
  { name: 'year_of_passing',   desc: '4-digit year'                                         },
  { name: 'percentage',        desc: 'Marks percentage'                                     },
  { name: 'last_firm_name',    desc: 'Previous employer name'                               },
  { name: 'last_designation',  desc: 'Previous designation'                                 },
  { name: 'years_of_experience', desc: 'Total years of experience'                          },
  { name: 'last_drawn_salary', desc: 'Previous CTC (numeric)'                               },
  { name: 'reason_to_quit',    desc: 'Reason for leaving previous job'                      },
  { name: 'health_issues',     desc: 'Known health conditions'                              },
  { name: 'allergies',         desc: 'Known allergies'                                      },
  { name: 'referred_by',       desc: 'Referral source or person'                            },
]

// ─── Derived ──────────────────────────────────────────────────────────────────
const successRate = computed(() => {
  if (!result.value || result.value.total === 0) return 0
  return Math.round((result.value.succeeded / result.value.total) * 100)
})

const unmappedRequired = computed(() =>
  requiredFields.filter(f => {
    const mapped = columnMap.value[f.name]
    return !mapped || !csvHeaders.value.includes(mapped)
  })
)

// Rows for mapping UI — only system fields that have a CSV column candidate
const mappingRows = computed(() =>
  EMPLOYEE_SYSTEM_FIELDS.map(field => ({
    field,
    mapped: columnMap.value[field] ?? '',
  }))
)

// ─── File handling ─────────────────────────────────────────────────────────────
function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  setFile(input.files?.[0] ?? null)
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file && (file.name.endsWith('.csv') || file.type === 'text/csv')) {
    setFile(file)
  } else if (file) {
    errorMsg.value = 'Only CSV files are supported.'
  }
}

async function setFile(file: File | null) {
  selectedFile.value = file
  result.value = null
  errorMsg.value = ''
  mappingConfirmed.value = false
  mappingOpen.value = false
  csvHeaders.value = []
  columnMap.value = {}

  if (!file) return

  // Parse headers and auto-map
  const headers = await parseCsvHeaders(file)
  csvHeaders.value = headers
  autoMap(headers)
}

function autoMap(headers: string[]) {
  const map: Record<string, string> = {}
  const headerSet = new Set(headers)
  for (const field of EMPLOYEE_SYSTEM_FIELDS) {
    // Exact match
    if (headerSet.has(field)) { map[field] = field; continue }
    // Fuzzy: try replacing spaces/hyphens with underscores
    const fuzzy = headers.find(h => h.replace(/[-\s]/g, '_') === field)
    if (fuzzy) map[field] = fuzzy
  }
  columnMap.value = map
}

function resetMapping() {
  if (csvHeaders.value.length) autoMap(csvHeaders.value)
}

// ─── Import ───────────────────────────────────────────────────────────────────
function handleDownload() {
  downloadEmployeeTemplate()
}

async function handleUpload() {
  if (!selectedFile.value) return
  uploading.value = true
  errorMsg.value = ''
  result.value = null
  progressDone.value = 0
  progressTotal.value = 0

  // Only pass the map if user actually opened the mapping UI
  const map = mappingOpen.value ? { ...columnMap.value } : undefined

  try {
    result.value = await uploadEmployeeCsv(selectedFile.value, ({ done, total }: ImportProgress) => {
      progressDone.value = done
      progressTotal.value = total
    }, map)
  } catch (e: any) {
    errorMsg.value = e.message
  } finally {
    uploading.value = false
  }
}

function clearFile() {
  selectedFile.value = null
  result.value = null
  errorMsg.value = ''
  csvHeaders.value = []
  columnMap.value = {}
  mappingOpen.value = false
  mappingConfirmed.value = false
}
</script>

<template>
  <div class="space-y-6 max-w-3xl">

    <!-- Header -->
    <div>
      <h2 class="text-xl font-bold text-slate-900">Bulk Import Employees</h2>
      <p class="text-sm text-slate-500 mt-0.5">
        Import multiple employee records at once from a CSV file. Use this during initial setup,
        data migration, or bulk updates.
      </p>
    </div>

    <!-- Info banner -->
    <div class="flex gap-3 bg-blue-50 border border-blue-200/60 rounded-[18px] p-4">
      <InfoIcon class="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
      <p class="text-sm text-blue-700">
        Download the template, fill in employee data, then upload. Each row becomes one <strong>employee HR record only</strong> —
        no login accounts are created. Go to the <strong>Employee Directory</strong> after import to send portal invite links.
        Duplicate emails update the existing record. Use <strong>Map Columns</strong> if your CSV uses different header names.
      </p>
    </div>

    <!-- ── Step 1: Download Template ── -->
    <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-1">
            <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] font-bold shrink-0">1</span>
            <h3 class="text-sm font-semibold text-slate-700">Download Template</h3>
          </div>
          <p class="text-sm text-slate-500 mb-4 pl-7">
            Download the CSV template, fill in your data, and save as
            <code class="bg-slate-100 px-1.5 py-0.5 rounded text-xs">.csv</code> (UTF-8 encoding).
          </p>
          <div class="pl-7">
            <button
              @click="handleDownload"
              class="flex items-center gap-2 px-5 py-2.5 border border-slate-200 text-slate-700 rounded-full font-medium text-sm hover:bg-slate-50 transition-all"
            >
              <DownloadIcon class="w-4 h-4" />
              Download employee_import_template.csv
            </button>
          </div>
        </div>
        <FileSpreadsheetIcon class="w-10 h-10 text-slate-200 shrink-0" />
      </div>

      <!-- Field reference accordion -->
      <div class="mt-5 border-t border-slate-100 pt-4">
        <button
          @click="fieldInfoOpen = !fieldInfoOpen"
          class="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
        >
          <component :is="fieldInfoOpen ? ChevronDownIcon : ChevronRightIcon" class="w-4 h-4" />
          View column reference
        </button>

        <Transition name="accordion">
          <div v-if="fieldInfoOpen" class="mt-4 space-y-4">
            <div>
              <p class="text-xs font-semibold text-rose-600 uppercase tracking-wider mb-2">Required columns</p>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                <div
                  v-for="f in requiredFields" :key="f.name"
                  class="flex gap-2 bg-rose-50 border border-rose-100 rounded-[10px] px-3 py-2"
                >
                  <code class="text-xs font-mono font-semibold text-rose-700 shrink-0">{{ f.name }}</code>
                  <span class="text-xs text-rose-600">{{ f.desc }}</span>
                </div>
              </div>
            </div>
            <div>
              <p class="text-xs font-semibold text-amber-600 uppercase tracking-wider mb-2">Optional columns</p>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                <div
                  v-for="f in optionalFields" :key="f.name"
                  class="flex gap-2 bg-amber-50 border border-amber-100 rounded-[10px] px-3 py-2"
                >
                  <code class="text-xs font-mono font-semibold text-amber-700 shrink-0">{{ f.name }}</code>
                  <span class="text-xs text-amber-700">{{ f.desc }}</span>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- ── Step 2: Upload CSV ── -->
    <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
      <div class="flex items-center gap-2 mb-4">
        <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] font-bold shrink-0">2</span>
        <h3 class="text-sm font-semibold text-slate-700">Upload CSV File</h3>
      </div>

      <!-- Drop zone -->
      <label class="block w-full cursor-pointer">
        <div
          :class="[
            'border-2 border-dashed rounded-[18px] p-10 text-center transition-all',
            dragOver     ? 'border-slate-400 bg-slate-50 scale-[1.01]' :
            selectedFile ? 'border-emerald-300 bg-emerald-50/50'        :
                           'border-slate-200 hover:border-slate-300',
          ]"
          @dragover.prevent="dragOver = true"
          @dragleave.prevent="dragOver = false"
          @drop.prevent="onDrop"
        >
          <UploadIcon :class="['w-9 h-9 mx-auto mb-3', selectedFile ? 'text-emerald-400' : 'text-slate-300']" />
          <p class="text-sm font-medium text-slate-600">
            {{ selectedFile ? selectedFile.name : 'Click to browse or drag & drop a CSV file' }}
          </p>
          <p class="text-xs text-slate-400 mt-1">
            {{ selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB · ${csvHeaders.length} columns detected` : '.csv files only · Max recommended ~5,000 rows per import' }}
          </p>
        </div>
        <input type="file" accept=".csv,text/csv" class="hidden" @change="onFileChange" />
      </label>

      <!-- ── Column Mapping (optional) ── -->
      <div v-if="selectedFile && csvHeaders.length > 0" class="mt-5 border-t border-slate-100 pt-4">
        <button
          @click="mappingOpen = !mappingOpen"
          class="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
        >
          <component :is="mappingOpen ? ChevronDownIcon : ChevronRightIcon" class="w-4 h-4" />
          Map columns
          <span v-if="!mappingOpen" class="ml-1 text-xs text-slate-400">(optional — use if your CSV has different header names)</span>
        </button>

        <Transition name="accordion">
          <div v-if="mappingOpen" class="mt-4 space-y-3">
            <!-- Auto-detect hint -->
            <div class="flex items-center justify-between mb-1">
              <p class="text-xs text-slate-500">
                Map each system field to the corresponding column in your CSV.
                <span class="text-emerald-600 font-medium">Auto-detected matches are pre-filled.</span>
              </p>
              <button
                @click="resetMapping"
                class="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 border border-slate-200 rounded-full px-3 py-1.5 transition-colors"
              >
                <RefreshCwIcon class="w-3 h-3" /> Reset
              </button>
            </div>

            <!-- Mapping grid -->
            <div class="rounded-[14px] border border-slate-200 overflow-hidden">
              <div class="grid grid-cols-[1fr_32px_1fr] text-xs font-semibold text-slate-500 bg-slate-50 px-4 py-2 border-b border-slate-200">
                <span>System Field</span>
                <span></span>
                <span>Your CSV Column</span>
              </div>
              <div class="max-h-80 overflow-y-auto divide-y divide-slate-100">
                <div
                  v-for="row in mappingRows"
                  :key="row.field"
                  class="grid grid-cols-[1fr_32px_1fr] items-center px-4 py-2 hover:bg-slate-50/60"
                >
                  <!-- System field -->
                  <div class="flex items-center gap-2">
                    <code class="text-xs font-mono text-slate-700">{{ row.field }}</code>
                    <span
                      v-if="requiredFields.some(f => f.name === row.field)"
                      class="text-[10px] font-bold text-rose-500 uppercase"
                    >req</span>
                  </div>

                  <ArrowRightIcon class="w-3.5 h-3.5 text-slate-300 mx-auto" />

                  <!-- CSV column select -->
                  <select
                    :value="columnMap[row.field] ?? ''"
                    @change="columnMap[row.field] = ($event.target as HTMLSelectElement).value"
                    class="w-full text-xs bg-white border border-slate-200 rounded-[8px] px-2 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400"
                  >
                    <option value="">— skip this field —</option>
                    <option v-for="h in csvHeaders" :key="h" :value="h">{{ h }}</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Unmapped required warning -->
            <div v-if="unmappedRequired.length > 0" class="flex items-start gap-2 bg-rose-50 border border-rose-200 rounded-[12px] px-4 py-3">
              <AlertTriangleIcon class="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
              <p class="text-xs text-rose-700">
                Required fields not mapped:
                <strong>{{ unmappedRequired.map(f => f.name).join(', ') }}</strong>
                — map these or ensure your CSV has matching column names.
              </p>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Actions -->
      <div class="mt-4 flex items-center gap-3">
        <button
          @click="handleUpload"
          :disabled="!selectedFile || uploading"
          class="flex items-center gap-2 px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-50"
        >
          <UploadIcon class="w-4 h-4" />
          {{ uploading ? 'Importing…' : 'Start Import' }}
        </button>
        <button
          v-if="selectedFile"
          @click="clearFile"
          class="px-4 py-2.5 border border-slate-200 text-slate-600 rounded-full text-sm hover:bg-slate-50 transition-colors"
        >
          Clear
        </button>
      </div>

      <!-- Upload progress (indeterminate while waiting for server response) -->
      <div v-if="uploading" class="mt-4 space-y-1.5">
        <div class="flex justify-between text-xs text-slate-500">
          <span>Sending to server…</span>
        </div>
        <div class="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
          <div class="h-full rounded-full bg-slate-700 animate-pulse" style="width: 100%" />
        </div>
      </div>

      <p v-if="errorMsg" class="mt-3 flex items-center gap-2 text-sm text-rose-600">
        <XCircleIcon class="w-4 h-4 shrink-0" /> {{ errorMsg }}
      </p>
    </div>

    <!-- ── Step 3: Import Results ── -->
    <div
      v-if="result"
      class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]"
    >
      <div class="flex items-center gap-2 mb-5">
        <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] font-bold shrink-0">3</span>
        <h3 class="text-sm font-semibold text-slate-700">Import Results</h3>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-4 gap-3 mb-6">
        <div class="text-center p-4 bg-slate-50 rounded-[16px]">
          <p class="text-3xl font-bold text-slate-900">{{ result.total }}</p>
          <p class="text-xs text-slate-500 mt-1">Total Rows</p>
        </div>
        <div class="text-center p-4 bg-emerald-50 rounded-[16px]">
          <p class="text-3xl font-bold text-emerald-700">{{ result.succeeded }}</p>
          <p class="text-xs text-emerald-600 mt-1">Imported</p>
        </div>
        <div class="text-center p-4 bg-amber-50 rounded-[16px]">
          <p class="text-3xl font-bold text-amber-600">{{ result.skipped }}</p>
          <p class="text-xs text-amber-500 mt-1">Skipped</p>
        </div>
        <div class="text-center p-4 bg-rose-50 rounded-[16px]">
          <p class="text-3xl font-bold text-rose-600">{{ result.failed }}</p>
          <p class="text-xs text-rose-500 mt-1">Failed</p>
        </div>
      </div>

      <!-- Progress bar -->
      <div class="mb-5">
        <div class="flex justify-between text-xs text-slate-500 mb-1">
          <span>Success rate</span><span>{{ successRate }}%</span>
        </div>
        <div class="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            class="h-full bg-emerald-500 rounded-full transition-all duration-700"
            :style="{ width: `${successRate}%` }"
          />
        </div>
      </div>

      <!-- Banner -->
      <div v-if="result.failed === 0 && result.skipped === 0" class="flex items-center justify-between gap-3 bg-emerald-50 border border-emerald-200 rounded-[14px] px-4 py-3 mb-4">
        <div class="flex items-center gap-2">
          <CheckCircle2Icon class="w-4 h-4 text-emerald-600 shrink-0" />
          <p class="text-sm text-emerald-700 font-medium">All records imported! Go to the directory to send invite links.</p>
        </div>
        <button
          @click="emit('navigate', 'employees')"
          class="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-700 text-white rounded-full text-xs font-semibold hover:bg-emerald-800 transition-colors shrink-0"
        >
          <UsersIcon class="w-3.5 h-3.5" /> Directory → Send Invites
        </button>
      </div>
      <div v-else-if="result.failed === 0 && result.skipped > 0" class="flex items-center justify-between gap-3 bg-amber-50 border border-amber-200 rounded-[14px] px-4 py-3 mb-4">
        <div class="flex items-center gap-2">
          <AlertTriangleIcon class="w-4 h-4 text-amber-500 shrink-0" />
          <p class="text-sm text-amber-700 font-medium">
            {{ result.skipped }} row{{ result.skipped !== 1 ? 's' : '' }} updated (already existed). New records ready for invites.
          </p>
        </div>
        <button
          v-if="result.succeeded > 0"
          @click="emit('navigate', 'employees')"
          class="flex items-center gap-1.5 px-4 py-1.5 bg-slate-700 text-white rounded-full text-xs font-semibold hover:bg-slate-800 transition-colors shrink-0"
        >
          <UsersIcon class="w-3.5 h-3.5" /> Directory → Send Invites
        </button>
      </div>
      <!-- View Directory when there are failures but some succeeded -->
      <div v-else-if="result.succeeded > 0" class="flex justify-end mb-4">
        <button
          @click="emit('navigate', 'employees')"
          class="flex items-center gap-1.5 px-4 py-2 border border-slate-200 text-slate-600 rounded-full text-xs font-semibold hover:bg-slate-50 transition-colors"
        >
          <UsersIcon class="w-3.5 h-3.5" /> Directory → Send Invites ({{ result.succeeded }} ready)
        </button>
      </div>

      <!-- Error / skip log -->
      <div v-if="result.errors.length > 0" class="space-y-2">
        <div class="flex items-center gap-2">
          <AlertTriangleIcon class="w-4 h-4 text-amber-500 shrink-0" />
          <p class="text-sm font-semibold text-slate-600">
            {{ result.errors.length }} issue{{ result.errors.length !== 1 ? 's' : '' }}
            <span v-if="result.failed > 0"> · {{ result.failed }} failed (fix &amp; re-import)</span>
            <span v-if="result.skipped > 0"> · {{ result.skipped }} skipped (already exist)</span>
          </p>
        </div>
        <div class="rounded-[14px] border border-slate-200 overflow-hidden">
          <div class="grid grid-cols-[64px_1fr_2fr] text-xs font-semibold text-slate-500 bg-slate-50 px-4 py-2 border-b border-slate-200">
            <span>Row</span><span>Field</span><span>Message</span>
          </div>
          <div
            v-for="err in result.errors"
            :key="err.row"
            :class="[
              'grid grid-cols-[64px_1fr_2fr] text-xs py-2.5 px-4 border-b border-slate-100 last:border-0',
              err.skipped ? 'bg-amber-50/50' : 'hover:bg-slate-50/60',
            ]"
          >
            <span class="font-mono font-semibold text-slate-500">{{ err.row }}</span>
            <span class="text-slate-500 font-medium">{{ err.field ?? '—' }}</span>
            <span :class="err.skipped ? 'text-amber-600' : 'text-rose-600'">{{ err.error }}</span>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.accordion-enter-active, .accordion-leave-active { transition: all 0.25s ease; overflow: hidden; }
.accordion-enter-from, .accordion-leave-to { opacity: 0; max-height: 0; }
.accordion-enter-to, .accordion-leave-from { opacity: 1; max-height: 2000px; }
</style>
