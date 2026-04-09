import { apiFetchData } from './http'

export interface ShiftRequest {
  id: string
  company_id: string
  employee_id: string
  request_type: 'swap' | 'change' | 'leave'
  from_date: string
  to_date: string
  requested_shift_type_id?: string
  reason?: string
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  reviewed_by?: string
  reviewed_at?: string
  review_note?: string
  created_at?: string
  updated_at?: string
}

export async function listShiftRequests(employeeId?: string, status?: string): Promise<ShiftRequest[]> {
  const params = new URLSearchParams()
  if (employeeId) params.set('employee_id', employeeId)
  if (status) params.set('status', status)
  const qs = params.toString() ? `?${params.toString()}` : ''
  return apiFetchData<ShiftRequest[]>(`/shift-requests${qs}`)
}

export async function createShiftRequest(payload: Partial<ShiftRequest>): Promise<ShiftRequest> {
  return apiFetchData<ShiftRequest>('/shift-requests', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateShiftRequest(id: string, payload: Partial<ShiftRequest>): Promise<ShiftRequest> {
  return apiFetchData<ShiftRequest>(`/shift-requests/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function reviewShiftRequest(id: string, payload: { status: 'approved' | 'rejected'; review_note?: string }): Promise<ShiftRequest> {
  return apiFetchData<ShiftRequest>(`/shift-requests/${id}/review`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function cancelShiftRequest(id: string): Promise<ShiftRequest> {
  return apiFetchData<ShiftRequest>(`/shift-requests/${id}`, { method: 'DELETE' })
}
