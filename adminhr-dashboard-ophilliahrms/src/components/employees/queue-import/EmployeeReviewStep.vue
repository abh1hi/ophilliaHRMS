<script setup lang="ts">
/**
 * EmployeeReviewStep — shows the final cleaned data for one employee,
 * lets HR assign a department, displays the auto-generated initial password,
 * and triggers the actual create.
 */
import { ref, computed } from 'vue'
import { CheckCircle2Icon, KeyIcon, CopyIcon, CheckIcon, XCircleIcon, LoaderIcon } from 'lucide-vue-next'
import type { Department } from '../../../services/department.service'

// ─── Props / Emits ────────────────────────────────────────────────────────────
const props = defineProps<{
  data: Record<string, string>
  departments: Department[]
  password: string
  loading: boolean
  submitError: string
}>()

const emit = defineEmits<{
  (e: 'submit', departmentId: string): void
  (e: 'skip'): void
}>()

// ─── Department selection ─────────────────────────────────────────────────────
// Pre-select if the corrected data already has a department UUID (set in correction step)
const selectedDeptId = ref(
  // If data.department looks like a UUID, use it; otherwise empty
  /^[0-9a-f-]{36}$/.test(props.data.department ?? '') ? props.data.department : ''
)

const selectedDeptName = computed(() => {
  const d = props.departments.find(d => d.id === selectedDeptId.value)
  return d?.name ?? '—'
})

// ─── Password copy ────────────────────────────────────────────────────────────
const copied = ref(false)
async function copyPassword() {
  try {
    await navigator.clipboard.writeText(props.password)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2500)
  } catch {
    // fallback — select the text
  }
}

// ─── Field display config ─────────────────────────────────────────────────────
const SECTIONS = [
  {
    title: 'Personal',
    fields: ['first_name', 'last_name', 'email', 'phone', 'gender', 'date_of_birth', 'personal_email'],
  },
  {
    title: 'Employment',
    fields: ['employee_code', 'designation', 'date_joined', 'employment_status', 'joining_salary', 'project'],
  },
  {
    title: 'Government IDs',
    fields: ['pan_number', 'aadhaar_number', 'uan_number', 'esi_number', 'driving_license_number'],
  },
  {
    title: 'Banking',
    fields: ['bank_account_number', 'bank_name', 'bank_branch', 'ifsc_code', 'salary_mode'],
  },
  {
    title: 'Address',
    fields: ['door_no', 'street', 'village_town', 'pin_code'],
  },
]

const LABELS: Record<string, string> = {
  first_name: 'First Name', last_name: 'Last Name', email: 'Work Email',
  phone: 'Phone', gender: 'Gender', date_of_birth: 'Date of Birth', personal_email: 'Personal Email',
  employee_code: 'Employee Code', designation: 'Designation', date_joined: 'Date Joined',
  employment_status: 'Status', joining_salary: 'Salary (CTC)', project: 'Project',
  pan_number: 'PAN', aadhaar_number: 'Aadhaar', uan_number: 'UAN', esi_number: 'ESI',
  driving_license_number: 'Driving License', bank_account_number: 'Account No.',
  bank_name: 'Bank', bank_branch: 'Branch', ifsc_code: 'IFSC', salary_mode: 'Pay Mode',
  door_no: 'Door No.', street: 'Street', village_town: 'Town', pin_code: 'PIN',
}

function fieldValue(field: string): string {
  return props.data[field]?.trim() || ''
}

function sectionHasData(section: typeof SECTIONS[number]): boolean {
  return section.fields.some(f => fieldValue(f))
}
</script>

<template>
  <div class="space-y-5">

    <!-- Ready banner -->
    <div class="flex items-center gap-3 p-3 bg-emerald-50 border border-emerald-200/60 rounded-[14px]">
      <CheckCircle2Icon class="w-4 h-4 text-emerald-600 shrink-0" />
      <p class="text-sm text-emerald-800 font-medium">
        Data is ready. Review the details, assign a department, then submit.
      </p>
    </div>

    <!-- Department assignment -->
    <div class="bg-white/70 border border-slate-200/60 rounded-[16px] p-4">
      <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
        Department
      </label>
      <select
        v-model="selectedDeptId"
        class="w-full px-3 py-2 text-sm border border-slate-200 rounded-[10px] bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/10"
      >
        <option value="">— No department —</option>
        <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
      </select>
    </div>

    <!-- Data sections -->
    <div
      v-for="section in SECTIONS"
      :key="section.title"
      v-show="sectionHasData(section)"
      class="bg-white/60 border border-slate-200/60 rounded-[16px] p-4"
    >
      <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">{{ section.title }}</p>
      <dl class="grid grid-cols-2 gap-x-6 gap-y-2.5">
        <template v-for="field in section.fields" :key="field">
          <div v-if="fieldValue(field)" class="col-span-1">
            <dt class="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
              {{ LABELS[field] ?? field.replace(/_/g, ' ') }}
            </dt>
            <dd class="text-sm text-slate-800 font-medium mt-0.5 break-all">{{ fieldValue(field) }}</dd>
          </div>
        </template>
      </dl>
    </div>

    <!-- Password block -->
    <div class="bg-slate-900 rounded-[18px] p-5">
      <div class="flex items-center gap-2 mb-3">
        <KeyIcon class="w-4 h-4 text-amber-400" />
        <p class="text-sm font-semibold text-white">Initial Login Credentials</p>
      </div>
      <div class="grid grid-cols-2 gap-3 mb-4">
        <div class="bg-white/10 rounded-[12px] px-3 py-2.5">
          <p class="text-[10px] text-white/50 uppercase tracking-wider mb-0.5">Email</p>
          <p class="text-sm text-white font-mono break-all">{{ data.email }}</p>
        </div>
        <div class="bg-white/10 rounded-[12px] px-3 py-2.5 relative">
          <p class="text-[10px] text-white/50 uppercase tracking-wider mb-0.5">Password</p>
          <div class="flex items-center justify-between gap-2">
            <p class="text-sm text-amber-300 font-mono font-bold tracking-widest">{{ password }}</p>
            <button
              @click="copyPassword"
              :class="[
                'shrink-0 p-1.5 rounded-[8px] transition-colors',
                copied ? 'bg-emerald-500 text-white' : 'bg-white/20 text-white/70 hover:bg-white/30',
              ]"
              title="Copy password"
            >
              <CheckIcon v-if="copied" class="w-3.5 h-3.5" />
              <CopyIcon v-else class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
      <p class="text-xs text-white/40">
        Share this password with the employee. They can change it after first login.
      </p>
    </div>

    <!-- Submit error -->
    <div v-if="submitError" class="flex items-center gap-2 text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-[12px] px-4 py-3">
      <XCircleIcon class="w-4 h-4 shrink-0" /> {{ submitError }}
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-3">
      <button
        @click="emit('submit', selectedDeptId)"
        :disabled="loading"
        class="flex items-center gap-2 px-6 py-2.5 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 disabled:opacity-50 transition-all"
      >
        <LoaderIcon v-if="loading" class="w-4 h-4 animate-spin" />
        <CheckCircle2Icon v-else class="w-4 h-4" />
        {{ loading ? 'Creating…' : 'Submit & Create Account' }}
      </button>
      <button
        @click="emit('skip')"
        :disabled="loading"
        class="px-5 py-2.5 border border-slate-200 text-slate-500 rounded-full text-sm hover:bg-slate-50 disabled:opacity-40 transition-colors"
      >
        Skip Employee
      </button>
    </div>
  </div>
</template>
