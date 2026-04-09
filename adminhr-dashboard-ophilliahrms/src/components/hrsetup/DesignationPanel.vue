<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { PencilIcon, Trash2Icon, XIcon } from 'lucide-vue-next'
import { listDesignations, createDesignation, updateDesignation, deleteDesignation } from '../../services/designation.service'
import type { Designation } from '../../services/designation.service'

const rows = ref<Designation[]>([]); const loading = ref(false)
const drawerOpen = ref(false); const form = ref<Partial<Designation>>({})
const selected = ref<Designation | null>(null); const deleteTarget = ref<Designation | null>(null)
const saving = ref(false); const deleting = ref(false); const errorMsg = ref('')
const skillInput = ref('')

const columns = [
  { key: 'name',        label: 'Designation'    },
  { key: 'description', label: 'Description'   },
]

async function load() { loading.value = true; try { rows.value = await listDesignations() } catch {} finally { loading.value = false } }
onMounted(load)

function openCreate() { selected.value = null; form.value = { required_skills: [] }; skillInput.value = ''; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: Designation) { selected.value = row; form.value = { ...row, required_skills: [...(row.required_skills ?? [])] }; skillInput.value = ''; errorMsg.value = ''; drawerOpen.value = true }

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
  saving.value = true; errorMsg.value = ''
  try { if (selected.value) await updateDesignation(selected.value.id, form.value); else await createDesignation(form.value); drawerOpen.value = false; load() }
  catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}
async function confirmDelete() {
  if (!deleteTarget.value) return; deleting.value = true
  try { await deleteDesignation(deleteTarget.value.id); deleteTarget.value = null; load() } catch {} finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Designations" subtitle="Define job titles and required skills" action-label="+ New Designation" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No designations yet.">
      <template #actions="{ row }">
        <div class="flex items-center justify-end space-x-2">
          <button @click="openEdit(row)" class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"><PencilIcon class="w-4 h-4" /></button>
          <button @click="deleteTarget = row" class="p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"><Trash2Icon class="w-4 h-4" /></button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Designation' : 'New Designation'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Designation Name" :modelValue="form.name" @update:modelValue="form.name = $event" required />
        <FormTextarea label="Description" :modelValue="form.description" @update:modelValue="form.description = $event" />

        <!-- Required Skills -->
        <div class="space-y-2">
          <label class="block text-sm font-semibold text-slate-700">Required Skills</label>
          <div class="flex gap-2">
            <input
              v-model="skillInput"
              @keydown.enter.prevent="addSkill"
              type="text"
              placeholder="Type a skill and press Enter"
              class="flex-1 bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-[12px] px-3 py-2.5 outline-none focus:ring-2 focus:ring-slate-900/10"
            />
            <button @click="addSkill" type="button" class="px-4 py-2.5 bg-slate-900 text-white text-sm rounded-[12px] hover:bg-slate-800 transition-colors font-medium">Add</button>
          </div>
          <div v-if="form.required_skills?.length" class="flex flex-wrap gap-2 pt-1">
            <span
              v-for="(skill, i) in form.required_skills"
              :key="i"
              class="inline-flex items-center gap-1.5 bg-slate-100 text-slate-700 text-xs font-medium px-3 py-1.5 rounded-full"
            >
              {{ skill }}
              <button @click="removeSkill(i)" class="text-slate-400 hover:text-rose-500 transition-colors"><XIcon class="w-3 h-3" /></button>
            </span>
          </div>
        </div>
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
    <ConfirmDialog :open="!!deleteTarget" title="Delete Designation?" :message="`Delete '${deleteTarget?.name}'?`" :loading="deleting" @confirm="confirmDelete" @cancel="deleteTarget = null" />
  </div>
</template>
