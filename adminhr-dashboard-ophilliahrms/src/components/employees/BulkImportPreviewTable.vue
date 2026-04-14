<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  CheckCircle2Icon, XCircleIcon, AlertTriangleIcon, RepeatIcon,
  ChevronLeftIcon, ChevronRightIcon, DownloadIcon, PencilIcon, CheckIcon, XIcon,
} from 'lucide-vue-next'
import type { PreviewRow, RowIssue, AutoCorrection, PreviewSummary } from '../../services/employee.service'

// ─── Props / Emits ────────────────────────────────────────────────────────────
const props = defineProps<{
  rows: PreviewRow[]
  summary: PreviewSummary
  autoCorrections: AutoCorrection[]
  jobId?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'cell-edit', rowIndex: number, field: string, newValue: string): void
  (e: 'download-errors'): void
}>()

// ─── Pagination ───────────────────────────────────────────────────────────────
const PAGE_SIZE = 50
const currentPage = ref(1)
const totalPages = computed(() => Math.max(1, Math.ceil(props.rows.length / PAGE_SIZE)))
const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return props.rows.slice(start, start + PAGE_SIZE)
})

// ─── Columns: union of all fields across visible rows ────────────────────────
const columns = computed(() => {
  const cols = new Set<string>()
  // Show key fields first
  const priority = ['first_name', 'last_name', 'email', 'phone', 'date_joined', 'designation', 'department', 'employment_status']
  priority.forEach(c => cols.add(c))
  props.rows.slice(0, 100).forEach(r => Object.keys(r.data).forEach(k => cols.add(k)))
  return Array.from(cols).filter(c => props.rows.some(r => r.data[c]))
})

// ─── Status config ────────────────────────────────────────────────────────────
const STATUS = {
  valid:     { bg: 'bg-emerald-50',  border: 'border-emerald-100', dot: 'bg-emerald-400' },
  warning:   { bg: 'bg-amber-50',    border: 'border-amber-100',   dot: 'bg-amber-400' },
  error:     { bg: 'bg-red-50',      border: 'border-red-100',     dot: 'bg-red-500' },
  cross_row: { bg: 'bg-orange-50',   border: 'border-orange-100',  dot: 'bg-orange-500' },
}

function rowStyle(status: string) {
  return STATUS[status as keyof typeof STATUS] ?? STATUS.valid
}

// ─── Issues tooltip per cell ──────────────────────────────────────────────────
function cellIssues(row: PreviewRow, field: string): RowIssue[] {
  return row.issues.filter(i => i.field === field)
}

function cellHasError(row: PreviewRow, field: string): boolean {
  return row.issues.some(i => i.field === field && !i.is_warning)
}

function cellHasWarning(row: PreviewRow, field: string): boolean {
  return row.issues.some(i => i.field === field && i.is_warning)
}

// ─── Inline editing ───────────────────────────────────────────────────────────
const editingCell = ref<{ rowIndex: number; field: string } | null>(null)
const editValue = ref('')

function startEdit(rowIndex: number, field: string, current: string) {
  editingCell.value = { rowIndex, field }
  editValue.value = current
}

function commitEdit() {
  if (!editingCell.value) return
  emit('cell-edit', editingCell.value.rowIndex, editingCell.value.field, editValue.value)
  editingCell.value = null
}

function cancelEdit() {
  editingCell.value = null
}

function isEditing(rowIndex: number, field: string) {
  return editingCell.value?.rowIndex === rowIndex && editingCell.value?.field === field
}

// ─── Summary counts ───────────────────────────────────────────────────────────
const statusCounts = computed(() => {
  let valid = 0, warning = 0, error = 0, cross = 0
  for (const r of props.rows) {
    if (r.status === 'valid')     valid++
    else if (r.status === 'warning')  warning++
    else if (r.status === 'error')    error++
    else if (r.status === 'cross_row') cross++
  }
  return { valid, warning, error, cross }
})
</script>

