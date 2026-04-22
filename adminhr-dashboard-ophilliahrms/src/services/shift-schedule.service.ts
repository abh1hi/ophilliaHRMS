import { apiFetchData } from './http'

export interface ShiftSchedule {
  id: string
  company_id: string
  name: string
  description?: string
  shift_type_id: string
  allowed_clock_in_location_ids: string[]
  allowed_clock_out_location_ids: string[]
  clock_in_start_time: string
  clock_in_end_time: string
  clock_out_start_time: string
  clock_out_end_time: string
  auto_clock_out_enabled: boolean
  auto_clock_out_time: string | null
  tasks_mandatory: boolean
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
