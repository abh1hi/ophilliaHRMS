import { apiFetchData } from './http'

export interface ShiftType {
  id: string
  company_id: string
  name: string
  start_time: string
  end_time: string
  work_hours_per_day?: number
  break_minutes: number
  grace_period_minutes: number
  is_night_shift: boolean
  color_code?: string
  description?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export async function listShiftTypes(): Promise<ShiftType[]> {
  return apiFetchData<ShiftType[]>('/shift-types')
}

export async function createShiftType(payload: Partial<ShiftType>): Promise<ShiftType> {
  return apiFetchData<ShiftType>('/shift-types', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateShiftType(id: string, payload: Partial<ShiftType>): Promise<ShiftType> {
  return apiFetchData<ShiftType>(`/shift-types/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteShiftType(id: string): Promise<ShiftType> {
  return apiFetchData<ShiftType>(`/shift-types/${id}`, { method: 'DELETE' })
}
