import { apiFetchData } from './http'

export interface Branch {
  id: string
  company_id: string
  name: string
  is_active: number
  created_at?: string
  updated_at?: string
}

export async function listBranches(): Promise<Branch[]> {
  return apiFetchData<Branch[]>('/branches')
}

export async function createBranch(payload: { name: string }): Promise<Branch> {
  return apiFetchData<Branch>('/branches', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateBranch(id: string, payload: { name?: string; is_active?: number }): Promise<Branch> {
  return apiFetchData<Branch>(`/branches/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteBranch(id: string): Promise<void> {
  await apiFetchData<Branch>(`/branches/${id}`, { method: 'DELETE' })
}
