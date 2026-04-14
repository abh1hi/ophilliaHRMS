<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  UploadIcon, AlertTriangleIcon, ChevronDownIcon, ChevronRightIcon,
  ArrowRightIcon, RefreshCwIcon, LoaderIcon,
} from 'lucide-vue-next'
import { parseCsvHeaders, parseXlsxHeaders, EMPLOYEE_SYSTEM_FIELDS } from '../../services/employee.service'

const props = defineProps<{
  loading?: boolean
  errorMsg?: string
}>()

const emit = defineEmits<{
  (e: 'file-selected', file: File, headers: string[], columnMap: Record<string, string>): void
  (e: 'preview', file: File, columnMap: Record<string, string>, duplicateStrategy: string): void
  (e: 'clear'): void
}>()

// ─── State ────────────────────────────────────────────────────────────────────
const selectedFile      = ref<File | null>(null)
const dragOver          = ref(false)
const csvHeaders        = ref<string[]>([])
const columnMap         = ref<Record<string, string>>({})
const mappingOpen       = ref(false)
const duplicateStrategy = ref<'skip' | 'update' | 'fail'>('update')

const requiredFields = ['first_name', 'last_name', 'email']

const unmappedRequired = computed(() =>
  requiredFields.filter(f => {
    const mapped = columnMap.value[f]
    return !mapped || !csvHeaders.value.includes(mapped)
  })
)

const mappingRows = computed(() =>
  EMPLOYEE_SYSTEM_FIELDS.map(field => ({ field, mapped: columnMap.value[field] ?? '' }))
)

// ─── File handling ─────────────────────────────────────────────────────────────
function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  handleFile(input.files?.[0] ?? null)
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file && (file.name.endsWith('.csv') || file.name.endsWith('.xlsx'))) {
    handleFile(file)
  }
}

async function handleFile(file: File | null) {
  selectedFile.value = file
  csvHeaders.value = []
  columnMap.value = {}
  mappingOpen.value = false
  if (!file) return

  const headers = file.name.endsWith('.xlsx')
    ? await parseXlsxHeaders(file)
    : await parseCsvHeaders(file)
  csvHeaders.value = headers
  autoMap(headers)
  emit('file-selected', file, headers, columnMap.value)
}

function autoMap(headers: string[]) {
  const map: Record<string, string> = {}
  const headerSet = new Set(headers)
  for (const field of EMPLOYEE_SYSTEM_FIELDS) {
    if (headerSet.has(field)) { map[field] = field; continue }
    const fuzzy = headers.find(h => h.replace(/[-\s]/g, '_') === field)
    if (fuzzy) map[field] = fuzzy
  }
  columnMap.value = map
}

function resetMapping() {
  if (csvHeaders.value.length) autoMap(csvHeaders.value)
}

function clearFile() {
  selectedFile.value = null
  csvHeaders.value = []
  columnMap.value = {}
  mappingOpen.value = false
  emit('clear')
}
</script>

