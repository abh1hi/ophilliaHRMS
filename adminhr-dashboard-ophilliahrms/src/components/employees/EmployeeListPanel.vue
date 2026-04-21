<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import EmployeeDrawer from './EmployeeDrawer.vue'
import EmployeeProfilePanel from './EmployeeProfilePanel.vue'
import EmployeeTable from './EmployeeTable.vue'
import EmployeeFilters from './EmployeeFilters.vue'
import EmployeeBulkActions from './EmployeeBulkActions.vue'
import EmployeeInviteModal from './EmployeeInviteModal.vue'
import { CheckIcon, XCircle } from 'lucide-vue-next'
import {
  listEmployees, deleteEmployee,
  sendEmployeeInvite, resendEmployeeInvite, revokeEmployeeInvite, disableEmployeeAccount,
} from '../../services/employee.service'
import type { Employee, SendInviteResponse } from '../../services/employee.service'

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

// Bulk selection
const selectedIds  = ref(new Set<string>())
const bulkInviting = ref(false)
const bulkInviteResult = ref<string | null>(null)

// Profile panel
const profileOpen     = ref(false)
const profileEmployee = ref<Employee | null>(null)

// Invite state
const inviteTarget  = ref<Employee | null>(null)
const inviteResult  = ref<SendInviteResponse | null>(null)
const inviting      = ref(false)
const showInviteModal = ref(false)

// Revoke state
const revokeTarget = ref<Employee | null>(null)
const revoking     = ref(false)

// Disable state
const disableTarget = ref<Employee | null>(null)
const disabling     = ref(false)

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

function toggleSelect(id: string) {
  const s = new Set(selectedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedIds.value = s
}

function toggleSelectAll() {
  if (selectedIds.value.size === employees.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(employees.value.map(e => e.id))
  }
}

const selectedNotRegistered = computed(() =>
  employees.value.filter(e => selectedIds.value.has(e.id) && e.account_status === 'not_registered')
)

async function bulkInvite() {
  if (!selectedNotRegistered.value.length) return
  bulkInviting.value = true
  bulkInviteResult.value = null
  let success = 0
  for (const emp of selectedNotRegistered.value) {
    try { await sendEmployeeInvite(emp.id); success++ } catch { /* continue */ }
  }
  bulkInviteResult.value = `Invites sent to ${success} of ${selectedNotRegistered.value.length} employee(s).`
  selectedIds.value = new Set()
  bulkInviting.value = false
  load()
}

function exportCsv() {
  const headers = ['Employee ID', 'First Name', 'Last Name', 'Email', 'Department', 'Designation', 'Status']
  const rows = employees.value.map(e => [
    e.employee_code ?? '',
    e.first_name ?? '',
    e.last_name ?? '',
    e.email ?? '',
    e.department?.name ?? '',
    e.designation ?? '',
    e.employment_status ?? '',
  ])
  const csv = [headers, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'employees.csv'
  a.click()
  URL.revokeObjectURL(url)
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
        <EmployeeBulkActions
          :selected-count="selectedNotRegistered.length"
          :bulk-inviting="bulkInviting"
          :loading="loading"
          @bulk-invite="bulkInvite"
          @export="exportCsv"
          @refresh="load"
        />
      </template>
    </PageHeader>

    <!-- Filters -->
    <EmployeeFilters
      v-model:statusFilter="statusFilter"
      v-model:accountFilter="accountFilter"
      @update:statusFilter="page = 1"
      @update:accountFilter="page = 1"
    />

    <!-- Bulk invite feedback -->
    <div v-if="bulkInviteResult" class="flex items-center gap-2 px-4 py-2.5 bg-blue-50 border border-blue-100 rounded-xl text-sm text-blue-700 font-medium animate-in fade-in">
      <CheckIcon class="w-4 h-4 shrink-0" />
      {{ bulkInviteResult }}
      <button @click="bulkInviteResult = null" class="ml-auto text-blue-400 hover:text-blue-600">
        <XCircle class="w-4 h-4" />
      </button>
    </div>

    <!-- Table -->
    <EmployeeTable
      :employees="employees"
      :loading="loading"
      :total="total"
      :page="page"
      :selected-ids="selectedIds"
      :inviting="inviting"
      :invite-target-id="inviteTarget?.id"
      @page-change="page = $event; load()"
      @search="onSearch"
      @profile="openProfile"
      @edit="openEdit"
      @delete="deleteTarget = $event"
      @invite="confirmSendInvite"
      @revoke="revokeTarget = $event"
      @disable="disableTarget = $event"
      @toggle-select="toggleSelect"
      @toggle-select-all="toggleSelectAll"
    />

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

    <!-- Confirm Dialogs -->
    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Employee?"
      :message="`This will permanently delete ${fullName(deleteTarget!)} and all associated records.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />

    <ConfirmDialog
      :open="!!revokeTarget"
      title="Revoke Invite?"
      :message="`This will cancel the pending invite for ${fullName(revokeTarget!)}. You can send a new invite at any time.`"
      :loading="revoking"
      @confirm="confirmRevokeInvite"
      @cancel="revokeTarget = null"
    />

    <ConfirmDialog
      :open="!!disableTarget"
      title="Disable Account?"
      :message="`This will revoke portal access for ${fullName(disableTarget!)}. Their HR record will remain.`"
      :loading="disabling"
      @confirm="confirmDisable"
      @cancel="disableTarget = null"
    />

    <!-- Invite Link Modal -->
    <EmployeeInviteModal
      v-model:open="showInviteModal"
      :invite-result="inviteResult"
    />
  </div>
</template>
