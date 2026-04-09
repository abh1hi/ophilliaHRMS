<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import { PencilIcon, Trash2Icon, PlusIcon, XIcon } from 'lucide-vue-next'
import { listEmployeeGroups, createEmployeeGroup, updateEmployeeGroup, deleteEmployeeGroup } from '../../services/employee-group.service'
import type { EmployeeGroup } from '../../services/employee-group.service'

const rows = ref<EmployeeGroup[]>([]); const loading = ref(false)
const drawerOpen = ref(false); const form = ref<Partial<EmployeeGroup>>({ members: [] })
const selected = ref<EmployeeGroup | null>(null); const deleteTarget = ref<EmployeeGroup | null>(null)
const saving = ref(false); const deleting = ref(false); const errorMsg = ref('')
const newMemberId = ref('')

const columns = [{ key: 'name', label: 'Group Name' }, { key: 'member_count', label: 'Members' }]

async function load() {
  loading.value = true
  try {
    const groups = await listEmployeeGroups()
    rows.value = groups.map(g => ({ ...g, member_count: g.members?.length ?? 0 }))
  } catch {} finally { loading.value = false }
}
onMounted(load)
function openCreate() { selected.value = null; form.value = { members: [] }; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: EmployeeGroup) { selected.value = row; form.value = { ...row, members: [...(row.members ?? [])] }; errorMsg.value = ''; drawerOpen.value = true }
function addMember() {
  if (!newMemberId.value.trim()) return
  form.value.members = [...(form.value.members ?? []), { employee_id: newMemberId.value.trim() }]
  newMemberId.value = ''
}
function removeMember(id: string) { form.value.members = form.value.members?.filter(m => m.employee_id !== id) }
async function save() {
  saving.value = true; errorMsg.value = ''
  try { if (selected.value) await updateEmployeeGroup(selected.value.id, form.value); else await createEmployeeGroup(form.value); drawerOpen.value = false; load() }
  catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}
async function confirmDelete() {
  if (!deleteTarget.value) return; deleting.value = true
  try { await deleteEmployeeGroup(deleteTarget.value.id); deleteTarget.value = null; load() } catch {} finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Employee Groups" subtitle="Group employees for SLA and bulk operations" action-label="+ New Group" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No employee groups yet.">
      <template #actions="{ row }">
        <div class="flex items-center justify-end space-x-2">
          <button @click="openEdit(row)" class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"><PencilIcon class="w-4 h-4" /></button>
          <button @click="deleteTarget = row" class="p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"><Trash2Icon class="w-4 h-4" /></button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Group' : 'New Employee Group'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6">
        <FormInput label="Group Name" :modelValue="form.name" @update:modelValue="form.name = $event" required />
        <div class="space-y-3">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide">Members</p>
          <div class="flex gap-2">
            <input v-model="newMemberId" placeholder="Employee ID" @keydown.enter.prevent="addMember"
              class="flex-1 bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-[12px] px-4 py-2.5 outline-none focus:ring-2 focus:ring-slate-900/10" />
            <button @click="addMember" class="p-2.5 bg-slate-900 text-white rounded-[12px] hover:bg-slate-800 transition-colors">
              <PlusIcon class="w-4 h-4" />
            </button>
          </div>
          <div v-if="form.members?.length" class="space-y-2">
            <div v-for="m in form.members" :key="m.employee_id" class="flex items-center justify-between px-3 py-2 bg-slate-50 rounded-[10px] border border-slate-200/60">
              <span class="text-sm font-medium text-slate-700">{{ m.employee_name || m.employee_id }}</span>
              <button @click="removeMember(m.employee_id)" class="text-slate-400 hover:text-rose-500 transition-colors"><XIcon class="w-4 h-4" /></button>
            </div>
          </div>
          <p v-else class="text-xs text-slate-400">No members added yet.</p>
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
    <ConfirmDialog :open="!!deleteTarget" title="Delete Group?" :message="`Delete '${deleteTarget?.name}'?`" :loading="deleting" @confirm="confirmDelete" @cancel="deleteTarget = null" />
  </div>
</template>
