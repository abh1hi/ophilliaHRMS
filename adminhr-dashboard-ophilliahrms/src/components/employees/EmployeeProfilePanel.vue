<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import EmployeeStatusBadge from './EmployeeStatusBadge.vue'
import AccountStatusBadge from './AccountStatusBadge.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import {
  sendEmployeeInvite, resendEmployeeInvite, revokeEmployeeInvite,
  disableEmployeeAccount, deleteEmployee,
} from '../../services/employee.service'
import type { Employee, SendInviteResponse } from '../../services/employee.service'
import {
  PencilIcon, Trash2Icon, MailIcon, RefreshCwIcon, XCircleIcon,
  ShieldOffIcon, UserIcon, PhoneIcon, BriefcaseIcon, BuildingIcon,
  BookOpenIcon, HeartPulseIcon, CreditCardIcon, ShieldAlertIcon,
  BadgeCheckIcon, ClipboardListIcon, CopyIcon, CheckIcon,
} from 'lucide-vue-next'

const props = defineProps<{
  open: boolean
  employee: Employee | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit', emp: Employee): void
  (e: 'deleted'): void
  (e: 'updated'): void
}>()

// ── Invite state ─────────────────────────────────────────────────────────────
const inviting       = ref(false)
const inviteResult   = ref<SendInviteResponse | null>(null)
const showInviteModal = ref(false)
const copySuccess    = ref(false)

// ── Revoke / Disable / Delete state ──────────────────────────────────────────
const showRevoke  = ref(false)
const revoking    = ref(false)
const showDisable = ref(false)
const disabling   = ref(false)
const showDelete  = ref(false)
const deleting    = ref(false)

const actionError = ref('')

// Active section tab
const activeSection = ref('overview')
const sections = [
  { key: 'overview',   label: 'Overview',        icon: UserIcon         },
  { key: 'job',        label: 'Job & Joining',   icon: BriefcaseIcon    },
  { key: 'contact',    label: 'Contact',          icon: PhoneIcon        },
  { key: 'banking',    label: 'Banking',          icon: CreditCardIcon   },
  { key: 'ids',        label: 'Gov. IDs',         icon: BadgeCheckIcon   },
  { key: 'emergency',  label: 'Emergency',        icon: ShieldAlertIcon  },
  { key: 'education',  label: 'Education',        icon: BookOpenIcon     },
  { key: 'experience', label: 'Experience',       icon: ClipboardListIcon },
  { key: 'health',     label: 'Health',           icon: HeartPulseIcon   },
]

watch(() => props.open, (val) => {
  if (val) { activeSection.value = 'overview'; actionError.value = '' }
})

// ── Helpers ───────────────────────────────────────────────────────────────────
const emp = computed(() => props.employee)

function fullName(e: Employee | null) {
  if (!e) return '—'
  return `${e.first_name ?? ''} ${e.last_name ?? ''}`.trim()
}

function initials(e: Employee | null) {
  if (!e) return ''
  return (e.first_name?.[0] ?? '') + (e.last_name?.[0] ?? '')
}

function fmt(val: string | number | null | undefined, fallback = '—') {
  if (val === null || val === undefined || val === '') return fallback
  return String(val)
}

function fmtDate(val: string | null | undefined) {
  if (!val) return '—'
  try { return new Date(val).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) }
  catch { return val }
}

function fmtCurrency(val: string | number | null | undefined) {
  if (!val) return '—'
  const n = Number(val)
  if (isNaN(n)) return String(val)
  return '₹ ' + n.toLocaleString('en-IN')
}

