<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import { Button } from '@/components/ui/button'
import { Pencil, Trash2, Building, CheckCircle2, XCircle } from 'lucide-vue-next'
import { listBranches, createBranch, updateBranch, deleteBranch } from '../../services/branch.service'
import type { Branch } from '../../services/branch.service'

const rows        = ref<Branch[]>([])
const loading     = ref(false)
const drawerOpen  = ref(false)
const form        = ref<Partial<Branch>>({})
const selected    = ref<Branch | null>(null)
const deleteTarget = ref<Branch | null>(null)
const saving      = ref(false)
const deleting    = ref(false)
const errorMsg    = ref('')

const columns = [
  { key: 'name',      label: 'Branch Name' },
  { key: 'is_active', label: 'Status'      },
]

async function load() {
  loading.value = true
  try { rows.value = await listBranches() }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}
onMounted(load)

function openCreate() { selected.value = null; form.value = {}; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: Branch) { selected.value = row; form.value = { ...row }; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  if (!form.value.name?.trim()) { errorMsg.value = 'Branch name is required.'; return }
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateBranch(selected.value.id, form.value)
    else await createBranch(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try { await deleteBranch(deleteTarget.value.id); deleteTarget.value = null; load() }
  catch (e) { console.error(e) }
  finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Branches"
      subtitle="Manage your company's office locations and branches"
      action-label="Add Branch"
      @action="openCreate"
    />

    <DataTable
      :columns="columns"
      :rows="rows"
      :loading="loading"
      :searchable="true"
      empty-text="No branches found. Add your first branch to get started."
    >
      <template #cell-name="{ value }">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
            <Building class="w-4 h-4 text-slate-500" />
          </div>
          <span class="font-medium text-slate-900">{{ value }}</span>
        </div>
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
      :title="selected ? 'Edit Branch' : 'Add Branch'"
      width="w-full max-w-lg"
      @close="drawerOpen = false"
    >
      <div class="space-y-5 py-2">
        <p class="text-sm text-slate-500">
          {{ selected ? 'Update the branch name below.' : 'Enter a name for the new branch or office location.' }}
        </p>

        <FormInput
          label="Branch Name"
          v-model="form.name"
          required
          placeholder="e.g. Mumbai Head Office, Delhi Branch"
        />
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-3">
          <p v-if="errorMsg" class="text-sm text-destructive">{{ errorMsg }}</p>
          <div class="flex gap-2 ml-auto">
            <Button variant="outline" @click="drawerOpen = false">Cancel</Button>
            <Button @click="save" :disabled="saving">
              {{ saving ? 'Saving…' : selected ? 'Save Changes' : 'Add Branch' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Branch?"
      :message="`Are you sure you want to delete the branch '${deleteTarget?.name}'? This action cannot be undone.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
