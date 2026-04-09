import { apiFetchData } from './http'

export interface Designation {
  id: string
  company_id: string
  name: string
  description?: string
  required_skills?: string[]
  is_active: number
  created_at?: string
  updated_at?: string
}

export async function listDesignations(): Promise<Designation[]> {
  return apiFetchData<Designation[]>('/designations')
}

export async function createDesignation(payload: Partial<Designation>): Promise<Designation> {
  return apiFetchData<Designation>('/designations', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateDesignation(id: string, payload: Partial<Designation>): Promise<Designation> {
  return apiFetchData<Designation>(`/designations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteDesignation(id: string): Promise<void> {
  await apiFetchData<Designation>(`/designations/${id}`, { method: 'DELETE' })
}
