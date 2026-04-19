<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import { Button } from '@/components/ui/button'
import { Pencil, Trash2, Award, CheckCircle2, XCircle } from 'lucide-vue-next'
import { listEmployeeGrades, createEmployeeGrade, updateEmployeeGrade, deleteEmployeeGrade } from '../../services/employee-grade.service'
import type { EmployeeGrade } from '../../services/employee-grade.service'

const rows        = ref<EmployeeGrade[]>([])
const loading     = ref(false)
const drawerOpen  = ref(false)
const form        = ref<Partial<EmployeeGrade>>({})
const selected    = ref<EmployeeGrade | null>(null)
const deleteTarget = ref<EmployeeGrade | null>(null)
const saving      = ref(false)
const deleting    = ref(false)
const errorMsg    = ref('')

const columns = [
  { key: 'name',                    label: 'Grade Name'            },
  { key: 'default_leave_policy',    label: 'Default Leave Policy'  },
  { key: 'default_salary_structure', label: 'Default Salary Structure' },
  { key: 'is_active',               label: 'Status'               },
]

async function load() {
  loading.value = true
  try { rows.value = await listEmployeeGrades() }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}
onMounted(load)

function openCreate() { selected.value = null; form.value = {}; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: EmployeeGrade) { selected.value = row; form.value = { ...row }; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  if (!form.value.name?.trim()) { errorMsg.value = 'Grade name is required.'; return }
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateEmployeeGrade(selected.value.id, form.value)
    else await createEmployeeGrade(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try { await deleteEmployeeGrade(deleteTarget.value.id); deleteTarget.value = null; load() }
  catch (e) { console.error(e) }
  finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Employee Grades"
      subtitle="Define grade levels and link default leave policies and salary structures"
      action-label="Add Grade"
      @action="openCreate"
    />

    <DataTable
      :columns="columns"
      :rows="rows"
      :loading="loading"
      :searchable="true"
      empty-text="No grades found. Add your first employee grade to get started."
    >
      <template #cell-name="{ value }">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
            <Award class="w-4 h-4 text-slate-500" />
          </div>
          <span class="font-medium text-slate-900">{{ value }}</span>
        </div>
      </template>

      <template #cell-default_leave_policy="{ value }">
        <span class="text-sm text-slate-500">{{ value || '— Not set —' }}</span>
      </template>

      <template #cell-default_salary_structure="{ value }">
        <span class="text-sm text-slate-500">{{ value || '— Not set —' }}</span>
      </template>

      <template #cell-is_active="{ value }">
        <span :class="['inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium', value ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500']">
          <CheckCircle2 v-if="value" class="w-3 h-3" />
          <XCircle v-else class="w-3 h-3" />
          {{ value ? 'Active' : 'Inactive' }}
        </span>
      </template>

      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <Button variant="ghost" size="icon" @click="openEdit(row)" class="h-8 w-8 text-slate-400 hover:text-slate-700 hover:bg-slate-100">
            <Pencil class="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="icon" @click="deleteTarget = row" class="h-8 w-8 text-slate-400 hover:text-destructive hover:bg-red-50">
            <Trash2 class="w-3.5 h-3.5" />
          </Button>
        </div>
      </template>
    </DataTable>

    <!-- Create / Edit drawer -->
    <SlideDrawer
      :open="drawerOpen"
      :title="selected ? 'Edit Employee Grade' : 'Add Employee Grade'"
      width="w-full max-w-lg"
      @close="drawerOpen = false"
    >
      <div class="space-y-5 py-2">
        <p class="text-sm text-slate-500">
          {{ selected
            ? 'Update the grade details below.'
            : 'Create a new grade level. Optionally link a default leave policy and salary structure that employees at this grade will inherit.' }}
        </p>

        <FormInput
          label="Grade Name"
          v-model="form.name"
          required
          placeholder="e.g. L1 – Junior, L3 – Senior, M1 – Manager"
        />

        <div class="space-y-4 pt-2 border-t border-slate-100">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Default Policies (optional)</p>

          <FormInput
            label="Default Leave Policy"
            v-model="form.default_leave_policy"
            placeholder="Leave policy ID or name"
          />

          <FormInput
            label="Default Salary Structure"
            v-model="form.default_salary_structure"
            placeholder="Salary structure ID or name"
          />

          <p class="text-xs text-slate-400">
            Employees assigned to this grade will inherit these defaults unless overridden individually.
          </p>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-3">
          <p v-if="errorMsg" class="text-sm text-destructive">{{ errorMsg }}</p>
          <div class="flex gap-2 ml-auto">
            <Button variant="outline" @click="drawerOpen = false">Cancel</Button>
            <Button @click="save" :disabled="saving">
              {{ saving ? 'Saving…' : selected ? 'Save Changes' : 'Add Grade' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Employee Grade?"
      :message="`Are you sure you want to delete the grade '${deleteTarget?.name}'? Employees assigned this grade may be affected.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