<template>
  <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
    <div class="flex items-center gap-2 mb-4">
      <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] font-bold shrink-0">2</span>
      <h3 class="text-sm font-semibold text-slate-700">Upload File &amp; Map Columns</h3>
    </div>

    <!-- Drop zone -->
    <label class="block w-full cursor-pointer">
      <div
        :class="[
          'border-2 border-dashed rounded-[18px] p-10 text-center transition-all',
          dragOver     ? 'border-slate-400 bg-slate-50 scale-[1.01]' :
          selectedFile ? 'border-emerald-300 bg-emerald-50/50' :
                         'border-slate-200 hover:border-slate-300',
        ]"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
      >
        <UploadIcon :class="['w-9 h-9 mx-auto mb-3', selectedFile ? 'text-emerald-400' : 'text-slate-300']" />
        <p class="text-sm font-medium text-slate-600">
          {{ selectedFile ? selectedFile.name : 'Click to browse or drag & drop a .csv or .xlsx file' }}
        </p>
        <p class="text-xs text-slate-400 mt-1">
          {{ selectedFile
            ? `${(selectedFile.size / 1024).toFixed(1)} KB · ${csvHeaders.length} columns detected`
            : '.csv or .xlsx · Max 10 MB · ~5,000 rows recommended per import' }}
        </p>
      </div>
      <input type="file" accept=".csv,.xlsx,text/csv" class="hidden" @change="onFileChange" />
    </label>

    <!-- Column Mapping -->
    <div v-if="selectedFile && csvHeaders.length > 0" class="mt-5 border-t border-slate-100 pt-4">
      <button
        @click="mappingOpen = !mappingOpen"
        class="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
      >
        <component :is="mappingOpen ? ChevronDownIcon : ChevronRightIcon" class="w-4 h-4" />
        Map columns
        <span v-if="!mappingOpen" class="ml-1 text-xs text-slate-400">(optional)</span>
      </button>
      <Transition name="accordion">
        <div v-if="mappingOpen" class="mt-4 space-y-3">
          <div class="flex items-center justify-between mb-1">
            <p class="text-xs text-slate-500">Auto-detected matches are pre-filled.</p>
            <button @click="resetMapping"
              class="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 border border-slate-200 rounded-full px-3 py-1.5 transition-colors">
              <RefreshCwIcon class="w-3 h-3" /> Reset
            </button>
          </div>
          <div class="rounded-[14px] border border-slate-200 overflow-hidden">
            <div class="grid grid-cols-[1fr_32px_1fr] text-xs font-semibold text-slate-500 bg-slate-50 px-4 py-2 border-b border-slate-200">
              <span>System Field</span><span></span><span>Your Column</span>
            </div>
            <div class="max-h-80 overflow-y-auto divide-y divide-slate-100">
              <div v-for="row in mappingRows" :key="row.field"
                   class="grid grid-cols-[1fr_32px_1fr] items-center px-4 py-2 hover:bg-slate-50/60">
                <div class="flex items-center gap-2">
                  <code class="text-xs font-mono text-slate-700">{{ row.field }}</code>
                  <span v-if="requiredFields.includes(row.field)"
                        class="text-[10px] font-bold text-rose-500 uppercase">req</span>
                </div>
                <ArrowRightIcon class="w-3.5 h-3.5 text-slate-300 mx-auto" />
                <select
                  :value="columnMap[row.field] ?? ''"
                  @change="columnMap[row.field] = ($event.target as HTMLSelectElement).value"
                  class="w-full text-xs bg-white border border-slate-200 rounded-[8px] px-2 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                >
                  <option value="">— skip —</option>
                  <option v-for="h in csvHeaders" :key="h" :value="h">{{ h }}</option>
                </select>
              </div>
            </div>
          </div>
          <div v-if="unmappedRequired.length > 0"
               class="flex items-start gap-2 bg-rose-50 border border-rose-200 rounded-[12px] px-4 py-3">
            <AlertTriangleIcon class="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
            <p class="text-xs text-rose-700">
              Required fields not mapped: <strong>{{ unmappedRequired.join(', ') }}</strong>
            </p>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Duplicate strategy -->
    <div v-if="selectedFile" class="mt-4 flex items-center gap-3 flex-wrap">
      <span class="text-xs font-medium text-slate-500">If duplicate email found:</span>
      <div class="flex gap-2">
        <button v-for="opt in [['update','Update existing'],['skip','Skip'],['fail','Reject']]" :key="opt[0]"
          @click="duplicateStrategy = opt[0] as any"
          :class="[
            'px-3 py-1.5 text-xs rounded-full border transition-colors',
            duplicateStrategy === opt[0]
              ? 'bg-slate-900 text-white border-slate-900'
              : 'border-slate-200 text-slate-600 hover:bg-slate-50',
          ]">
          {{ opt[1] }}
        </button>
      </div>
    </div>

    <!-- Actions -->
    <div class="mt-4 flex items-center gap-3 flex-wrap">
      <button
        @click="emit('preview', selectedFile!, columnMap, duplicateStrategy)"
        :disabled="!selectedFile || loading"
        class="flex items-center gap-2 px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-50"
      >
        <LoaderIcon v-if="loading" class="w-4 h-4 animate-spin" />
        <UploadIcon v-else class="w-4 h-4" />
        {{ loading ? 'Analysing…' : 'Preview File' }}
      </button>
      <button v-if="selectedFile" @click="clearFile"
        class="px-4 py-2.5 border border-slate-200 text-slate-600 rounded-full text-sm hover:bg-slate-50 transition-colors">
        Clear
      </button>
    </div>

    <p v-if="errorMsg" class="mt-3 flex items-center gap-2 text-sm text-rose-600">
      <AlertTriangleIcon class="w-4 h-4 shrink-0" /> {{ errorMsg }}
    </p>
  </div>
</template>

<style scoped>
.accordion-enter-active, .accordion-leave-active { transition: all 0.25s ease; overflow: hidden; }
.accordion-enter-from, .accordion-leave-to { opacity: 0; max-height: 0; }
.accordion-enter-to, .accordion-leave-from { opacity: 1; max-height: 2000px; }
</style>
