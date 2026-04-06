import { apiFetchData } from './http'

export interface AttendanceRequest {
  id: string
  company_id: string
  employee_id: string
  from_date: string
  to_date: string
  reason: 'on_site_duty' | 'work_from_home' | 'other'
  explanation?: string
  include_holidays: number
  half_day: number
  half_day_date?: string
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  reviewed_by?: string
  reviewed_at?: string
  review_note?: string
  created_at: string
  updated_at: string
}

export interface AttendanceRequestListResponse {
  total: number
  skip: number
  limit: number
  requests: AttendanceRequest[]
}

export interface RequestFilters {
  employee_id?: string
  status?: string
  skip?: number
  limit?: number
}

export async function listAttendanceRequests(filters: RequestFilters = {}): Promise<AttendanceRequestListResponse> {
  const params = new URLSearchParams()
  if (filters.employee_id) params.set('employee_id', filters.employee_id)
  if (filters.status) params.set('status', filters.status)
  if (filters.skip !== undefined) params.set('skip', String(filters.skip))
  if (filters.limit !== undefined) params.set('limit', String(filters.limit))
  const qs = params.toString() ? `?${params}` : ''
  return apiFetchData<AttendanceRequestListResponse>(`/attendance/requests${qs}`)
}

export async function createAttendanceRequest(payload: Partial<AttendanceRequest>): Promise<AttendanceRequest> {
  return apiFetchData<AttendanceRequest>('/attendance/requests', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function cancelAttendanceRequest(id: string): Promise<AttendanceRequest> {
  return apiFetchData<AttendanceRequest>(`/attendance/requests/${id}/cancel`, { method: 'PATCH' })
}

export async function reviewAttendanceRequest(
  id: string,
  data: { status: 'approved' | 'rejected'; review_note?: string }
): Promise<AttendanceRequest> {
  return apiFetchData<AttendanceRequest>(`/attendance/requests/${id}/review`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}
