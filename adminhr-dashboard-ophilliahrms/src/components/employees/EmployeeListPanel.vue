<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import EmployeeDrawer from './EmployeeDrawer.vue'
import EmployeeProfilePanel from './EmployeeProfilePanel.vue'
import EmployeeStatusBadge from './EmployeeStatusBadge.vue'
import AccountStatusBadge from './AccountStatusBadge.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Button } from '../ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog'
import { Textarea } from '../ui/textarea'
import {
  listEmployees, deleteEmployee,
  sendEmployeeInvite, resendEmployeeInvite, revokeEmployeeInvite, disableEmployeeAccount,
} from '../../services/employee.service'
import type { Employee, SendInviteResponse } from '../../services/employee.service'
import { 
  Pencil, 
  Trash2, 
  RefreshCw, 
  Mail, 
  ShieldOff, 
  XCircle,
  Copy,
  Check as CheckIcon
} from 'lucide-vue-next'

const employees    = ref<Employee[]>([])
const total        = ref(0)
const loading      = ref(false)
const page         = ref(1)
const search       = ref('')
const statusFilter = ref('')
const accountFilter = ref('')
const drawerOpen   = ref(false)
const selected     = ref<Employee | null>(null)
const deleteTarget = ref<Employee | null>(null)
const deleting     = ref(false)

// Profile panel
const profileOpen     = ref(false)
const profileEmployee = ref<Employee | null>(null)

// Invite state
const inviteTarget  = ref<Employee | null>(null)
const inviteResult  = ref<SendInviteResponse | null>(null)
const inviting      = ref(false)
const showInviteModal = ref(false)
const copySuccess   = ref(false)

// Revoke state
const revokeTarget = ref<Employee | null>(null)
const revoking     = ref(false)

// Disable state
const disableTarget = ref<Employee | null>(null)
const disabling     = ref(false)

const columns = [
  { key: 'employee_code',    label: 'Code'        },
  { key: 'name',             label: 'Name'        },
  { key: 'email',            label: 'Email'       },
  { key: 'department',       label: 'Department'  },
  { key: 'designation',      label: 'Designation' },
  { key: 'employment_status', label: 'Status'     },
  { key: 'account_status',   label: 'Account'     },
]

const statusOptions = [
  { value: '',           label: 'All Statuses'  },
  { value: 'active',     label: 'Active'        },
  { value: 'inactive',   label: 'Inactive'      },
  { value: 'terminated', label: 'Terminated'    },
]

const accountStatusOptions = [
  { value: '',               label: 'All Accounts'   },
  { value: 'not_registered', label: 'Not Registered' },
  { value: 'invited',        label: 'Invite Sent'    },
  { value: 'active',         label: 'Active'         },
  { value: 'suspended',      label: 'Suspended'      },
]

