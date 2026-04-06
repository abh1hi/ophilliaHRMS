<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import EmployeeDrawer from './EmployeeDrawer.vue'
import EmployeeStatusBadge from './EmployeeStatusBadge.vue'
import FormSelect from '../ui/FormSelect.vue'
import { listEmployees, deleteEmployee } from '../../services/employee.service'
import type { Employee } from '../../services/employee.service'
import { PencilIcon, Trash2Icon } from 'lucide-vue-next'

const employees   = ref<Employee[]>([])
const total       = ref(0)
const loading     = ref(false)
const page        = ref(1)
const search      = ref('')
const statusFilter = ref('')
const drawerOpen  = ref(false)
const selected    = ref<Employee | null>(null)
const deleteTarget = ref<Employee | null>(null)
const deleting    = ref(false)

const columns = [
  { key: 'name',       label: 'Name'       },
  { key: 'email',      label: 'Email'      },
  { key: 'department', label: 'Department' },
  { key: 'designation',label: 'Designation'},
  { key: 'employment_status', label: 'Status' },
]

const statusOptions = [
  { value: '',           label: 'All Statuses' },
  { value: 'active',     label: 'Active'       },
  { value: 'inactive',   label: 'Inactive'     },
  { value: 'terminated', label: 'Terminated'   },
]

async function load() {
  loading.value = true
  try {
    const result = await listEmployees({
      page: page.value,
      page_size: 20,
      search: search.value || undefined,
      employment_status: statusFilter.value || undefined,
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
watch([page, statusFilter], load)

function onSearch(q: string) { search.value = q; page.value = 1; load() }
function openCreate() { selected.value = null; drawerOpen.value = true }
function openEdit(emp: Employee) { selected.value = emp; drawerOpen.value = true }
function onSaved() { load() }
async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try { await deleteEmployee(deleteTarget.value.id); deleteTarget.value = null; load() }
  catch (err) { console.error('Delete failed', err) }
  finally { deleting.value = false }
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
    />

    <!-- Filters -->
    <div class="flex items-center gap-4">
      <div class="w-52">
        <FormSelect
          label=""
          :modelValue="statusFilter"
          :options="statusOptions"
          @update:modelValue="statusFilter = $event; page = 1"
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
      :page-size="20"
      :searchable="true"
      empty-text="No employees found. Create the first one!"
      @page-change="page = $event; load()"
      @search="onSearch"
    >
      <!-- Custom cells -->
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

      <!-- Actions -->
      <template #actions="{ row }">
        <div class="flex items-center justify-end space-x-2">
          <button
            @click="openEdit(row)"
            class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"
            title="Edit"
          >
            <PencilIcon class="w-4 h-4" />
          </button>
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

    <!-- Drawer -->
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
  </div>
</template>
