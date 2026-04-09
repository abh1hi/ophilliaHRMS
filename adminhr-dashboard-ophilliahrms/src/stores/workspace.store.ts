import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  listWorkspaces,
  getWorkspace,
  createWorkspace,
  updateWorkspace,
  deleteWorkspace,
  listMembers,
  addMember,
  updateMember,
  removeMember,
  type Workspace,
  type WorkspaceMember,
  type WorkspaceCreate,
  type WorkspaceUpdate,
  type AddMemberPayload,
  type UpdateMemberPayload,
} from '@/services/calendar-workspace.service'

export const useWorkspaceStore = defineStore('workspace', () => {
  const workspaces = ref<Workspace[]>([])
  const currentWorkspace = ref<Workspace | null>(null)
  const members = ref<WorkspaceMember[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const currentWorkspaceId = computed(() => currentWorkspace.value?.id)

  async function fetchWorkspaces() {
    loading.value = true
    error.value = null
    try {
      workspaces.value = (await listWorkspaces()) ?? []
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load workspaces'
    } finally {
      loading.value = false
    }
  }

  async function selectWorkspace(id: string) {
    loading.value = true
    error.value = null
    try {
      currentWorkspace.value = await getWorkspace(id) ?? null
      if (currentWorkspace.value) {
        members.value = (await listMembers(id)) ?? []
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load workspace'
    } finally {
      loading.value = false
    }
  }

  async function create(payload: WorkspaceCreate) {
    const ws = await createWorkspace(payload)
    if (ws) workspaces.value.unshift(ws)
    return ws
  }

  async function update(id: string, payload: WorkspaceUpdate) {
    const ws = await updateWorkspace(id, payload)
    if (ws) {
      const idx = workspaces.value.findIndex(w => w.id === id)
      if (idx !== -1) workspaces.value[idx] = ws
      if (currentWorkspace.value?.id === id) currentWorkspace.value = ws
    }
    return ws
  }

  async function remove(id: string) {
    await deleteWorkspace(id)
    workspaces.value = workspaces.value.filter(w => w.id !== id)
    if (currentWorkspace.value?.id === id) currentWorkspace.value = null
  }

  async function fetchMembers(workspaceId: string) {
    members.value = (await listMembers(workspaceId)) ?? []
  }

  async function addWorkspaceMember(workspaceId: string, payload: AddMemberPayload) {
    const m = await addMember(workspaceId, payload)
    if (m) members.value.push(m)
    return m
  }

  async function updateWorkspaceMember(workspaceId: string, employeeId: string, payload: UpdateMemberPayload) {
    const m = await updateMember(workspaceId, employeeId, payload)
    if (m) {
      const idx = members.value.findIndex(x => x.employee_id === employeeId)
      if (idx !== -1) members.value[idx] = m
    }
    return m
  }

  async function removeWorkspaceMember(workspaceId: string, employeeId: string) {
    await removeMember(workspaceId, employeeId)
    members.value = members.value.filter(m => m.employee_id !== employeeId)
  }

  return {
    workspaces,
    currentWorkspace,
    currentWorkspaceId,
    members,
    loading,
    error,
    fetchWorkspaces,
    selectWorkspace,
    create,
    update,
    remove,
    fetchMembers,
    addWorkspaceMember,
    updateWorkspaceMember,
    removeWorkspaceMember,
  }
})
