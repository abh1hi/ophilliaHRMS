import { apiFetchData } from './http'

export interface ShiftSchedule {
  id: string
  company_id: string
  name: string
  description?: string
  effective_from?: string
  effective_to?: string
  is_active: number
  created_at?: string
  updated_at?: string
}

export async function listShiftSchedules(): Promise<ShiftSchedule[]> {
  return apiFetchData<ShiftSchedule[]>('/shift-schedules')
}

export async function createShiftSchedule(payload: Partial<ShiftSchedule>): Promise<ShiftSchedule> {
  return apiFetchData<ShiftSchedule>('/shift-schedules', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateShiftSchedule(id: string, payload: Partial<ShiftSchedule>): Promise<ShiftSchedule> {
  return apiFetchData<ShiftSchedule>(`/shift-schedules/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteShiftSchedule(id: string): Promise<void> {
  await apiFetchData<void>(`/shift-schedules/${id}`, { method: 'DELETE' })
}