function mask(val: string | null | undefined, keep = 4) {
  if (!val) return '—'
  if (val.length <= keep) return val
  return '•'.repeat(val.length - keep) + val.slice(-keep)
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function sendInvite(isResend = false) {
  if (!emp.value) return
  inviting.value = true
  actionError.value = ''
  try {
    const result = isResend
      ? await resendEmployeeInvite(emp.value.id)
      : await sendEmployeeInvite(emp.value.id)
    inviteResult.value = result
    showInviteModal.value = true
    emit('updated')
  } catch (e: any) {
    actionError.value = e.message ?? 'Failed to send invite'
  } finally {
    inviting.value = false
  }
}

async function doRevoke() {
  if (!emp.value) return
  revoking.value = true
  try { await revokeEmployeeInvite(emp.value.id); showRevoke.value = false; emit('updated') }
  catch (e: any) { actionError.value = e.message ?? 'Revoke failed' }
  finally { revoking.value = false }
}

async function doDisable() {
  if (!emp.value) return
  disabling.value = true
  try { await disableEmployeeAccount(emp.value.id); showDisable.value = false; emit('updated') }
  catch (e: any) { actionError.value = e.message ?? 'Disable failed' }
  finally { disabling.value = false }
}

async function doDelete() {
  if (!emp.value) return
  deleting.value = true
  try { await deleteEmployee(emp.value.id); showDelete.value = false; emit('deleted') }
  catch (e: any) { actionError.value = e.message ?? 'Delete failed' }
  finally { deleting.value = false }
}

async function copyInviteUrl() {
  if (!inviteResult.value?.invite_url) return
  await navigator.clipboard.writeText(inviteResult.value.invite_url).catch(() => {})
  copySuccess.value = true
  setTimeout(() => { copySuccess.value = false }, 2000)
}
</script>

<template>
  <SlideDrawer
    :open="open"
    title=""
    width="w-full max-w-2xl"
    @close="emit('close')"
  >
    <template #default>
      <div v-if="emp" class="space-y-6 -mt-2">

        <!-- ── Profile header ─────────────────────────────────────── -->
        <div class="flex items-start gap-5">
          <!-- Avatar -->
          <div v-if="emp.staff_photo_url" class="w-20 h-20 rounded-2xl overflow-hidden shrink-0 border border-slate-200">
            <img :src="emp.staff_photo_url" :alt="fullName(emp)" class="w-full h-full object-cover" />
          </div>
          <div v-else class="w-20 h-20 rounded-2xl bg-slate-100 flex items-center justify-center text-2xl font-bold text-slate-500 shrink-0 border border-slate-200">
            {{ initials(emp) }}
          </div>

          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-2">
              <div>
                <h2 class="text-xl font-bold text-slate-900 leading-tight">{{ fullName(emp) }}</h2>
                <p class="text-sm text-slate-500 mt-0.5">{{ fmt(emp.designation) }}</p>
              </div>
              <!-- Edit button -->
              <button
                @click="emit('edit', emp)"
                class="flex items-center gap-1.5 px-3.5 py-1.5 border border-slate-200 rounded-full text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors shrink-0"
              >
                <PencilIcon class="w-3.5 h-3.5" /> Edit Profile
              </button>
            </div>

            <!-- Badges & meta -->
            <div class="flex flex-wrap items-center gap-2 mt-3">
              <span v-if="emp.employee_code" class="px-2.5 py-1 rounded-md bg-slate-100 text-slate-600 text-xs font-mono font-semibold">
                {{ emp.employee_code }}
              </span>
              <EmployeeStatusBadge :status="emp.employment_status" />
              <AccountStatusBadge :status="emp.account_status" :expires-at="emp.invite_expires_at" />
            </div>

            <p class="text-xs text-slate-400 mt-2">{{ fmt(emp.email) }}</p>
          </div>
        </div>

        <!-- ── Action buttons ─────────────────────────────────────── -->
        <div class="flex flex-wrap gap-2 p-4 bg-slate-50 rounded-2xl border border-slate-200/70">
          <p class="w-full text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Account Actions</p>

          <!-- Send Invite -->
          <button
            v-if="emp.account_status === 'not_registered'"
            @click="sendInvite(false)"
            :disabled="inviting"
            class="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <MailIcon class="w-3.5 h-3.5" />
            {{ inviting ? 'Sending…' : 'Send Invite' }}
          </button>

          <!-- Resend Invite -->
          <button
            v-if="emp.account_status === 'invited'"
            @click="sendInvite(true)"
            :disabled="inviting"
            class="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <RefreshCwIcon class="w-3.5 h-3.5" />
            {{ inviting ? 'Sending…' : 'Resend Invite' }}
          </button>

          <!-- Revoke Invite -->
          <button
            v-if="emp.account_status === 'invited'"
            @click="showRevoke = true"
            class="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium border border-amber-300 text-amber-700 bg-amber-50 hover:bg-amber-100 transition-colors"
          >
            <XCircleIcon class="w-3.5 h-3.5" /> Revoke Invite
          </button>

          <!-- Disable Account -->
          <button
            v-if="emp.account_status === 'active'"
            @click="showDisable = true"
            class="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium border border-rose-300 text-rose-700 bg-rose-50 hover:bg-rose-100 transition-colors"
          >
            <ShieldOffIcon class="w-3.5 h-3.5" /> Disable Account
          </button>

          <!-- Suspended label -->
          <span
            v-if="emp.account_status === 'suspended'"
            class="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium text-slate-500 bg-white border border-slate-200"
          >
            <ShieldOffIcon class="w-3.5 h-3.5" /> Account Suspended
          </span>

          <!-- Debug: if no status matches -->
          <span
            v-if="!['not_registered', 'invited', 'active', 'suspended'].includes(emp.account_status)"
            class="text-xs text-rose-600"
          >
            Account Status: {{ emp.account_status || '(not set)' }}
          </span>

          <!-- Delete -->
          <button
            @click="showDelete = true"
            class="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium border border-rose-200 text-rose-600 bg-white hover:bg-rose-50 transition-colors ml-auto"
          >
            <Trash2Icon class="w-3.5 h-3.5" /> Delete
          </button>

          <!-- Error -->
          <p v-if="actionError" class="w-full text-xs text-rose-600 mt-1">{{ actionError }}</p>
        </div>

        <!-- ── Section Tabs ────────────────────────────────────────── -->
        <div class="flex flex-wrap gap-1.5 -mb-2">
          <button
            v-for="s in sections"
            :key="s.key"
            @click="activeSection = s.key"
            :class="[
              'flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all',
              activeSection === s.key
                ? 'bg-slate-900 text-white'
                : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
            ]"
          >
            <component :is="s.icon" class="w-3.5 h-3.5" />
            {{ s.label }}
          </button>
        </div>

        <!-- ── OVERVIEW ────────────────────────────────────────────── -->
        <div v-if="activeSection === 'overview'" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="info-card"><p class="info-label">Full Name</p><p class="info-value">{{ fullName(emp) }}</p></div>
            <div class="info-card"><p class="info-label">Work Email</p><p class="info-value break-all">{{ fmt(emp.email) }}</p></div>
            <div class="info-card"><p class="info-label">Gender</p><p class="info-value capitalize">{{ fmt(emp.gender) }}</p></div>
            <div class="info-card"><p class="info-label">Date of Birth</p><p class="info-value">{{ fmtDate(emp.date_of_birth) }}</p></div>
            <div class="info-card"><p class="info-label">Phone</p><p class="info-value">{{ fmt(emp.phone) }}</p></div>
            <div class="info-card"><p class="info-label">Personal Email</p><p class="info-value break-all">{{ fmt(emp.personal_email) }}</p></div>
            <div class="info-card col-span-2"><p class="info-label">Address</p>
              <p class="info-value">{{ [emp.door_no, emp.street, emp.village_town, emp.pin_code].filter(Boolean).join(', ') || '—' }}</p>
            </div>
          </div>
        </div>

        <!-- ── JOB & JOINING ──────────────────────────────────────── -->
        <div v-if="activeSection === 'job'" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="info-card"><p class="info-label">Date Joined</p><p class="info-value">{{ fmtDate(emp.date_joined) }}</p></div>
            <div class="info-card"><p class="info-label">Designation</p><p class="info-value">{{ fmt(emp.designation) }}</p></div>
            <div class="info-card"><p class="info-label">Department</p><p class="info-value">{{ fmt(emp.department) }}</p></div>
            <div class="info-card"><p class="info-label">Employment Status</p>
              <EmployeeStatusBadge :status="emp.employment_status" />
            </div>
            <div class="info-card"><p class="info-label">Role</p><p class="info-value capitalize">{{ fmt(emp.role) }}</p></div>
            <div class="info-card"><p class="info-label">Project</p><p class="info-value">{{ fmt(emp.project) }}</p></div>
            <div class="info-card"><p class="info-label">Joining Salary</p><p class="info-value">{{ fmtCurrency(emp.joining_salary) }}</p></div>
            <div class="info-card"><p class="info-label">Employee Code</p><p class="info-value font-mono">{{ fmt(emp.employee_code) }}</p></div>
          </div>
        </div>

        <!-- ── CONTACT ─────────────────────────────────────────────── -->
        <div v-if="activeSection === 'contact'" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="info-card"><p class="info-label">Primary Phone</p><p class="info-value">{{ fmt(emp.phone) }}</p></div>
            <div class="info-card"><p class="info-label">Secondary Phone</p><p class="info-value">{{ fmt(emp.phone_2) }}</p></div>
            <div class="info-card col-span-2"><p class="info-label">Personal Email</p><p class="info-value break-all">{{ fmt(emp.personal_email) }}</p></div>
            <div class="info-card"><p class="info-label">Door No.</p><p class="info-value">{{ fmt(emp.door_no) }}</p></div>
            <div class="info-card"><p class="info-label">Street</p><p class="info-value">{{ fmt(emp.street) }}</p></div>
            <div class="info-card"><p class="info-label">Village / Town</p><p class="info-value">{{ fmt(emp.village_town) }}</p></div>
            <div class="info-card"><p class="info-label">PIN Code</p><p class="info-value font-mono">{{ fmt(emp.pin_code) }}</p></div>
          </div>
        </div>

        <!-- ── BANKING ─────────────────────────────────────────────── -->
        <div v-if="activeSection === 'banking'" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="info-card col-span-2"><p class="info-label">Bank Name</p><p class="info-value">{{ fmt(emp.bank_name) }}</p></div>
            <div class="info-card"><p class="info-label">Branch</p><p class="info-value">{{ fmt(emp.bank_branch) }}</p></div>
            <div class="info-card"><p class="info-label">IFSC Code</p><p class="info-value font-mono">{{ fmt(emp.ifsc_code) }}</p></div>
            <div class="info-card col-span-2"><p class="info-label">Account Number</p>
              <p class="info-value font-mono tracking-wider">{{ mask(emp.bank_account_number) }}</p>
            </div>
          </div>
        </div>

        <!-- ── GOVERNMENT IDs ──────────────────────────────────────── -->
        <div v-if="activeSection === 'ids'" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="info-card"><p class="info-label">Aadhaar Number</p><p class="info-value font-mono">{{ mask(emp.aadhaar_number) }}</p></div>
            <div class="info-card"><p class="info-label">PAN Number</p><p class="info-value font-mono">{{ fmt(emp.pan_number) }}</p></div>
            <div class="info-card"><p class="info-label">UAN Number</p><p class="info-value font-mono">{{ fmt(emp.uan_number) }}</p></div>
            <div class="info-card"><p class="info-label">ESI Number</p><p class="info-value font-mono">{{ fmt(emp.esi_number) }}</p></div>
            <div class="info-card col-span-2"><p class="info-label">Driving License</p><p class="info-value font-mono">{{ fmt(emp.driving_license_number) }}</p></div>
          </div>
        </div>

        <!-- ── EMERGENCY ───────────────────────────────────────────── -->
        <div v-if="activeSection === 'emergency'" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="info-card col-span-2"><p class="info-label">Contact Name</p><p class="info-value">{{ fmt(emp.emergency_contact_name) }}</p></div>
            <div class="info-card"><p class="info-label">Phone</p><p class="info-value">{{ fmt(emp.emergency_contact_number) }}</p></div>
            <div class="info-card"><p class="info-label">Relation</p><p class="info-value capitalize">{{ fmt(emp.emergency_contact_relation) }}</p></div>
          </div>
        </div>

        <!-- ── EDUCATION ───────────────────────────────────────────── -->
        <div v-if="activeSection === 'education'" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="info-card col-span-2"><p class="info-label">Highest Qualification</p><p class="info-value">{{ fmt(emp.highest_qualification) }}</p></div>
            <div class="info-card col-span-2"><p class="info-label">Institute / University</p><p class="info-value">{{ fmt(emp.institute_name) }}</p></div>
            <div class="info-card"><p class="info-label">Year of Passing</p><p class="info-value">{{ fmt(emp.year_of_passing) }}</p></div>
            <div class="info-card"><p class="info-label">Percentage / CGPA</p><p class="info-value">{{ fmt(emp.percentage) }}</p></div>
          </div>
        </div>

        <!-- ── EXPERIENCE ──────────────────────────────────────────── -->
        <div v-if="activeSection === 'experience'" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="info-card col-span-2"><p class="info-label">Previous Employer</p><p class="info-value">{{ fmt(emp.last_firm_name) }}</p></div>
            <div class="info-card"><p class="info-label">Last Designation</p><p class="info-value">{{ fmt(emp.last_designation) }}</p></div>
            <div class="info-card"><p class="info-label">Years of Experience</p><p class="info-value">{{ fmt(emp.years_of_experience) }}</p></div>
            <div class="info-card"><p class="info-label">Last Drawn Salary</p><p class="info-value">{{ fmtCurrency(emp.last_drawn_salary) }}</p></div>
            <div class="info-card"><p class="info-label">Referred By</p><p class="info-value">{{ fmt(emp.referred_by) }}</p></div>
            <div class="info-card col-span-2"><p class="info-label">Reason to Quit</p><p class="info-value">{{ fmt(emp.reason_to_quit) }}</p></div>
          </div>
        </div>

        <!-- ── HEALTH ──────────────────────────────────────────────── -->
        <div v-if="activeSection === 'health'" class="space-y-4">
          <div class="grid grid-cols-1 gap-3">
            <div class="info-card"><p class="info-label">Health Issues</p><p class="info-value whitespace-pre-line">{{ fmt(emp.health_issues) }}</p></div>
            <div class="info-card"><p class="info-label">Allergies</p><p class="info-value whitespace-pre-line">{{ fmt(emp.allergies) }}</p></div>
          </div>
        </div>

        <!-- Timestamps -->
        <p class="text-[11px] text-slate-300 text-right">
          Added {{ fmtDate(emp.created_at) }} · Updated {{ fmtDate(emp.updated_at) }}
        </p>
      </div>

      <!-- Empty state -->
      <div v-else class="flex items-center justify-center h-48 text-slate-400 text-sm">
        No employee selected.
      </div>
    </template>
  </SlideDrawer>

  <!-- Confirm Dialogs -->
  <ConfirmDialog
    :open="showRevoke"
    title="Revoke Invite?"
    :message="`Cancel the pending invite for ${fullName(emp!)}. They won't be able to use the current invite link.`"
    :loading="revoking"
    @confirm="doRevoke"
    @cancel="showRevoke = false"
  />
  <ConfirmDialog
    :open="showDisable"
    title="Disable Portal Access?"
    :message="`This will revoke ${fullName(emp!)}'s login access. Their HR record will remain intact.`"
    :loading="disabling"
    @confirm="doDisable"
    @cancel="showDisable = false"
  />
  <ConfirmDialog
    :open="showDelete"
    title="Delete Employee?"
    :message="`This will permanently delete ${fullName(emp!)} and all associated records. This cannot be undone.`"
    :loading="deleting"
    confirm-label="Delete"
    @confirm="doDelete"
    @cancel="showDelete = false"
  />

  <!-- Invite Link Modal -->
  <div
    v-if="showInviteModal && inviteResult"
    class="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 backdrop-blur-sm"
    @click.self="showInviteModal = false"
  >
    <div class="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md mx-4 space-y-4">
      <h3 class="text-base font-semibold text-slate-800">Invite Link Ready</h3>
      <p class="text-sm text-slate-500">
        Share this link with <strong>{{ inviteResult.email }}</strong>. Expires on
        <strong>{{ inviteResult.expires_at ? new Date(inviteResult.expires_at).toLocaleDateString() : '7 days from now' }}</strong>.
      </p>
      <textarea
        readonly
        :value="inviteResult.invite_url"
        rows="3"
        class="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-3 resize-none text-slate-700 focus:outline-none"
      />
      <div class="flex justify-end gap-3">
        <button @click="showInviteModal = false" class="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 transition-colors">
          Close
        </button>
        <button
          @click="copyInviteUrl"
          class="flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-slate-900 text-white rounded-full hover:bg-slate-700 transition-colors"
        >
          <component :is="copySuccess ? CheckIcon : CopyIcon" class="w-4 h-4" />
          {{ copySuccess ? 'Copied!' : 'Copy Link' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.info-card {
  @apply bg-slate-50/80 border border-slate-100 rounded-[14px] px-4 py-3;
}
.info-label {
  @apply text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1;
}
.info-value {
  @apply text-sm text-slate-800 font-medium;
}
</style>
