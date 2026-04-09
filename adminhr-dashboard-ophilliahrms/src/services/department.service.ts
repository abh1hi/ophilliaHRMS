import { apiFetchData } from './http'

export interface Department {
  id: string
  company_id: string
  name: string
  description?: string
  manager_id?: string
  is_group: number
  parent_department_id?: string
  leave_block_list?: string
  is_active: number
  created_at?: string
  updated_at?: string
}

export async function listDepartments(): Promise<Department[]> {
  return apiFetchData<Department[]>('/departments')
}

export async function getDepartment(id: string): Promise<Department> {
  return apiFetchData<Department>(`/departments/${id}`)
}

export async function createDepartment(payload: Partial<Department>): Promise<Department> {
  return apiFetchData<Department>('/departments', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateDepartment(id: string, payload: Partial<Department>): Promise<Department> {
  return apiFetchData<Department>(`/departments/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteDepartment(id: string): Promise<void> {
  await apiFetchData<Department>(`/departments/${id}`, { method: 'DELETE' })
}
