import { apiFetchData } from './http'

// ─── Types ────────────────────────────────────────────────────────────────────
export interface EmployeeGroupMember {
  employee_id: string
  employee_name?: string
}

export interface EmployeeGroup {
  id: string
  name: string
  members?: EmployeeGroupMember[]
  created_at?: string
}

// ─── Employee Group API ───────────────────────────────────────────────────────
export async function listEmployeeGroups(): Promise<EmployeeGroup[]> {
  return apiFetchData<EmployeeGroup[]>('/employee-groups')
}

export async function createEmployeeGroup(payload: Partial<EmployeeGroup>): Promise<EmployeeGroup> {
  return apiFetchData<EmployeeGroup>('/employee-groups', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateEmployeeGroup(id: string, payload: Partial<EmployeeGroup>): Promise<EmployeeGroup> {
  return apiFetchData<EmployeeGroup>(`/employee-groups/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteEmployeeGroup(id: string): Promise<void> {
  await apiFetchData<null>(`/employee-groups/${id}`, { method: 'DELETE' })
}
