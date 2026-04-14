<script setup lang="ts">
/**
 * BulkImportQueueModal — full-screen orchestrator for queue-based import.
 *
 * Phase per employee:
 *   correcting → reviewing → submitting → success | error
 *
 * After all employees: shows a summary card.
 */
import { ref, computed, watch, onMounted } from 'vue'
import {
  XIcon, CheckCircle2Icon, XCircleIcon, SkipForwardIcon,
  UsersIcon, CopyIcon, CheckIcon,
} from 'lucide-vue-next'
import type { PreviewRow } from '../../../services/employee.service'
import type { Department } from '../../../services/department.service'
import {
  buildEmployeePayload,
  createEmployeeRecord,
  generateEmployeePassword,
} from '../../../services/employee.service'
import { createUser } from '../../../services/auth.service'
import EmployeeCorrectionStep from './EmployeeCorrectionStep.vue'
import EmployeeReviewStep    from './EmployeeReviewStep.vue'

// ─── Props / Emits ────────────────────────────────────────────────────────────
const props = defineProps<{
  rows: PreviewRow[]
  departments: Department[]
}>()
const emit = defineEmits<{ (e: 'close'): void }>()

// ─── Queue state ──────────────────────────────────────────────────────────────
type Phase = 'correcting' | 'reviewing' | 'submitting' | 'success' | 'error'

interface QueueResult {
  name: string
  email: string
  status: 'imported' | 'skipped' | 'failed'
  password?: string
  accountCreated?: boolean
  error?: string
}

const idx          = ref(0)
const phase        = ref<Phase>('correcting')
const corrected    = ref<Record<string, string>>({})
const password     = ref('')
const submitError  = ref('')
const autoTimer    = ref<ReturnType<typeof setTimeout> | null>(null)
const results      = ref<QueueResult[]>([])

const currentRow   = computed(() => props.rows[idx.value])
const allDone      = computed(() => idx.value >= props.rows.length)
const progress     = computed(() => Math.round((idx.value / props.rows.length) * 100))

const employeeName = computed(() => {
  const d = corrected.value
  const r = currentRow.value?.data
  const fn = d.first_name || r?.first_name || ''
  const ln = d.last_name  || r?.last_name  || ''
  return [fn, ln].filter(Boolean).join(' ') || `Row ${idx.value + 1}`
})

// ─── Phase helpers ────────────────────────────────────────────────────────────
function initEmployee() {
  const row = props.rows[idx.value]
  corrected.value = { ...row.data }
  submitError.value = ''

  // Skip correction if no issues
  if (row.status === 'valid') {
    password.value = generateEmployeePassword()
    phase.value = 'reviewing'
  } else {
    phase.value = 'correcting'
  }
}

onMounted(initEmployee)

function onCorrectionDone(data: Record<string, string>) {
  corrected.value = data
  password.value = generateEmployeePassword()
  phase.value = 'reviewing'
}

async function onSubmit(departmentId: string) {
  phase.value = 'submitting'
  submitError.value = ''

  try {
    // 1. Build payload and create employee
    const payload = buildEmployeePayload(corrected.value, departmentId || undefined)
    await createEmployeeRecord(payload)

    // 2. Create auth account — failure is non-fatal
    let accountCreated = false
    let accountNote = ''
    try {
      const companyId = localStorage.getItem('selected_company_id') ?? undefined
      await createUser({
        email: corrected.value.email,
        password: password.value,
        role: 'employee',
        ...(companyId ? { company_id: companyId } : {}),
      })
      accountCreated = true
    } catch (e: any) {
      accountNote = e.message ?? 'Account creation failed'
    }

    results.value.push({
      name: employeeName.value,
      email: corrected.value.email,
      status: 'imported',
      password: password.value,
      accountCreated,
      error: accountNote || undefined,
    })

    phase.value = 'success'

    // Auto-advance after 3 s
    autoTimer.value = setTimeout(advanceQueue, 3000)
  } catch (e: any) {
    submitError.value = e.message ?? 'Failed to create employee'
    results.value.push({
      name: employeeName.value,
      email: corrected.value.email ?? '',
      status: 'failed',
      error: submitError.value,
    })
    phase.value = 'error'
  }
}

function onSkip() {
  clearAutoTimer()
  results.value.push({
    name: employeeName.value,
    email: currentRow.value?.data?.email ?? '',
    status: 'skipped',
  })
  advanceQueue()
}

function advanceQueue() {
  clearAutoTimer()
  idx.value++
  if (!allDone.value) initEmployee()
}

