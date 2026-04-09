import { apiFetchData } from './http'

const BASE = '/calendar/workspaces'

export interface Workspace {
  id: string
  company_id: string
  name: string
  description?: string
  workspace_type: 'team' | 'project' | 'personal'
  color?: string
  icon?: string
  owner_id: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface WorkspaceMember {
  id: string
  workspace_id: string
  employee_id: string
  role: 'owner' | 'admin' | 'member' | 'viewer'
  joined_at: string
  invited_by?: string
}

export interface WorkspaceCreate {
  name: string
  description?: string
  workspace_type?: 'team' | 'project' | 'personal'
  color?: string
  icon?: string
}

export interface WorkspaceUpdate {
  name?: string
  description?: string
  color?: string
  icon?: string
  is_active?: boolean
}

export interface AddMemberPayload {
  employee_id: string
  role?: 'admin' | 'member' | 'viewer'
}

export interface UpdateMemberPayload {
  role: 'admin' | 'member' | 'viewer'
}

export const listWorkspaces = () =>
  apiFetchData<Workspace[]>(BASE)

export const getWorkspace = (id: string) =>
  apiFetchData<Workspace>(`${BASE}/${id}`)

export const createWorkspace = (payload: WorkspaceCreate) =>
  apiFetchData<Workspace>(BASE, { method: 'POST', body: JSON.stringify(payload) })

export const updateWorkspace = (id: string, payload: WorkspaceUpdate) =>
  apiFetchData<Workspace>(`${BASE}/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })

export const deleteWorkspace = (id: string) =>
  apiFetchData<void>(`${BASE}/${id}`, { method: 'DELETE' })

export const listMembers = (workspaceId: string) =>
  apiFetchData<WorkspaceMember[]>(`${BASE}/${workspaceId}/members`)

export const addMember = (workspaceId: string, payload: AddMemberPayload) =>
  apiFetchData<WorkspaceMember>(`${BASE}/${workspaceId}/members`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const updateMember = (workspaceId: string, employeeId: string, payload: UpdateMemberPayload) =>
  apiFetchData<WorkspaceMember>(`${BASE}/${workspaceId}/members/${employeeId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const removeMember = (workspaceId: string, employeeId: string) =>
  apiFetchData<void>(`${BASE}/${workspaceId}/members/${employeeId}`, { method: 'DELETE' })