async function load() {
  loading.value = true
  try {
    const result = await listEmployees({
      page: page.value,
      page_size: 10,
      search: search.value || undefined,
      employment_status: statusFilter.value || undefined,
      account_status: accountFilter.value || undefined,
    } as any)
    employees.value = result.data
    total.value = result.meta?.total_items ?? result.data.length
  } catch (err) {
    console.error('Failed to load employees', err)
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch([page, statusFilter, accountFilter], load)

function onSearch(q: string) { search.value = q; page.value = 1; load() }
function openCreate() { selected.value = null; drawerOpen.value = true }
function openEdit(emp: Employee) { profileOpen.value = false; selected.value = emp; drawerOpen.value = true }
function openProfile(emp: Employee) { profileEmployee.value = emp; profileOpen.value = true }
function onSaved() { load() }

async function onProfileUpdated() {
  await load()
  // Refresh the profile employee so badges update immediately
  if (profileEmployee.value) {
    const refreshed = employees.value.find(e => e.id === profileEmployee.value!.id)
    if (refreshed) profileEmployee.value = refreshed
  }
}
function onProfileDeleted() {
  profileOpen.value = false
  profileEmployee.value = null
  load()
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try { await deleteEmployee(deleteTarget.value.id); deleteTarget.value = null; load() }
  catch (err) { console.error('Delete failed', err) }
  finally { deleting.value = false }
}

async function confirmSendInvite(emp: Employee, isResend = false) {
  inviting.value = true
  inviteTarget.value = emp
  try {
    const result = isResend
      ? await resendEmployeeInvite(emp.id)
      : await sendEmployeeInvite(emp.id)
    inviteResult.value = result
    showInviteModal.value = true
    load()
  } catch (err: any) {
    console.error('Invite failed', err)
    alert(err.message ?? 'Failed to send invite')
  } finally {
    inviting.value = false
  }
}

async function confirmRevokeInvite() {
  if (!revokeTarget.value) return
  revoking.value = true
  try { await revokeEmployeeInvite(revokeTarget.value.id); revokeTarget.value = null; load() }
  catch (err) { console.error('Revoke failed', err) }
  finally { revoking.value = false }
}

async function confirmDisable() {
  if (!disableTarget.value) return
  disabling.value = true
  try { await disableEmployeeAccount(disableTarget.value.id); disableTarget.value = null; load() }
  catch (err) { console.error('Disable failed', err) }
  finally { disabling.value = false }
}

async function copyInviteUrl() {
  if (!inviteResult.value?.invite_url) return
  try {
    await navigator.clipboard.writeText(inviteResult.value.invite_url)
    copySuccess.value = true
    setTimeout(() => { copySuccess.value = false }, 2000)
  } catch {
    // fallback: select the textarea
  }
}

function fullName(emp: Employee | null) {
  if (!emp) return '—'
  return `${emp.first_name ?? ''} ${emp.last_name ?? ''}`.trim()
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Employee Directory"
      subtitle="Manage all employees across your organization"
      action-label="New Employee"
      @action="openCreate"
    >
      <template #extra>
        <Button
          variant="outline"
          @click="load"
          :disabled="loading"
          class="rounded-full gap-2 px-4 h-9"
          title="Refresh list"
        >
          <RefreshCw :class="['w-3.5 h-3.5', loading ? 'animate-spin' : '']" />
          Refresh
        </Button>
      </template>
    </PageHeader>

    <!-- Filters -->
    <div class="flex items-center gap-4 flex-wrap">
      <div class="w-52">
        <FormSelect
          label=""
          :modelValue="statusFilter"
          :options="statusOptions"
          @update:modelValue="statusFilter = $event; page = 1"
        />
      </div>
      <div class="w-52">
        <FormSelect
          label=""
          :modelValue="accountFilter"
          :options="accountStatusOptions"
          @update:modelValue="accountFilter = $event; page = 1"
        />
      </div>
    </div>

    <!-- Table -->
    <DataTable
      :columns="columns"
      :rows="employees"
      :loading="loading"
      :total="total"
      :page="page"
      :page-size="10"
      :searchable="true"
      :pagination-top="true"
      empty-text="No employees found. Create the first one!"
      @page-change="page = $event; load()"
      @search="onSearch"
      @row-click="openProfile"
    >
      <!-- Custom cells -->
      <template #cell-employee_code="{ row }">
        <span
          v-if="row.employee_code"
          class="inline-block px-2 py-0.5 rounded-md bg-muted text-muted-foreground text-[10px] font-mono font-bold"
        >{{ row.employee_code }}</span>
        <span v-else class="text-muted-foreground/30 text-xs">—</span>
      </template>

      <template #cell-name="{ row }">
        <div class="flex items-center space-x-3">
          <div class="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-[10px] font-bold text-muted-foreground shrink-0 border border-border">
            {{ (row.first_name?.[0] ?? '') + (row.last_name?.[0] ?? '') }}
          </div>
          <span class="font-semibold text-foreground">{{ fullName(row) }}</span>
        </div>
      </template>

      <template #cell-employment_status="{ row }">
        <EmployeeStatusBadge :status="row.employment_status" />
      </template>

      <template #cell-account_status="{ row }">
        <AccountStatusBadge :status="row.account_status" :expires-at="row.invite_expires_at" />
      </template>

      <!-- Actions -->
      <template #actions="{ row }">
        <div class="flex items-center justify-end space-x-1">
          <!-- Edit -->
          <Button
            variant="ghost"
            size="icon"
            @click="openEdit(row)"
            class="h-8 w-8 rounded-md"
            title="Edit"
          >
            <Pencil class="w-4 h-4 text-muted-foreground" />
          </Button>

          <!-- Send Invite (not_registered) -->
          <Button
            v-if="row.account_status === 'not_registered'"
            variant="ghost"
            size="icon"
            @click="confirmSendInvite(row)"
            :disabled="inviting && inviteTarget?.id === row.id"
            class="h-8 w-8 rounded-md text-blue-500 hover:text-blue-600 hover:bg-blue-50"
            title="Send Invite"
          >
            <Mail class="w-4 h-4" />
          </Button>

          <!-- Resend Invite (invited) -->
          <Button
            v-if="row.account_status === 'invited'"
            variant="ghost"
            size="icon"
            @click="confirmSendInvite(row, true)"
            :disabled="inviting && inviteTarget?.id === row.id"
            class="h-8 w-8 rounded-md text-blue-500 hover:text-blue-600 hover:bg-blue-50"
            title="Resend Invite"
          >
            <RefreshCw class="w-4 h-4" />
          </Button>

          <!-- Revoke Invite (invited) -->
          <Button
            v-if="row.account_status === 'invited'"
            variant="ghost"
            size="icon"
            @click="revokeTarget = row"
            class="h-8 w-8 rounded-md text-amber-500 hover:text-amber-600 hover:bg-amber-50"
            title="Revoke Invite"
          >
            <XCircle class="w-4 h-4" />
          </Button>

          <!-- Disable Account (active) -->
          <Button
            v-if="row.account_status === 'active'"
            variant="ghost"
            size="icon"
            @click="disableTarget = row"
            class="h-8 w-8 rounded-md text-destructive hover:text-destructive hover:bg-destructive/10"
            title="Disable Account"
          >
            <ShieldOff class="w-4 h-4 text-destructive" />
          </Button>

          <!-- Delete -->
          <Button
            variant="ghost"
            size="icon"
            @click="deleteTarget = row"
            class="h-8 w-8 rounded-md text-destructive hover:text-destructive hover:bg-destructive/10"
            title="Delete"
          >
            <Trash2 class="w-4 h-4 text-destructive" />
          </Button>
        </div>
      </template>
    </DataTable>

    <!-- Employee Profile Panel -->
    <EmployeeProfilePanel
      :open="profileOpen"
      :employee="profileEmployee"
      @close="profileOpen = false"
      @edit="openEdit"
      @updated="onProfileUpdated"
      @deleted="onProfileDeleted"
    />

    <!-- Create / Edit Drawer -->
    <EmployeeDrawer
      :open="drawerOpen"
      :employee="selected"
      @close="drawerOpen = false"
      @saved="onSaved"
    />

    <!-- Delete Confirm -->
    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Employee?"
      :message="`This will permanently delete ${fullName(deleteTarget!)} and all associated records.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />

    <!-- Revoke Invite Confirm -->
    <ConfirmDialog
      :open="!!revokeTarget"
      title="Revoke Invite?"
      :message="`This will cancel the pending invite for ${fullName(revokeTarget!)}. You can send a new invite at any time.`"
      :loading="revoking"
      @confirm="confirmRevokeInvite"
      @cancel="revokeTarget = null"
    />

    <!-- Disable Account Confirm -->
    <ConfirmDialog
      :open="!!disableTarget"
      title="Disable Account?"
      :message="`This will revoke portal access for ${fullName(disableTarget!)}. Their HR record will remain.`"
      :loading="disabling"
      @confirm="confirmDisable"
      @cancel="disableTarget = null"
    />

    <!-- Invite Link Modal (Shadcn Dialog) -->
    <Dialog :open="showInviteModal" @update:open="showInviteModal = $event">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Invite Link Ready</DialogTitle>
          <DialogDescription v-if="inviteResult">
            Share this link with <span class="font-bold">{{ inviteResult.email }}</span>. It expires on
            {{ inviteResult.expires_at ? new Date(inviteResult.expires_at).toLocaleDateString() : '7 days from now' }}.
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

        <DialogFooter class="flex justify-end gap-2 mt-4">
          <Button variant="ghost" @click="showInviteModal = false">
            Close
          </Button>
          <Button @click="copyInviteUrl" class="gap-2 px-6">
            <CheckIcon v-if="copySuccess" class="w-4 h-4" />
            <Copy v-else class="w-4 h-4" />
            {{ copySuccess ? 'Copied!' : 'Copy Link' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
