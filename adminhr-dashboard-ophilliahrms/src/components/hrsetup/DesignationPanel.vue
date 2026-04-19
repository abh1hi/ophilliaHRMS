<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Pencil, Trash2, X, Briefcase } from 'lucide-vue-next'
import { listDesignations, createDesignation, updateDesignation, deleteDesignation } from '../../services/designation.service'
import type { Designation } from '../../services/designation.service'

const rows       = ref<Designation[]>([])
const loading    = ref(false)
const drawerOpen = ref(false)
const form       = ref<Partial<Designation>>({})
const selected   = ref<Designation | null>(null)
const deleteTarget = ref<Designation | null>(null)
const saving     = ref(false)
const deleting   = ref(false)
const errorMsg   = ref('')
const skillInput = ref('')

const columns = [
  { key: 'name',        label: 'Designation'  },
  { key: 'description', label: 'Description'  },
]

async function load() {
  loading.value = true
  try { rows.value = await listDesignations() }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}
onMounted(load)

function openCreate() {
  selected.value = null
  form.value = { required_skills: [] }
  skillInput.value = ''
  errorMsg.value = ''
  drawerOpen.value = true
}

function openEdit(row: Designation) {
  selected.value = row
  form.value = { ...row, required_skills: [...(row.required_skills ?? [])] }
  skillInput.value = ''
  errorMsg.value = ''
  drawerOpen.value = true
}

function addSkill() {
  const s = skillInput.value.trim()
  if (!s) return
  form.value.required_skills = [...(form.value.required_skills ?? []), s]
  skillInput.value = ''
}

function removeSkill(i: number) {
  form.value.required_skills = (form.value.required_skills ?? []).filter((_, idx) => idx !== i)
}

async function save() {
  if (!form.value.name?.trim()) { errorMsg.value = 'Designation name is required.'; return }
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateDesignation(selected.value.id, form.value)
    else await createDesignation(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try { await deleteDesignation(deleteTarget.value.id); deleteTarget.value = null; load() }
  catch (e) { console.error(e) }
  finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Designations"
      subtitle="Define job titles, roles, and required skills for your organization"
      action-label="Add Designation"
      @action="openCreate"
    />

    <DataTable
      :columns="columns"
      :rows="rows"
      :loading="loading"
      :searchable="true"
      empty-text="No designations found. Add your first designation to get started."
    >
      <template #cell-name="{ value }">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
            <Briefcase class="w-4 h-4 text-slate-500" />
          </div>
          <span class="font-medium text-slate-900">{{ value }}</span>
        </div>
      </template>

      <template #cell-description="{ value }">
        <span class="text-sm text-slate-500 line-clamp-1 max-w-sm">{{ value || '—' }}</span>
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
      :title="selected ? 'Edit Designation' : 'Add Designation'"
      width="w-full max-w-lg"
      @close="drawerOpen = false"
    >
      <div class="space-y-5 py-2">
        <p class="text-sm text-slate-500">
          {{ selected ? 'Update the designation details below.' : 'Create a new job title or role for your organization.' }}
        </p>

        <FormInput
          label="Designation Name"
          v-model="form.name"
          required
          placeholder="e.g. Software Engineer, HR Manager"
        />

        <FormTextarea
          label="Description"
          v-model="form.description"
          placeholder="Briefly describe the responsibilities of this role (optional)"
        />

        <!-- Required Skills -->
        <div class="space-y-3">
          <label class="block text-sm font-medium text-slate-700">Required Skills</label>
          <div class="flex gap-2">
            <input
              v-model="skillInput"
              @keydown.enter.prevent="addSkill"
              type="text"
              placeholder="Type a skill and press Enter or click Add"
              class="flex-1 border border-slate-200 bg-white text-slate-900 text-sm rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
            />
            <Button @click="addSkill" type="button" variant="outline" class="shrink-0">Add</Button>
          </div>

          <div v-if="form.required_skills?.length" class="flex flex-wrap gap-2">
            <Badge
              v-for="(skill, i) in form.required_skills"
              :key="i"
              variant="secondary"
              class="flex items-center gap-1.5 px-3 py-1 text-sm"
            >
              {{ skill }}
              <button @click="removeSkill(i)" class="text-slate-400 hover:text-destructive transition-colors ml-1">
                <X class="w-3 h-3" />
              </button>
            </Badge>
          </div>
          <p v-else class="text-xs text-slate-400">No skills added yet.</p>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-3">
          <p v-if="errorMsg" class="text-sm text-destructive">{{ errorMsg }}</p>
          <div class="flex gap-2 ml-auto">
            <Button variant="outline" @click="drawerOpen = false">Cancel</Button>
            <Button @click="save" :disabled="saving">
              {{ saving ? 'Saving…' : selected ? 'Save Changes' : 'Add Designation' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Designation?"
      :message="`Are you sure you want to delete the designation '${deleteTarget?.name}'? This action cannot be undone.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
