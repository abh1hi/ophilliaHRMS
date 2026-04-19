<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Pencil, Trash2, Building2, FolderTree, CheckCircle2, XCircle, FolderOpen } from 'lucide-vue-next'
import { listDepartments, createDepartment, updateDepartment, deleteDepartment } from '../../services/department.service'
import type { Department } from '../../services/department.service'

const rows      = ref<Department[]>([])
const loading   = ref(false)
const drawerOpen = ref(false)
const form      = ref<Partial<Department>>({ is_group: 0 })
const selected  = ref<Department | null>(null)
const deleteTarget = ref<Department | null>(null)
const saving    = ref(false)
const deleting  = ref(false)
const errorMsg  = ref('')

const columns = [
  { key: 'name',      label: 'Department Name' },
  { key: 'is_group',  label: 'Type'            },
  { key: 'is_active', label: 'Status'          },
]

const parentOptions = computed(() => [
  { value: '', label: '— None (Top-level) —' },
  ...rows.value.filter(d => d.is_group).map(d => ({ value: d.id, label: d.name }))
])

async function load() {
  loading.value = true
  try { rows.value = await listDepartments() }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}
onMounted(load)

function openCreate() { selected.value = null; form.value = { is_group: 0 }; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: Department) { selected.value = row; form.value = { ...row }; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  if (!form.value.name?.trim()) { errorMsg.value = 'Department name is required.'; return }
  saving.value = true; errorMsg.value = ''
  try {
    const payload = { ...form.value, parent_department_id: form.value.parent_department_id || undefined }
    if (selected.value) await updateDepartment(selected.value.id, payload)
    else await createDepartment(payload)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try { await deleteDepartment(deleteTarget.value.id); deleteTarget.value = null; load() }
  catch (e) { console.error(e) }
  finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Departments"
      subtitle="Define your organizational structure and reporting hierarchy"
      action-label="Add Department"
      @action="openCreate"
    />

    <DataTable
      :columns="columns"
      :rows="rows"
      :loading="loading"
      :searchable="true"
      empty-text="No departments found. Add your first department to get started."
    >
      <template #cell-name="{ row, value }">
        <div class="flex items-center gap-3">
          <div :class="['h-8 w-8 rounded-lg flex items-center justify-center shrink-0', row.is_group ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-100 text-slate-500']">
            <FolderTree v-if="row.is_group" class="w-4 h-4" />
            <Building2 v-else class="w-4 h-4" />
          </div>
          <span class="font-medium text-slate-900">{{ value }}</span>
        </div>
      </template>

      <template #cell-is_group="{ value }">
        <span :class="['inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium', value ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-100 text-slate-600']">
          <FolderOpen v-if="value" class="w-3 h-3" />
          <Building2 v-else class="w-3 h-3" />
          {{ value ? 'Group' : 'Department' }}
        </span>
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
      :title="selected ? 'Edit Department' : 'Add Department'"
      width="w-full max-w-lg"
      @close="drawerOpen = false"
    >
      <div class="space-y-5 py-2">
        <p class="text-sm text-slate-500">
          {{ selected ? 'Update the department details below.' : 'Fill in the details to create a new department or department group.' }}
        </p>

        <FormInput
          label="Department Name"
          v-model="form.name"
          required
          placeholder="e.g. Engineering, Human Resources"
        />

        <FormInput
          label="Description"
          v-model="form.description"
          placeholder="Brief description of this department's function (optional)"
        />

        <FormSelect
          label="Parent Department"
          v-model="form.parent_department_id"
          :options="parentOptions"
        />

        <FormInput
          label="Leave Block List"
          v-model="form.leave_block_list"
          placeholder="Leave block list ID (optional)"
        />

        <label for="group-toggle" class="flex items-start gap-3 p-4 bg-slate-50 border border-slate-200 rounded-lg cursor-pointer">
          <Checkbox
            id="group-toggle"
            :checked="form.is_group === 1"
            @update:checked="form.is_group = $event ? 1 : 0"
            class="mt-0.5"
          />
          <div>
            <span class="text-sm font-medium text-slate-800">This is a department group</span>
            <p class="text-xs text-slate-500 mt-0.5">
              Groups can contain other departments as sub-departments.
            </p>
          </div>
        </label>
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-3">
          <p v-if="errorMsg" class="text-sm text-destructive">{{ errorMsg }}</p>
          <div class="flex gap-2 ml-auto">
            <Button variant="outline" @click="drawerOpen = false">Cancel</Button>
            <Button @click="save" :disabled="saving">
              {{ saving ? 'Saving…' : selected ? 'Save Changes' : 'Add Department' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Department?"
      :message="`Are you sure you want to delete '${deleteTarget?.name}'? This action cannot be undone.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
