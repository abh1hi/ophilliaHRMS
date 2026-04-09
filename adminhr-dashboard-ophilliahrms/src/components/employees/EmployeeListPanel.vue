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
import {
  listEmployees, deleteEmployee,
  sendEmployeeInvite, resendEmployeeInvite, revokeEmployeeInvite, disableEmployeeAccount,
} from '../../services/employee.service'
import type { Employee, SendInviteResponse } from '../../services/employee.service'
import { PencilIcon, Trash2Icon, RefreshCwIcon, MailIcon, ShieldOffIcon, XCircleIcon } from 'lucide-vue-next'

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
      action-label="+ New Employee"
      @action="openCreate"
    >
      <template #extra>
        <button
          @click="load"
          :disabled="loading"
          class="flex items-center gap-1.5 px-4 py-2 border border-slate-200 text-slate-500 rounded-full text-sm font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
          title="Refresh list"
        >
          <RefreshCwIcon :class="['w-3.5 h-3.5', loading ? 'animate-spin' : '']" />
          Refresh
        </button>
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
          class="inline-block px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-xs font-mono font-semibold"
        >{{ row.employee_code }}</span>
        <span v-else class="text-slate-300 text-xs">—</span>
      </template>

      <template #cell-name="{ row }">
        <div class="flex items-center space-x-3">
          <div class="w-8 h-8 rounded-[10px] bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-600 shrink-0">
            {{ (row.first_name?.[0] ?? '') + (row.last_name?.[0] ?? '') }}
          </div>
          <span class="font-semibold text-slate-900">{{ fullName(row) }}</span>
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
          <button
            @click="openEdit(row)"
            class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"
            title="Edit"
          >
            <PencilIcon class="w-4 h-4" />
          </button>

          <!-- Send Invite (not_registered) -->
          <button
            v-if="row.account_status === 'not_registered'"
            @click="confirmSendInvite(row)"
            :disabled="inviting && inviteTarget?.id === row.id"
            class="p-2 rounded-[10px] hover:bg-blue-50 text-slate-400 hover:text-blue-600 transition-colors disabled:opacity-40"
            title="Send Invite"
          >
            <MailIcon class="w-4 h-4" />
          </button>

          <!-- Resend Invite (invited) -->
          <button
            v-if="row.account_status === 'invited'"
            @click="confirmSendInvite(row, true)"
            :disabled="inviting && inviteTarget?.id === row.id"
            class="p-2 rounded-[10px] hover:bg-blue-50 text-slate-400 hover:text-blue-600 transition-colors disabled:opacity-40"
            title="Resend Invite"
          >
            <RefreshCwIcon class="w-4 h-4" />
          </button>

          <!-- Revoke Invite (invited) -->
          <button
            v-if="row.account_status === 'invited'"
            @click="revokeTarget = row"
            class="p-2 rounded-[10px] hover:bg-amber-50 text-slate-400 hover:text-amber-600 transition-colors"
            title="Revoke Invite"
          >
            <XCircleIcon class="w-4 h-4" />
          </button>

          <!-- Disable Account (active) -->
          <button
            v-if="row.account_status === 'active'"
            @click="disableTarget = row"
            class="p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"
            title="Disable Account"
          >
            <ShieldOffIcon class="w-4 h-4" />
          </button>

          <!-- Delete -->
          <button
            @click="deleteTarget = row"
            class="p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"
            title="Delete"
          >
            <Trash2Icon class="w-4 h-4" />
          </button>
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

    <!-- Invite Link Modal -->
    <div
      v-if="showInviteModal && inviteResult"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      @click.self="showInviteModal = false"
    >
      <div class="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md space-y-4">
        <h3 class="text-base font-semibold text-slate-800">Invite Link Ready</h3>
        <p class="text-sm text-slate-500">
          Share this link with <strong>{{ inviteResult.email }}</strong>. It expires on
          {{ inviteResult.expires_at ? new Date(inviteResult.expires_at).toLocaleDateString() : '7 days from now' }}.
        </p>
        <textarea
          readonly
          :value="inviteResult.invite_url"
          rows="3"
          class="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-3 resize-none text-slate-700 focus:outline-none"
        />
        <div class="flex justify-end gap-3">
          <button
            @click="showInviteModal = false"
            class="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 transition-colors"
          >Close</button>
          <button
            @click="copyInviteUrl"
            class="px-4 py-2 text-sm font-medium bg-slate-900 text-white rounded-full hover:bg-slate-700 transition-colors"
          >
            {{ copySuccess ? 'Copied!' : 'Copy Link' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
