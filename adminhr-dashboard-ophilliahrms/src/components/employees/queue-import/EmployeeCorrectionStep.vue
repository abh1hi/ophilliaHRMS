<script setup lang="ts">
/**
 * EmployeeCorrectionStep — shows ONLY the fields that still have issues after
 * auto-sanitization. Hard-error fields must be filled; warning fields can be skipped.
 */
import { ref, computed } from 'vue'
import { AlertTriangleIcon, XCircleIcon, RepeatIcon, SkipForwardIcon, CheckIcon } from 'lucide-vue-next'
import type { PreviewRow, RowIssue } from '../../../services/employee.service'
import type { Department } from '../../../services/department.service'

// ─── Props / Emits ────────────────────────────────────────────────────────────
const props = defineProps<{
  row: PreviewRow
  departments: Department[]
}>()

const emit = defineEmits<{
  (e: 'done', data: Record<string, string>): void
}>()

// ─── Field metadata ───────────────────────────────────────────────────────────
const REQUIRED = new Set(['first_name', 'last_name', 'email'])

const LABELS: Record<string, string> = {
  first_name: 'First Name', last_name: 'Last Name', email: 'Work Email',
  phone: 'Phone', phone_2: 'Alt Phone', date_of_birth: 'Date of Birth',
  date_joined: 'Date Joined', gender: 'Gender', employment_status: 'Status',
  pan_number: 'PAN Number', aadhaar_number: 'Aadhaar Number', uan_number: 'UAN Number',
  esi_number: 'ESI Number', employee_code: 'Employee Code', department: 'Department',
  designation: 'Designation', joining_salary: 'Salary (CTC)', year_of_passing: 'Year of Passing',
  personal_email: 'Personal Email', bank_account_number: 'Bank Account',
  driving_license_number: 'Driving License',
}

const SELECT_FIELDS: Record<string, { label: string; value: string }[]> = {
  gender: [
    { label: 'Male',   value: 'male'   },
    { label: 'Female', value: 'female' },
    { label: 'Other',  value: 'other'  },
  ],
  employment_status: [
    { label: 'Active',     value: 'active'     },
    { label: 'Inactive',   value: 'inactive'   },
    { label: 'Terminated', value: 'terminated' },
  ],
}

// ─── Derived issue list ───────────────────────────────────────────────────────
// Group issues by field; include cross-row issues so email can be fixed.
const issuesByField = computed(() => {
  const map: Record<string, RowIssue[]> = {}
  for (const issue of props.row.issues) {
    if (!map[issue.field]) map[issue.field] = []
    map[issue.field].push(issue)
  }
  return map
})

const issueFields = computed(() => Object.keys(issuesByField.value))

// ─── Local editable state ─────────────────────────────────────────────────────
const values  = ref<Record<string, string>>(
  Object.fromEntries(issueFields.value.map(f => [f, props.row.data[f] ?? '']))
)
const skipped = ref<Set<string>>(new Set())

function toggleSkip(field: string) {
  const next = new Set(skipped.value)
  if (next.has(field)) next.delete(field)
  else next.add(field)
  skipped.value = next
}

// ─── Validation ───────────────────────────────────────────────────────────────
function fieldHasHardError(field: string): boolean {
  return (issuesByField.value[field] ?? []).some(i => !i.is_warning)
}

function isResolved(field: string): boolean {
  if (skipped.value.has(field)) return !REQUIRED.has(field)  // can't skip required
  return values.value[field]?.trim().length > 0
}

const allResolved = computed(() => issueFields.value.every(isResolved))

// ─── Submit ───────────────────────────────────────────────────────────────────
function proceed() {
  if (!allResolved.value) return
  const merged = { ...props.row.data }
  for (const field of issueFields.value) {
    if (skipped.value.has(field)) {
      delete merged[field]
    } else {
      merged[field] = values.value[field] ?? ''
    }
  }
  emit('done', merged)
}

// ─── Input type helper ────────────────────────────────────────────────────────
function inputType(field: string): string {
  if (field === 'date_of_birth' || field === 'date_joined') return 'date'
  if (field === 'joining_salary' || field === 'last_drawn_salary') return 'number'
  if (field === 'email' || field === 'personal_email') return 'email'
  return 'text'
}
</script>

