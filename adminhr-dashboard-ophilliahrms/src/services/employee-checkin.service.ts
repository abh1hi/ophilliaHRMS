import { apiFetchData } from './http'

export interface EmployeeCheckin {
  id: string
  company_id: string
  employee_id: string
  log_datetime: string
  log_type: 'IN' | 'OUT'
  device_id?: string
  shift_type_id?: string
  latitude?: number
  longitude?: number
  location_name?: string
  skip_auto_attendance: number
  attendance_record_id?: string
  created_at: string
}

export interface CheckinListResponse {
  total: number
  skip: number
  limit: number
  checkins: EmployeeCheckin[]
}

export interface CheckinFilters {
  employee_id?: string
  from_dt?: string
  to_dt?: string
  log_type?: 'IN' | 'OUT'
  skip?: number
  limit?: number
}

export async function listCheckins(filters: CheckinFilters = {}): Promise<CheckinListResponse> {
  const params = new URLSearchParams()
  if (filters.employee_id) params.set('employee_id', filters.employee_id)
  if (filters.from_dt) params.set('from_dt', filters.from_dt)
  if (filters.to_dt) params.set('to_dt', filters.to_dt)
  if (filters.log_type) params.set('log_type', filters.log_type)
  if (filters.skip !== undefined) params.set('skip', String(filters.skip))
  if (filters.limit !== undefined) params.set('limit', String(filters.limit))
  const qs = params.toString() ? `?${params}` : ''
  return apiFetchData<CheckinListResponse>(`/attendance/checkins${qs}`)
}

export async function createCheckin(payload: Partial<EmployeeCheckin>): Promise<EmployeeCheckin> {
  return apiFetchData<EmployeeCheckin>('/attendance/checkins', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function fetchShiftForCheckin(id: string): Promise<EmployeeCheckin> {
  return apiFetchData<EmployeeCheckin>(`/attendance/checkins/${id}/fetch-shift`, { method: 'PATCH' })
}

export async function toggleCheckinSkip(id: string): Promise<EmployeeCheckin> {
  return apiFetchData<EmployeeCheckin>(`/attendance/checkins/${id}/skip`, { method: 'PATCH' })
}
