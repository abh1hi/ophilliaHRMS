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
  off_days?: string[]
  break_window_start?: string | null
  break_window_end?: string | null
  validity_start?: string | null
  validity_end?: string | null
  validity_auto_extended?: boolean
  assigned_employee_ids?: string[]
  effective_from?: string
  effective_to?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface ShiftScheduleAssignment {
  id: string
  schedule_id: string
  employee_id: string
  effective_from: string
  effective_to?: string | null
  notes?: string | null
  is_active: number
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

export async function listShiftScheduleAssignments(scheduleId?: string): Promise<ShiftScheduleAssignment[]> {
  const params = new URLSearchParams()
  if (scheduleId) params.set('schedule_id', scheduleId)
  const suffix = params.toString() ? `?${params.toString()}` : ''
  return apiFetchData<ShiftScheduleAssignment[]>(`/shift-schedule-assignments${suffix}`)
}

export async function createShiftScheduleAssignment(payload: {
  schedule_id: string
  employee_id: string
  effective_from: string
  effective_to?: string
  notes?: string
}): Promise<ShiftScheduleAssignment> {
  return apiFetchData<ShiftScheduleAssignment>('/shift-schedule-assignments', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function deleteShiftScheduleAssignment(id: string): Promise<void> {
  await apiFetchData<void>(`/shift-schedule-assignments/${id}`, { method: 'DELETE' })
}