<template>
  <div class="space-y-5">

    <!-- Preamble -->
    <div class="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200/70 rounded-[16px]">
      <AlertTriangleIcon class="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
      <div class="text-sm text-amber-800">
        <span class="font-semibold">{{ issueFields.length }} field{{ issueFields.length !== 1 ? 's' : '' }} need attention.</span>
        Auto-sanitized fields are already corrected — only these remain.
        Required fields must be filled; optional ones can be skipped.
      </div>
    </div>

    <!-- Issue fields -->
    <div class="space-y-3">
      <div
        v-for="field in issueFields"
        :key="field"
        :class="[
          'rounded-[16px] border p-4 transition-all',
          skipped.has(field)
            ? 'bg-slate-50 border-slate-200 opacity-60'
            : fieldHasHardError(field)
              ? 'bg-rose-50/60 border-rose-200'
              : 'bg-amber-50/60 border-amber-200',
        ]"
      >
        <!-- Field header -->
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <XCircleIcon v-if="fieldHasHardError(field)" class="w-3.5 h-3.5 text-rose-500 shrink-0" />
            <AlertTriangleIcon v-else class="w-3.5 h-3.5 text-amber-500 shrink-0" />
            <RepeatIcon v-if="(issuesByField[field] ?? []).some(i => i.is_cross_row)" class="w-3.5 h-3.5 text-orange-500 shrink-0" />
            <label class="text-xs font-semibold text-slate-700">
              {{ LABELS[field] ?? field.replace(/_/g, ' ') }}
              <span v-if="REQUIRED.has(field)" class="text-rose-500 ml-0.5">*</span>
            </label>
          </div>
          <!-- Skip button — only for non-required fields -->
          <button
            v-if="!REQUIRED.has(field)"
            @click="toggleSkip(field)"
            :class="[
              'flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors',
              skipped.has(field)
                ? 'bg-slate-200 border-slate-300 text-slate-600'
                : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50',
            ]"
          >
            <SkipForwardIcon class="w-3 h-3" />
            {{ skipped.has(field) ? 'Un-skip' : 'Skip' }}
          </button>
        </div>

        <!-- Issue messages -->
        <div class="mb-2 space-y-0.5">
          <p
            v-for="issue in (issuesByField[field] ?? [])"
            :key="issue.error"
            :class="['text-xs', issue.is_warning ? 'text-amber-700' : 'text-rose-700']"
          >
            {{ issue.error }}
            <span v-if="issue.suggested_fix" class="text-slate-400 italic"> — {{ issue.suggested_fix }}</span>
          </p>
        </div>

        <!-- Input (disabled when skipped) -->
        <div v-if="!skipped.has(field)">
          <!-- Department → dropdown -->
          <select
            v-if="field === 'department'"
            v-model="values[field]"
            class="w-full px-3 py-2 text-sm border border-slate-200 rounded-[10px] bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/10"
          >
            <option value="">— select department —</option>
            <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>

          <!-- Enum fields → dropdown -->
          <select
            v-else-if="SELECT_FIELDS[field]"
            v-model="values[field]"
            class="w-full px-3 py-2 text-sm border border-slate-200 rounded-[10px] bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/10"
          >
            <option value="">— select —</option>
            <option v-for="opt in SELECT_FIELDS[field]" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>

          <!-- Default → text/date/number input -->
          <input
            v-else
            v-model="values[field]"
            :type="inputType(field)"
            :placeholder="LABELS[field] ?? field"
            class="w-full px-3 py-2 text-sm border border-slate-200 rounded-[10px] bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/10"
          />
        </div>

        <!-- Resolved checkmark -->
        <div v-if="isResolved(field)" class="flex items-center gap-1 mt-2 text-xs text-emerald-600">
          <CheckIcon class="w-3 h-3" /> {{ skipped.has(field) ? 'Skipped' : 'Looks good' }}
        </div>
      </div>
    </div>

    <!-- Continue button -->
    <div class="pt-1">
      <button
        @click="proceed"
        :disabled="!allResolved"
        class="flex items-center gap-2 px-6 py-2.5 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        Continue to Review →
      </button>
    </div>
  </div>
</template>
