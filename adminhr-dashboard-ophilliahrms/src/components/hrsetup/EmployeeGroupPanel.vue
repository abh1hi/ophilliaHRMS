<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import { Button } from '@/components/ui/button'
import { Pencil, Trash2, X, Users, UserPlus } from 'lucide-vue-next'
import { listEmployeeGroups, createEmployeeGroup, updateEmployeeGroup, deleteEmployeeGroup } from '../../services/employee-group.service'
import type { EmployeeGroup } from '../../services/employee-group.service'

const rows        = ref<EmployeeGroup[]>([])
const loading     = ref(false)
const drawerOpen  = ref(false)
const form        = ref<Partial<EmployeeGroup>>({ members: [] })
const selected    = ref<EmployeeGroup | null>(null)
const deleteTarget = ref<EmployeeGroup | null>(null)
const saving      = ref(false)
const deleting    = ref(false)
const errorMsg    = ref('')
const newMemberId = ref('')

const columns = [
  { key: 'name',         label: 'Group Name'    },
  { key: 'member_count', label: 'Members'       },
]

async function load() {
  loading.value = true
  try {
    const groups = await listEmployeeGroups()
    rows.value = groups.map(g => ({ ...g, member_count: g.members?.length ?? 0 }))
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}
onMounted(load)

function openCreate() {
  selected.value = null
  form.value = { members: [] }
  newMemberId.value = ''
  errorMsg.value = ''
  drawerOpen.value = true
}

function openEdit(row: EmployeeGroup) {
  selected.value = row
  form.value = { ...row, members: [...(row.members ?? [])] }
  newMemberId.value = ''
  errorMsg.value = ''
  drawerOpen.value = true
}

function addMember() {
  const id = newMemberId.value.trim()
  if (!id) return
  if (form.value.members?.some(m => m.employee_id === id)) {
    errorMsg.value = 'This employee is already in the group.'
    return
  }
  form.value.members = [...(form.value.members ?? []), { employee_id: id }]
  newMemberId.value = ''
  errorMsg.value = ''
}

function removeMember(id: string) {
  form.value.members = form.value.members?.filter(m => m.employee_id !== id)
}

async function save() {
  if (!form.value.name?.trim()) { errorMsg.value = 'Group name is required.'; return }
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateEmployeeGroup(selected.value.id, form.value)
    else await createEmployeeGroup(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try { await deleteEmployeeGroup(deleteTarget.value.id); deleteTarget.value = null; load() }
  catch (e) { console.error(e) }
  finally { deleting.value = false }
}

function shortId(id: string) {
  return id.length > 12 ? id.slice(0, 8) + '…' : id
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Employee Groups"
      subtitle="Organize employees into groups for bulk policy assignments and management"
      action-label="Add Group"
      @action="openCreate"
    />

    <DataTable
      :columns="columns"
      :rows="rows"
      :loading="loading"
      :searchable="true"
      empty-text="No employee groups found. Add your first group to get started."
    >
      <template #cell-name="{ value }">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
            <Users class="w-4 h-4 text-indigo-500" />
          </div>
          <span class="font-medium text-slate-900">{{ value }}</span>
        </div>
      </template>

      <template #cell-member_count="{ value }">
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-600">
          <Users class="w-3 h-3" />
          {{ value }} {{ value === 1 ? 'member' : 'members' }}
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
      :title="selected ? 'Edit Employee Group' : 'Add Employee Group'"
      width="w-full max-w-lg"
      @close="drawerOpen = false"
    >
      <div class="space-y-5 py-2">
        <p class="text-sm text-slate-500">
          {{ selected ? 'Update the group name or manage its members.' : 'Create a new employee group and add members by their Employee ID.' }}
        </p>

        <FormInput
          label="Group Name"
          v-model="form.name"
          required
          placeholder="e.g. Engineering Team, Night Shift, Mumbai Office"
        />

        <!-- Members -->
        <div class="space-y-3 pt-2 border-t border-slate-100">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Members ({{ form.members?.length ?? 0 }})
          </p>

          <div class="flex gap-2">
            <input
              v-model="newMemberId"
              @keydown.enter.prevent="addMember"
              type="text"
              placeholder="Paste Employee ID and press Enter or click Add"
              class="flex-1 border border-slate-200 bg-white text-slate-900 text-sm rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
            />
            <Button @click="addMember" type="button" variant="outline" class="shrink-0 gap-1.5">
              <UserPlus class="w-4 h-4" /> Add
            </Button>
          </div>

          <!-- Member list -->
          <div v-if="form.members?.length" class="space-y-1.5 max-h-64 overflow-y-auto pr-1">
            <div
              v-for="m in form.members"
              :key="m.employee_id"
              class="group flex items-center justify-between px-3 py-2.5 bg-slate-50 hover:bg-white border border-slate-200 rounded-lg transition-colors"
            >
              <div class="flex items-center gap-3">
                <div class="h-7 w-7 rounded-md bg-indigo-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
                  {{ (m.employee_name || m.employee_id).slice(0, 2).toUpperCase() }}
                </div>
                <div>
                  <p class="text-sm font-medium text-slate-800">
                    {{ m.employee_name || 'Employee' }}
                  </p>
                  <p class="text-xs text-slate-400 font-mono">{{ shortId(m.employee_id) }}</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                @click="removeMember(m.employee_id)"
                class="h-7 w-7 opacity-0 group-hover:opacity-100 text-slate-400 hover:text-destructive transition-all"
              >
                <X class="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>

          <div v-else class="text-center py-6 border border-dashed border-slate-200 rounded-lg">
            <Users class="w-6 h-6 text-slate-300 mx-auto mb-2" />
            <p class="text-xs text-slate-400">No members added yet.</p>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-3">
          <p v-if="errorMsg" class="text-sm text-destructive">{{ errorMsg }}</p>
          <div class="flex gap-2 ml-auto">
            <Button variant="outline" @click="drawerOpen = false">Cancel</Button>
            <Button @click="save" :disabled="saving">
              {{ saving ? 'Saving…' : selected ? 'Save Changes' : 'Add Group' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Employee Group?"
      :message="`Are you sure you want to delete the group '${deleteTarget?.name}'? Members will be removed from the group.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
