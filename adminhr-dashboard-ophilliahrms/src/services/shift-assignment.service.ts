import { apiFetchData } from './http'

export interface ShiftAssignment {
  id: string
  company_id: string
  employee_id: string
  shift_type_id?: string
  shift_location_id?: string
  effective_from: string
  effective_to?: string
  is_active: number
  notes?: string
  created_at?: string
  updated_at?: string
}

export async function listShiftAssignments(employeeId?: string): Promise<ShiftAssignment[]> {
  const qs = employeeId ? `?employee_id=${employeeId}` : ''
  return apiFetchData<ShiftAssignment[]>(`/shift-assignments${qs}`)
}

export async function createShiftAssignment(payload: Partial<ShiftAssignment>): Promise<ShiftAssignment> {
  return apiFetchData<ShiftAssignment>('/shift-assignments', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateShiftAssignment(id: string, payload: Partial<ShiftAssignment>): Promise<ShiftAssignment> {
  return apiFetchData<ShiftAssignment>(`/shift-assignments/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteShiftAssignment(id: string): Promise<void> {
  await apiFetchData<void>(`/shift-assignments/${id}`, { method: 'DELETE' })
}