function clearAutoTimer() {
  if (autoTimer.value) { clearTimeout(autoTimer.value); autoTimer.value = null }
}

// ─── Summary counts ───────────────────────────────────────────────────────────
const imported = computed(() => results.value.filter(r => r.status === 'imported').length)
const skipped  = computed(() => results.value.filter(r => r.status === 'skipped').length)
const failed   = computed(() => results.value.filter(r => r.status === 'failed').length)

// ─── Password copy on success card ───────────────────────────────────────────
const successCopied = ref(false)
async function copySuccessPwd() {
  const latest = results.value[results.value.length - 1]
  if (!latest?.password) return
  try {
    await navigator.clipboard.writeText(latest.password)
    successCopied.value = true
    setTimeout(() => { successCopied.value = false }, 2500)
  } catch {}
}
</script>

<template>
  <!-- Backdrop -->
  <div
    class="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="emit('close')"
  >
    <!-- Dialog card -->
    <div class="bg-white rounded-[24px] shadow-2xl w-full max-w-2xl max-h-[92vh] flex flex-col overflow-hidden">

      <!-- ── Header ── -->
      <div class="px-6 pt-5 pb-4 border-b border-slate-100 shrink-0">
        <div class="flex items-center justify-between mb-3">
          <div>
            <p class="text-xs text-slate-400 font-medium uppercase tracking-wider">
              {{ allDone ? 'Complete' : `Employee ${idx + 1} of ${rows.length}` }}
            </p>
            <h2 v-if="!allDone" class="text-base font-bold text-slate-900 mt-0.5">{{ employeeName }}</h2>
          </div>
          <button
            @click="emit('close')"
            class="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors"
          >
            <XIcon class="w-4 h-4" />
          </button>
        </div>

        <!-- Progress bar -->
        <div v-if="!allDone" class="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            class="h-full bg-slate-800 rounded-full transition-all duration-500"
            :style="{ width: `${progress}%` }"
          />
        </div>

        <!-- Phase tabs -->
        <div v-if="!allDone" class="flex items-center gap-3 mt-3">
          <span
            v-for="(label, p) in { correcting: 'Fix Issues', reviewing: 'Review', submitting: 'Saving…', success: 'Done', error: 'Error' }"
            :key="p"
            :class="[
              'text-xs font-medium px-2.5 py-0.5 rounded-full',
              phase === p
                ? 'bg-slate-900 text-white'
                : 'text-slate-400',
            ]"
          >{{ label }}</span>
        </div>
      </div>

      <!-- ── Body (scrollable) ── -->
      <div class="flex-1 overflow-y-auto px-6 py-5">

        <!-- ═══ ALL DONE: Summary ═══ -->
        <div v-if="allDone" class="space-y-5">
          <div class="text-center py-4">
            <CheckCircle2Icon class="w-12 h-12 text-emerald-500 mx-auto mb-3" />
            <h3 class="text-lg font-bold text-slate-900">Import Complete</h3>
            <p class="text-sm text-slate-500 mt-1">All employees in the queue have been processed.</p>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div class="text-center p-4 bg-emerald-50 rounded-[16px]">
              <p class="text-3xl font-bold text-emerald-700">{{ imported }}</p>
              <p class="text-xs text-emerald-600 mt-1">Imported</p>
            </div>
            <div class="text-center p-4 bg-amber-50 rounded-[16px]">
              <p class="text-3xl font-bold text-amber-600">{{ skipped }}</p>
              <p class="text-xs text-amber-500 mt-1">Skipped</p>
            </div>
            <div class="text-center p-4 bg-rose-50 rounded-[16px]">
              <p class="text-3xl font-bold text-rose-600">{{ failed }}</p>
              <p class="text-xs text-rose-500 mt-1">Failed</p>
            </div>
          </div>

          <!-- Per-employee result list -->
          <div class="rounded-[16px] border border-slate-200 overflow-hidden">
            <div v-for="(r, i) in results" :key="i"
                 class="flex items-center gap-3 px-4 py-2.5 border-b border-slate-100 last:border-0 text-sm">
              <span :class="[
                'w-2 h-2 rounded-full shrink-0',
                r.status === 'imported' ? 'bg-emerald-400'
                : r.status === 'skipped' ? 'bg-amber-400'
                : 'bg-rose-400',
              ]" />
              <span class="flex-1 font-medium text-slate-700">{{ r.name }}</span>
              <span class="text-xs text-slate-400">{{ r.email }}</span>
              <span :class="[
                'text-xs font-medium capitalize',
                r.status === 'imported' ? 'text-emerald-600'
                : r.status === 'skipped' ? 'text-amber-600'
                : 'text-rose-600',
              ]">{{ r.status }}</span>
            </div>
          </div>
        </div>

        <!-- ═══ CORRECTION STEP ═══ -->
        <EmployeeCorrectionStep
          v-else-if="phase === 'correcting'"
          :row="currentRow"
          :departments="departments"
          @done="onCorrectionDone"
        />

        <!-- ═══ REVIEW STEP ═══ -->
        <EmployeeReviewStep
          v-else-if="phase === 'reviewing' || phase === 'submitting'"
          :data="corrected"
          :departments="departments"
          :password="password"
          :loading="phase === 'submitting'"
          :submit-error="submitError"
          @submit="onSubmit"
          @skip="onSkip"
        />

        <!-- ═══ SUCCESS ═══ -->
        <div v-else-if="phase === 'success'" class="space-y-4">
          <div class="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 rounded-[16px]">
            <CheckCircle2Icon class="w-5 h-5 text-emerald-600 shrink-0" />
            <div>
              <p class="text-sm font-semibold text-emerald-800">{{ employeeName }} imported!</p>
              <p v-if="results[results.length-1]?.accountCreated === false" class="text-xs text-amber-700 mt-0.5">
                ⚠ Employee created but account setup failed: {{ results[results.length-1]?.error }}
              </p>
            </div>
          </div>

          <!-- Show password for copy one more time -->
          <div class="bg-slate-900 rounded-[16px] p-4">
            <p class="text-xs text-white/50 mb-2">Credentials for {{ corrected.email }}</p>
            <div class="flex items-center justify-between gap-3">
              <p class="text-sm text-amber-300 font-mono font-bold tracking-widest">{{ password }}</p>
              <button
                @click="copySuccessPwd"
                :class="[
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-[10px] text-xs font-medium transition-colors',
                  successCopied ? 'bg-emerald-500 text-white' : 'bg-white/20 text-white/70 hover:bg-white/30',
                ]"
              >
                <CheckIcon v-if="successCopied" class="w-3.5 h-3.5" />
                <CopyIcon v-else class="w-3.5 h-3.5" />
                {{ successCopied ? 'Copied!' : 'Copy' }}
              </button>
            </div>
          </div>

          <p class="text-xs text-slate-400 text-center">Auto-advancing to next employee in 3s…</p>
        </div>

        <!-- ═══ ERROR ═══ -->
        <div v-else-if="phase === 'error'" class="space-y-4">
          <div class="flex items-start gap-3 p-4 bg-rose-50 border border-rose-200 rounded-[16px]">
            <XCircleIcon class="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <p class="text-sm font-semibold text-rose-800">Failed to create {{ employeeName }}</p>
              <p class="text-xs text-rose-600 mt-1">{{ submitError }}</p>
            </div>
          </div>
        </div>

      </div>

      <!-- ── Footer ── -->
      <div v-if="!allDone" class="px-6 py-4 border-t border-slate-100 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-2 text-xs text-slate-400">
          <span class="text-emerald-600 font-medium">{{ imported }} saved</span>
          <span>·</span>
          <span class="text-amber-500">{{ skipped }} skipped</span>
          <span v-if="failed > 0">·</span>
          <span v-if="failed > 0" class="text-rose-500">{{ failed }} failed</span>
        </div>

        <div class="flex items-center gap-2">
          <button
            v-if="phase === 'success' || phase === 'error'"
            @click="advanceQueue"
            class="flex items-center gap-1.5 px-4 py-2 bg-slate-900 text-white rounded-full text-xs font-semibold hover:bg-slate-800 transition-colors"
          >
            Continue → Next
          </button>
          <button
            v-else-if="phase !== 'submitting'"
            @click="onSkip"
            class="flex items-center gap-1.5 px-4 py-2 border border-slate-200 text-slate-500 rounded-full text-xs hover:bg-slate-50 transition-colors"
          >
            <SkipForwardIcon class="w-3.5 h-3.5" /> Skip Employee
          </button>
        </div>
      </div>

      <!-- Footer: all done close -->
      <div v-else class="px-6 py-4 border-t border-slate-100 flex justify-end shrink-0">
        <button
          @click="emit('close')"
          class="flex items-center gap-2 px-5 py-2.5 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-colors"
        >
          <UsersIcon class="w-4 h-4" /> Done — Go to Directory
        </button>
      </div>

    </div>
  </div>
</template>
