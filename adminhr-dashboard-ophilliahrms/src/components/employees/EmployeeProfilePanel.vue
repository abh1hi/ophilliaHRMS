<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import EmployeeStatusBadge from './EmployeeStatusBadge.vue'
import AccountStatusBadge from './AccountStatusBadge.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import { Button } from '../ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar'
import { Card, CardContent } from '../ui/card'
import { Textarea } from '../ui/textarea'
import {
  sendEmployeeInvite, resendEmployeeInvite, revokeEmployeeInvite,
  disableEmployeeAccount, deleteEmployee,
} from '../../services/employee.service'
import type { Employee, SendInviteResponse } from '../../services/employee.service'
import {
  Pencil, Trash2, Mail, RefreshCw, XCircle,
  ShieldOff, User, Phone, Briefcase, Building,
  BookOpen, HeartPulse, CreditCard, ShieldAlert,
  BadgeCheck, ClipboardList, Copy, Check as CheckIcon,
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
  { key: 'overview',   label: 'Overview',        icon: User         },
  { key: 'job',        label: 'Job & Joining',   icon: Briefcase    },
  { key: 'contact',    label: 'Contact',          icon: Phone        },
  { key: 'banking',    label: 'Banking',          icon: CreditCard   },
  { key: 'ids',        label: 'Gov. IDs',         icon: BadgeCheck   },
  { key: 'emergency',  label: 'Emergency',        icon: ShieldAlert  },
  { key: 'education',  label: 'Education',        icon: BookOpen     },
  { key: 'experience', label: 'Experience',       icon: ClipboardList },
  { key: 'health',     label: 'Health',           icon: HeartPulse   },
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
      <div v-if="emp" class="space-y-8 -mt-2">

        <!-- ── Profile header ─────────────────────────────────────── -->
        <div class="flex flex-col sm:flex-row items-start gap-6">
          <Avatar class="w-24 h-24 rounded-2xl border border-border shadow-sm">
            <AvatarImage v-if="emp.staff_photo_url" :src="emp.staff_photo_url" :alt="fullName(emp)" class="object-cover" />
            <AvatarFallback class="bg-muted text-2xl font-bold text-muted-foreground rounded-2xl">
              {{ initials(emp) }}
            </AvatarFallback>
          </Avatar>

          <div class="flex-1 min-w-0 w-full">
            <div class="flex items-start justify-between gap-4">
              <div class="space-y-1">
                <h2 class="text-3xl font-bold tracking-tight text-foreground leading-none">{{ fullName(emp) }}</h2>
                <p class="text-sm font-medium text-muted-foreground">{{ fmt(emp.designation) }}</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                @click="emit('edit', emp)"
                class="rounded-full gap-2 px-4 shadow-sm"
              >
                <Pencil class="w-3.5 h-3.5" /> 
                <span class="hidden sm:inline">Edit Profile</span>
                <span class="sm:hidden text-[10px]">Edit</span>
              </Button>
            </div>

            <!-- Badges & meta -->
            <div class="flex flex-wrap items-center gap-2 mt-4">
              <span v-if="emp.employee_code" class="px-2.5 py-1 rounded-md bg-muted text-muted-foreground text-[10px] font-mono font-bold">
                {{ emp.employee_code }}
              </span>
              <EmployeeStatusBadge :status="emp.employment_status" />
              <AccountStatusBadge :status="emp.account_status" :expires-at="emp.invite_expires_at" />
            </div>

            <p class="text-[11px] font-medium text-muted-foreground/60 mt-2 uppercase tracking-tight">{{ fmt(emp.email) }}</p>
          </div>
        </div>

        <!-- ── Account Actions Card ─────────────────────────────────────── -->
        <Card class="bg-muted/30 border-dashed">
          <CardContent class="p-5">
            <h4 class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-4">Account Administration</h4>
            
            <div class="flex flex-wrap gap-3">
              <!-- Invites -->
              <Button
                v-if="emp.account_status === 'not_registered'"
                @click="sendInvite(false)"
                :disabled="inviting"
                size="sm"
                class="rounded-full gap-2 bg-blue-600 hover:bg-blue-700"
              >
                <Mail class="w-3.5 h-3.5" />
                {{ inviting ? 'Sending…' : 'Send Invite' }}
              </Button>

              <Button
                v-if="emp.account_status === 'invited'"
                @click="sendInvite(true)"
                :disabled="inviting"
                size="sm"
                class="rounded-full gap-2 bg-blue-600 hover:bg-blue-700"
              >
                <RefreshCw class="w-3.5 h-3.5" :class="inviting ? 'animate-spin' : ''" />
                {{ inviting ? 'Sending…' : 'Resend Invite' }}
              </Button>

              <Button
                v-if="emp.account_status === 'invited'"
                variant="outline"
                @click="showRevoke = true"
                size="sm"
                class="rounded-full gap-2 border-amber-200 text-amber-600 hover:bg-amber-50"
              >
                <XCircle class="w-3.5 h-3.5" /> Revoke Invite
              </Button>

              <!-- Access Control -->
              <Button
                v-if="emp.account_status === 'active'"
                variant="outline"
                @click="showDisable = true"
                size="sm"
                class="rounded-full gap-2 border-destructive/30 text-destructive hover:bg-destructive/5"
              >
                <ShieldOff class="w-3.5 h-3.5" /> Disable Access
              </Button>

              <div
                v-if="emp.account_status === 'suspended'"
                class="flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold text-muted-foreground bg-background border shadow-sm"
              >
                <ShieldOff class="w-3.5 h-3.5" /> Account Suspended
              </div>

              <!-- Delete (Dangerous) -->
              <Button
                variant="ghost"
                @click="showDelete = true"
                size="sm"
                class="rounded-full gap-2 text-destructive hover:bg-destructive/10 ml-auto"
              >
                <Trash2 class="w-3.5 h-3.5" /> Delete Record
              </Button>
            </div>
            
            <p v-if="actionError" class="text-[10px] text-destructive font-medium mt-3 px-1">{{ actionError }}</p>
          </CardContent>
        </Card>

        <!-- ── Segmented Navigation ────────────────────────────────────────── -->
        <Tabs v-model="activeSection" class="w-full">
          <div class="sticky top-0 bg-background/95 backdrop-blur z-20 -mx-6 px-6 pb-2 border-b">
            <TabsList class="flex w-full justify-start h-auto p-1 bg-muted/50 rounded-lg overflow-x-auto no-scrollbar">
              <TabsTrigger
                v-for="s in sections"
                :key="s.key"
                :value="s.key"
                class="gap-1.5 px-4 py-2 text-xs font-semibold rounded-md data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
              >
                <component :is="s.icon" class="w-3 h-3" />
                {{ s.label }}
              </TabsTrigger>
            </TabsList>
          </div>

          <div class="mt-8">
            <!-- OVERVIEW -->
            <TabsContent value="overview">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="info-item"><p class="info-label">Full Name</p><p class="info-value">{{ fullName(emp) }}</p></div>
                <div class="info-item"><p class="info-label">Work Email</p><p class="info-value break-all">{{ fmt(emp.email) }}</p></div>
                <div class="info-item"><p class="info-label">Gender</p><p class="info-value capitalize">{{ fmt(emp.gender) }}</p></div>
                <div class="info-item"><p class="info-label">Date of Birth</p><p class="info-value">{{ fmtDate(emp.date_of_birth) }}</p></div>
                <div class="info-item"><p class="info-label">Primary Phone</p><p class="info-value">{{ fmt(emp.phone) }}</p></div>
                <div class="info-item"><p class="info-label">Personal Email</p><p class="info-value break-all">{{ fmt(emp.personal_email) }}</p></div>
                <div class="info-item sm:col-span-2">
                  <p class="info-label">Current Address</p>
                  <p class="info-value">{{ [emp.door_no, emp.street, emp.village_town, emp.pin_code].filter(Boolean).join(', ') || '—' }}</p>
                </div>
              </div>
            </TabsContent>

            <!-- JOB & JOINING -->
            <TabsContent value="job">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="info-item"><p class="info-label">Date Joined</p><p class="info-value">{{ fmtDate(emp.date_joined) }}</p></div>
                <div class="info-item">
                  <p class="info-label">Designation</p>
                  <p class="info-value">{{ emp.designation_rel?.name || emp.designation || '—' }}</p>
                </div>
                <div class="info-item">
                  <p class="info-label">Department</p>
                  <p class="info-value">{{ emp.department?.name || emp.department_id || '—' }}</p>
                </div>
                <div class="info-item">
                  <p class="info-label">Grade</p>
                  <p class="info-value">{{ emp.grade?.name || '—' }}</p>
                </div>
                <div class="info-item">
                  <p class="info-label">Branch</p>
                  <p class="info-value">{{ emp.branch?.name || '—' }}</p>
                </div>
                <div class="info-item">
                  <p class="info-label">Employment Status</p>
                  <EmployeeStatusBadge :status="emp.employment_status" />
                </div>
                <div class="info-item"><p class="info-label">Role Authority</p><p class="info-value capitalize">{{ fmt(emp.role) }}</p></div>
                <div class="info-item"><p class="info-label">Primary Project</p><p class="info-value">{{ fmt(emp.project) }}</p></div>
                <div class="info-item"><p class="info-label">Starting Salary</p><p class="info-value">{{ fmtCurrency(emp.joining_salary) }}</p></div>
                <div class="info-item"><p class="info-label">Internal Code</p><p class="info-value font-mono">{{ fmt(emp.employee_code) }}</p></div>
              </div>
            </TabsContent>

            <!-- CONTACT -->
            <TabsContent value="contact">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="info-item"><p class="info-label">Primary Phone</p><p class="info-value">{{ fmt(emp.phone) }}</p></div>
                <div class="info-item"><p class="info-label">Secondary Phone</p><p class="info-value">{{ fmt(emp.phone_2) }}</p></div>
                <div class="info-item sm:col-span-2"><p class="info-label">Personal Email</p><p class="info-value break-all">{{ fmt(emp.personal_email) }}</p></div>
                <div class="info-item"><p class="info-label">Door No.</p><p class="info-value">{{ fmt(emp.door_no) }}</p></div>
                <div class="info-item"><p class="info-label">Street</p><p class="info-value">{{ fmt(emp.street) }}</p></div>
                <div class="info-item"><p class="info-label">Village / Town</p><p class="info-value">{{ fmt(emp.village_town) }}</p></div>
                <div class="info-item"><p class="info-label">PIN Code</p><p class="info-value font-mono">{{ fmt(emp.pin_code) }}</p></div>
              </div>
            </TabsContent>

            <!-- BANKING -->
            <TabsContent value="banking">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="info-item sm:col-span-2"><p class="info-label">Financial Institution</p><p class="info-value">{{ fmt(emp.bank_name) }}</p></div>
                <div class="info-item"><p class="info-label">Branch Location</p><p class="info-value">{{ fmt(emp.bank_branch) }}</p></div>
                <div class="info-item"><p class="info-label">IFSC Routine Code</p><p class="info-value font-mono">{{ fmt(emp.ifsc_code) }}</p></div>
                <div class="info-item sm:col-span-2">
                  <p class="info-label">Account Number (Secured)</p>
                  <p class="info-value font-mono tracking-widest">{{ mask(emp.bank_account_number) }}</p>
                </div>
              </div>
            </TabsContent>

            <!-- GOV IDs -->
            <TabsContent value="ids">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="info-item"><p class="info-label">Aadhaar (Secured)</p><p class="info-value font-mono">{{ mask(emp.aadhaar_number) }}</p></div>
                <div class="info-item"><p class="info-label">Permanent Account No (PAN)</p><p class="info-value font-mono">{{ fmt(emp.pan_number) }}</p></div>
                <div class="info-item"><p class="info-label">UAN Registration</p><p class="info-value font-mono">{{ fmt(emp.uan_number) }}</p></div>
                <div class="info-item"><p class="info-label">ESI Coverage No.</p><p class="info-value font-mono">{{ fmt(emp.esi_number) }}</p></div>
                <div class="info-item sm:col-span-2"><p class="info-label">Driver License</p><p class="info-value font-mono">{{ fmt(emp.driving_license_number) }}</p></div>
              </div>
            </TabsContent>

            <!-- EMERGENCY -->
            <TabsContent value="emergency">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="info-item sm:col-span-2"><p class="info-label">Emergency Contact Name</p><p class="info-value">{{ fmt(emp.emergency_contact_name) }}</p></div>
                <div class="info-item"><p class="info-label">Contact Phone</p><p class="info-value">{{ fmt(emp.emergency_contact_number) }}</p></div>
                <div class="info-item"><p class="info-label">Relationship</p><p class="info-value capitalize">{{ fmt(emp.emergency_contact_relation) }}</p></div>
              </div>
            </TabsContent>

            <!-- EDUCATION -->
            <TabsContent value="education">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="info-item sm:col-span-2"><p class="info-label">Highest Credential</p><p class="info-value">{{ fmt(emp.highest_qualification) }}</p></div>
                <div class="info-item sm:col-span-2"><p class="info-label">Institution / University</p><p class="info-value">{{ fmt(emp.institute_name) }}</p></div>
                <div class="info-item"><p class="info-label">Passing Year</p><p class="info-value">{{ fmt(emp.year_of_passing) }}</p></div>
                <div class="info-item"><p class="info-label">Score (Grade/%)</p><p class="info-value">{{ fmt(emp.percentage) }}</p></div>
              </div>
            </TabsContent>

            <!-- EXPERIENCE -->
            <TabsContent value="experience">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="info-item sm:col-span-2"><p class="info-label">Last Organization</p><p class="info-value">{{ fmt(emp.last_firm_name) }}</p></div>
                <div class="info-item"><p class="info-label">Last Designation</p><p class="info-value">{{ fmt(emp.last_designation) }}</p></div>
                <div class="info-item"><p class="info-label">Tenure (Years)</p><p class="info-value">{{ fmt(emp.years_of_experience) }}</p></div>
                <div class="info-item"><p class="info-label">Final Drawn Salary</p><p class="info-value">{{ fmtCurrency(emp.last_drawn_salary) }}</p></div>
                <div class="info-item"><p class="info-label">Internal Referral</p><p class="info-value">{{ fmt(emp.referred_by) }}</p></div>
                <div class="info-item sm:col-span-2"><p class="info-label">Transition Context</p><p class="info-value">{{ fmt(emp.reason_to_quit) }}</p></div>
              </div>
            </TabsContent>

            <!-- HEALTH -->
            <TabsContent value="health">
              <div class="grid grid-cols-1 gap-4">
                <div class="info-item"><p class="info-label">Known Health Conditions</p><p class="info-value whitespace-pre-line">{{ fmt(emp.health_issues) }}</p></div>
                <div class="info-item"><p class="info-label">Allergies / Critical Alerts</p><p class="info-value whitespace-pre-line text-destructive font-semibold">{{ fmt(emp.allergies) }}</p></div>
              </div>
            </TabsContent>
          </div>
        </Tabs>

        <!-- Timestamps -->
        <div class="pt-8 border-t flex justify-between items-center text-[10px] text-muted-foreground/50 italic tracking-tight">
          <span>Added: {{ fmtDate(emp.created_at) }}</span>
          <span>Last Synchronized: {{ fmtDate(emp.updated_at) }}</span>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="flex flex-col items-center justify-center h-64 text-muted-foreground opacity-50 space-y-2">
        <User class="w-12 h-12 stroke-[1]" />
        <p class="text-sm">No profile data currently available</p>
      </div>
    </template>
  </SlideDrawer>

  <!-- Confirm Dialogs -->
  <ConfirmDialog
    :open="showRevoke"
    title="Revoke Identity Invite?"
    :message="`This will invalidate the current invitation for ${fullName(emp!)}. Are you sure?`"
    :loading="revoking"
    @confirm="doRevoke"
    @cancel="showRevoke = false"
  />
  <ConfirmDialog
    :open="showDisable"
    title="Disable Platform Access?"
    :message="`This will immediately revoke login access for ${fullName(emp!)}. Core records will be preserved.`"
    :loading="disabling"
    @confirm="doDisable"
    @cancel="showDisable = false"
  />
  <ConfirmDialog
    :open="showDelete"
    title="Permanent Deletion"
    :message="`Deleting ${fullName(emp!)} is irreversible. All attendance, leave, and payroll history will be purged.`"
    :loading="deleting"
    confirm-label="Confirm Purge"
    @confirm="doDelete"
    @cancel="showDelete = false"
  />

  <!-- Invite Link Modal (Shadcn Dialog) -->
  <Dialog :open="showInviteModal" @update:open="showInviteModal = $event">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>Invite Securely Generated</DialogTitle>
        <DialogDescription v-if="inviteResult">
          Transmit this secure token to <span class="font-bold text-foreground">{{ inviteResult.email }}</span>. 
          Availability expires on <span class="text-foreground">{{ inviteResult.expires_at ? new Date(inviteResult.expires_at).toLocaleDateString() : '7 days from now' }}</span>.
        </DialogDescription>
      </DialogHeader>
      
      <div class="mt-4" v-if="inviteResult">
        <Textarea
          readonly
          :value="inviteResult.invite_url"
          rows="3"
          class="font-mono text-xs bg-muted resize-none focus-visible:ring-0"
        />
      </div>

      <DialogFooter class="flex flex-col sm:flex-row justify-end gap-2 mt-4">
        <Button variant="ghost" @click="showInviteModal = false">
          Dismiss
        </Button>
        <Button @click="copyInviteUrl" class="gap-2 px-6">
          <CheckIcon v-if="copySuccess" class="w-4 h-4" />
          <Copy v-else class="w-4 h-4" />
          {{ copySuccess ? 'Copied Token' : 'Copy Access Link' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

.info-item {
  @apply p-4 rounded-xl border border-transparent bg-muted/30 transition-colors hover:bg-muted/50 select-none;
}
.info-label {
  @apply text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1 opacity-70;
}
.info-value {
  @apply text-sm font-semibold text-foreground leading-tight;
}
</style>
