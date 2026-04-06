<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import { PencilIcon, Trash2Icon } from 'lucide-vue-next'
import { listEmployeeGrades, createEmployeeGrade, updateEmployeeGrade, deleteEmployeeGrade } from '../../services/employee-grade.service'
import type { EmployeeGrade } from '../../services/employee-grade.service'

const rows = ref<EmployeeGrade[]>([]); const loading = ref(false)
const drawerOpen = ref(false); const form = ref<Partial<EmployeeGrade>>({})
const selected = ref<EmployeeGrade | null>(null); const deleteTarget = ref<EmployeeGrade | null>(null)
const saving = ref(false); const deleting = ref(false); const errorMsg = ref('')

const columns = [
  { key: 'name',                   label: 'Grade'            },
  { key: 'default_leave_policy',   label: 'Leave Policy'    },
  { key: 'default_salary_structure', label: 'Salary Structure' },
  { key: 'is_active',              label: 'Status'           },
]

async function load() { loading.value = true; try { rows.value = await listEmployeeGrades() } catch {} finally { loading.value = false } }
onMounted(load)
function openCreate() { selected.value = null; form.value = {}; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: EmployeeGrade) { selected.value = row; form.value = { ...row }; errorMsg.value = ''; drawerOpen.value = true }
async function save() {
  saving.value = true; errorMsg.value = ''
  try { if (selected.value) await updateEmployeeGrade(selected.value.id, form.value); else await createEmployeeGrade(form.value); drawerOpen.value = false; load() }
  catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}
async function confirmDelete() {
  if (!deleteTarget.value) return; deleting.value = true
  try { await deleteEmployeeGrade(deleteTarget.value.id); deleteTarget.value = null; load() } catch {} finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Employee Grades" subtitle="Group employees by grade for payroll and leave allocation" action-label="+ New Grade" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No grades defined yet.">
      <template #cell-is_active="{ value }">
        <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', value ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500']">
          {{ value ? 'Active' : 'Inactive' }}
        </span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end space-x-2">
          <button @click="openEdit(row)" class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"><PencilIcon class="w-4 h-4" /></button>
          <button @click="deleteTarget = row" class="p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"><Trash2Icon class="w-4 h-4" /></button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Grade' : 'New Employee Grade'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Grade Name" :modelValue="form.name" @update:modelValue="form.name = $event" required placeholder="e.g. L1, Senior, Executive" />
        <FormInput label="Default Leave Policy" :modelValue="form.default_leave_policy" @update:modelValue="form.default_leave_policy = $event" placeholder="Optional — e.g. Annual Leave Policy" />
        <FormInput label="Default Salary Structure" :modelValue="form.default_salary_structure" @update:modelValue="form.default_salary_structure = $event" placeholder="Optional — e.g. Senior Structure" />
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="drawerOpen = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="save" :disabled="saving" class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>
    <ConfirmDialog :open="!!deleteTarget" title="Delete Grade?" :message="`Delete '${deleteTarget?.name}'?`" :loading="deleting" @confirm="confirmDelete" @cancel="deleteTarget = null" />
  </div>
</template>
