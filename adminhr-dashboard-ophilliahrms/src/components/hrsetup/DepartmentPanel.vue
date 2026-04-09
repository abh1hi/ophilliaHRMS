<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import { PencilIcon, Trash2Icon } from 'lucide-vue-next'
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

// Parent dept options (groups only)
const parentOptions = computed(() => [
  { value: '', label: '— None —' },
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
  saving.value = true; errorMsg.value = ''
  try {
    const payload = {
      ...form.value,
      parent_department_id: form.value.parent_department_id || undefined,
    }
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
    <PageHeader title="Departments" subtitle="Manage company departments and sub-departments" action-label="+ New Department" @action="openCreate" />

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No departments yet.">
      <template #cell-is_group="{ value }">
        <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', value ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-500']">
          {{ value ? 'Group' : 'Department' }}
        </span>
      </template>
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

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Department' : 'New Department'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Department Name" :modelValue="form.name" @update:modelValue="form.name = $event" required />
        <FormInput label="Description" :modelValue="form.description" @update:modelValue="form.description = $event" />
        <FormSelect
          label="Parent Department"
          :modelValue="form.parent_department_id ?? ''"
          :options="parentOptions"
          @update:modelValue="form.parent_department_id = $event || undefined"
        />
        <FormInput label="Leave Block List" :modelValue="form.leave_block_list" @update:modelValue="form.leave_block_list = $event" placeholder="Optional" />
        <label class="flex items-center space-x-3 cursor-pointer">
          <input
            type="checkbox"
            :checked="!!form.is_group"
            @change="form.is_group = ($event.target as HTMLInputElement).checked ? 1 : 0"
            class="w-4 h-4 rounded border-slate-300"
          />
          <span class="text-sm font-medium text-slate-700">Is Group (parent department)</span>
        </label>
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

    <ConfirmDialog :open="!!deleteTarget" title="Delete Department?" :message="`Delete '${deleteTarget?.name}'? This cannot be undone.`" :loading="deleting" @confirm="confirmDelete" @cancel="deleteTarget = null" />
  </div>
</template>
