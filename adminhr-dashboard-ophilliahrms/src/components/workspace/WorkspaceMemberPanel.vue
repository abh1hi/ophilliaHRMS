<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/40" @click="emit('close')" />
        <div class="relative w-full max-w-md bg-white h-full shadow-xl flex flex-col">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
            <h2 class="text-lg font-semibold text-slate-800">Manage Members</h2>
            <button @click="emit('close')" class="p-1.5 rounded-lg hover:bg-slate-100">
              <XIcon class="w-5 h-5 text-slate-500" />
            </button>
          </div>

          <!-- Add member -->
          <div class="px-6 py-4 border-b border-slate-100">
            <p class="text-sm font-medium text-slate-700 mb-3">Add Member</p>
            <div class="flex gap-2">
              <input
                v-model="newEmployeeId"
                type="text"
                placeholder="Employee ID"
                class="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
              <select
                v-model="newRole"
                class="px-2 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
                <option value="viewer">Viewer</option>
              </select>
              <button
                @click="addMember"
                :disabled="!newEmployeeId.trim() || adding"
                class="px-3 py-2 bg-slate-900 text-white text-sm rounded-lg hover:bg-slate-700 disabled:opacity-50"
              >
                <PlusIcon class="w-4 h-4" />
              </button>
            </div>
            <p v-if="addError" class="mt-2 text-xs text-red-500">{{ addError }}</p>
          </div>

          <!-- Member list -->
          <div class="flex-1 overflow-y-auto px-6 py-4 space-y-2">
            <div
              v-for="member in store.members"
              :key="member.id"
              class="flex items-center justify-between py-2.5 px-3 rounded-lg border border-slate-100 bg-slate-50"
            >
              <div>
                <p class="text-sm font-medium text-slate-800">{{ member.employee_id }}</p>
                <p class="text-xs text-slate-500 capitalize">{{ member.role }}</p>
              </div>
              <div class="flex items-center gap-2">
                <select
                  :value="member.role"
                  @change="changeRole(member.employee_id, ($event.target as HTMLSelectElement).value)"
                  :disabled="member.role === 'owner'"
                  class="text-xs border border-slate-200 rounded px-1.5 py-1 disabled:opacity-40"
                >
                  <option value="owner" disabled>Owner</option>
                  <option value="admin">Admin</option>
                  <option value="member">Member</option>
                  <option value="viewer">Viewer</option>
                </select>
                <button
                  v-if="member.role !== 'owner'"
                  @click="removeMember(member.employee_id)"
                  class="p-1 rounded hover:bg-red-50 text-red-400 hover:text-red-600"
                >
                  <TrashIcon class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
            <p v-if="!store.members.length" class="text-sm text-slate-400 text-center py-8">No members yet.</p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { XIcon, PlusIcon, TrashIcon } from 'lucide-vue-next'
import { useWorkspaceStore } from '@/stores/workspace.store'

interface Props {
  open: boolean
  workspaceId: string
}

const props = defineProps<Props>()
const emit = defineEmits<{ (e: 'close'): void }>()

const store = useWorkspaceStore()
const newEmployeeId = ref('')
const newRole = ref<'admin' | 'member' | 'viewer'>('member')
const adding = ref(false)
const addError = ref<string | null>(null)

async function addMember() {
  if (!newEmployeeId.value.trim()) return
  adding.value = true
  addError.value = null
  try {
    await store.addWorkspaceMember(props.workspaceId, {
      employee_id: newEmployeeId.value.trim(),
      role: newRole.value,
    })
    newEmployeeId.value = ''
  } catch (e: unknown) {
    addError.value = e instanceof Error ? e.message : 'Failed to add member'
  } finally {
    adding.value = false
  }
}

async function changeRole(employeeId: string, role: string) {
  await store.updateWorkspaceMember(props.workspaceId, employeeId, {
    role: role as 'admin' | 'member' | 'viewer',
  })
}

async function removeMember(employeeId: string) {
  await store.removeWorkspaceMember(props.workspaceId, employeeId)
}
</script>

<style scoped>
.drawer-enter-active,
.drawer-leave-active { transition: opacity 0.25s; }
.drawer-enter-from,
.drawer-leave-to { opacity: 0; }
</style>
