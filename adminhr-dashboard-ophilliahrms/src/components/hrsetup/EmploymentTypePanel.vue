<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import { Button } from '@/components/ui/button'
import { Pencil, Trash2, FileText } from 'lucide-vue-next'
import { listEmploymentTypes, createEmploymentType, updateEmploymentType, deleteEmploymentType } from '../../services/employment-type.service'
import type { EmploymentType } from '../../services/employment-type.service'

const rows        = ref<EmploymentType[]>([])
const loading     = ref(false)
const drawerOpen  = ref(false)
const form        = ref<Partial<EmploymentType>>({})
const selected    = ref<EmploymentType | null>(null)
const deleteTarget = ref<EmploymentType | null>(null)
const saving      = ref(false)
const deleting    = ref(false)
const errorMsg    = ref('')

const columns = [
  { key: 'name',       label: 'Employment Type' },
  { key: 'created_at', label: 'Created'         },
]

async function load() {
  loading.value = true
  try { rows.value = await listEmploymentTypes() }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}
onMounted(load)

function openCreate() { selected.value = null; form.value = {}; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: EmploymentType) { selected.value = row; form.value = { ...row }; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  if (!form.value.name?.trim()) { errorMsg.value = 'Employment type name is required.'; return }
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateEmploymentType(selected.value.id, form.value)
    else await createEmploymentType(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try { await deleteEmploymentType(deleteTarget.value.id); deleteTarget.value = null; load() }
  catch (e) { console.error(e) }
  finally { deleting.value = false }
}

function formatDate(value: string | undefined) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Employment Types"
      subtitle="Define the types of employment contracts used in your organization"
      action-label="Add Employment Type"
      @action="openCreate"
    />

    <DataTable
      :columns="columns"
      :rows="rows"
      :loading="loading"
      :searchable="true"
      empty-text="No employment types found. Add your first type to get started."
    >
      <template #cell-name="{ value }">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
            <FileText class="w-4 h-4 text-slate-500" />
          </div>
          <span class="font-medium text-slate-900">{{ value }}</span>
        </div>
      </template>

      <template #cell-created_at="{ value }">
        <span class="text-sm text-slate-500">{{ formatDate(value) }}</span>
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
      :title="selected ? 'Edit Employment Type' : 'Add Employment Type'"
      width="w-full max-w-lg"
      @close="drawerOpen = false"
    >
      <div class="space-y-5 py-2">
        <p class="text-sm text-slate-500">
          {{ selected
            ? 'Update the employment type name below.'
            : 'Add a new employment type (e.g. Full-time, Part-time, Contract, Intern).' }}
        </p>

        <FormInput
          label="Employment Type Name"
          v-model="form.name"
          required
          placeholder="e.g. Full-time, Part-time, Contract, Intern"
        />
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-3">
          <p v-if="errorMsg" class="text-sm text-destructive">{{ errorMsg }}</p>
          <div class="flex gap-2 ml-auto">
            <Button variant="outline" @click="drawerOpen = false">Cancel</Button>
            <Button @click="save" :disabled="saving">
              {{ saving ? 'Saving…' : selected ? 'Save Changes' : 'Add Employment Type' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Employment Type?"
      :message="`Are you sure you want to delete '${deleteTarget?.name}'? Employees assigned this type may be affected.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