<template>
  <div class="space-y-4">

    <!-- Summary Banner -->
    <div class="flex flex-wrap gap-3 items-center p-4 bg-white/60 border border-slate-200/60 rounded-[16px] backdrop-blur">
      <!-- "Ready" = valid + warning rows (both are importable) -->
      <div class="flex items-center gap-2 text-sm">
        <CheckCircle2Icon class="w-4 h-4 text-emerald-500" />
        <span class="font-medium text-emerald-700">
          {{ statusCounts.valid + statusCounts.warning }} ready to import
        </span>
        <span v-if="statusCounts.warning > 0" class="text-xs text-slate-400">
          ({{ statusCounts.warning }} with minor notes)
        </span>
      </div>
      <div v-if="statusCounts.error > 0" class="flex items-center gap-2 text-sm">
        <XCircleIcon class="w-4 h-4 text-red-500" />
        <span class="font-medium text-red-700">{{ statusCounts.error }} errors</span>
      </div>
      <div v-if="statusCounts.cross > 0" class="flex items-center gap-2 text-sm">
        <RepeatIcon class="w-4 h-4 text-orange-500" />
        <span class="font-medium text-orange-700">{{ statusCounts.cross }} file-duplicates</span>
      </div>
      <div v-if="summary.auto_corrections > 0" class="flex items-center gap-2 text-sm ml-auto">
        <span class="text-slate-500 italic">{{ summary.auto_corrections }} fields auto-corrected</span>
      </div>

      <!-- Download Error Report -->
      <button
        v-if="statusCounts.error > 0 || statusCounts.cross > 0"
        @click="emit('download-errors')"
        class="ml-auto flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-[10px] border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
      >
        <DownloadIcon class="w-3.5 h-3.5" />
        Download Error Report
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16 text-slate-400">
      <div class="w-5 h-5 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin mr-3" />
      Validating rows…
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto rounded-[18px] border border-slate-200/60 bg-white/50 backdrop-blur">
      <table class="w-full text-xs text-left">
        <thead class="border-b border-slate-200/60 bg-white/40">
          <tr>
            <th class="px-3 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider w-12">#</th>
            <th class="px-3 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider w-20">Status</th>
            <th
              v-for="col in columns"
              :key="col"
              class="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap"
            >
              {{ col.replace(/_/g, ' ') }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="rows.length === 0">
            <td :colspan="columns.length + 2" class="px-5 py-12 text-center text-slate-400">
              No rows to preview.
            </td>
          </tr>
          <tr
            v-for="(row, idx) in pagedRows"
            :key="row.index"
            :class="[
              'border-b border-slate-100/60 transition-colors',
              rowStyle(row.status).bg,
              rowStyle(row.status).border,
            ]"
          >
            <!-- Row number -->
            <td class="px-3 py-2.5 text-slate-400 font-mono">
              {{ row.index + 2 }}
            </td>

            <!-- Status dot + label -->
            <td class="px-3 py-2.5">
              <div class="flex items-center gap-1.5">
                <span :class="['w-2 h-2 rounded-full shrink-0', rowStyle(row.status).dot]" />
                <span class="text-xs font-medium capitalize text-slate-600">
                  {{ row.status === 'cross_row' ? 'duplicate' : row.status }}
                </span>
              </div>
            </td>

            <!-- Data cells -->
            <td
              v-for="col in columns"
              :key="col"
              class="px-3 py-2 max-w-[180px]"
            >
              <!-- Editing state -->
              <div v-if="isEditing(row.index, col)" class="flex items-center gap-1">
                <input
                  v-model="editValue"
                  @keydown.enter="commitEdit"
                  @keydown.escape="cancelEdit"
                  autofocus
                  class="w-full px-2 py-1 text-xs border border-slate-300 rounded-[6px] focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                />
                <button @click="commitEdit" class="text-emerald-600 hover:text-emerald-700">
                  <CheckIcon class="w-3.5 h-3.5" />
                </button>
                <button @click="cancelEdit" class="text-slate-400 hover:text-slate-600">
                  <XIcon class="w-3.5 h-3.5" />
                </button>
              </div>

              <!-- Display state -->
              <div v-else class="group relative">
                <!-- Cell value -->
                <div
                  :class="[
                    'text-xs truncate pr-5',
                    cellHasError(row, col) ? 'text-red-700 font-medium' :
                    cellHasWarning(row, col) ? 'text-amber-700' : 'text-slate-700',
                  ]"
                  :title="row.data[col] ?? ''"
                >
                  {{ row.data[col] || '—' }}
                </div>

                <!-- Edit button on error cells -->
                <button
                  v-if="cellHasError(row, col) || row.status !== 'valid'"
                  @click="startEdit(row.index, col, row.data[col] ?? '')"
                  class="absolute right-0 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Edit cell"
                >
                  <PencilIcon class="w-3 h-3 text-slate-400 hover:text-slate-700" />
                </button>

                <!-- Issue tooltip -->
                <div
                  v-if="cellIssues(row, col).length > 0"
                  class="absolute left-0 bottom-full mb-1 z-20 hidden group-hover:block min-w-[200px] max-w-xs"
                >
                  <div class="bg-slate-900 text-white text-xs rounded-[10px] px-3 py-2 shadow-lg space-y-1">
                    <div v-for="issue in cellIssues(row, col)" :key="issue.error">
                      <p class="font-medium">{{ issue.error }}</p>
                      <p v-if="issue.suggested_fix" class="text-slate-300 mt-0.5">
                        Fix: {{ issue.suggested_fix }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between pt-1">
      <span class="text-xs text-slate-500">
        Page {{ currentPage }} of {{ totalPages }}
        <span class="text-slate-400 ml-1">({{ rows.length }} rows)</span>
      </span>
      <div class="flex items-center gap-2">
        <button
          @click="currentPage--"
          :disabled="currentPage <= 1"
          class="flex items-center gap-1 px-3 py-1.5 rounded-[10px] border border-slate-200 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeftIcon class="w-3.5 h-3.5" /> Previous
        </button>
        <button
          @click="currentPage++"
          :disabled="currentPage >= totalPages"
          class="flex items-center gap-1 px-3 py-1.5 rounded-[10px] border border-slate-200 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Next <ChevronRightIcon class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

  </div>
</template>
