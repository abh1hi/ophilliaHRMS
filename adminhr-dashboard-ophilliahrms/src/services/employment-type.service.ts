import { apiFetchData } from './http'

// ─── Types ────────────────────────────────────────────────────────────────────
export interface EmploymentType {
  id: string
  name: string
  created_at?: string
}

// ─── Employment Type API ──────────────────────────────────────────────────────
export async function listEmploymentTypes(): Promise<EmploymentType[]> {
  return apiFetchData<EmploymentType[]>('/employment-types')
}

export async function createEmploymentType(payload: Partial<EmploymentType>): Promise<EmploymentType> {
  return apiFetchData<EmploymentType>('/employment-types', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateEmploymentType(id: string, payload: Partial<EmploymentType>): Promise<EmploymentType> {
  return apiFetchData<EmploymentType>(`/employment-types/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteEmploymentType(id: string): Promise<void> {
  await apiFetchData<null>(`/employment-types/${id}`, { method: 'DELETE' })
}
