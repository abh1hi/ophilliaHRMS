import { apiFetchData } from './http'

const BASE = '/leave/compensatory-leave-requests'

export interface CompensatoryLeaveRequest {
  id: string
  company_id: string
  employee_id: string
  leave_type_id: string
  work_from_date: string
  work_end_date: string
  reason?: string
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  leave_allocation_id?: string
  reviewed_by?: string
  reviewed_at?: string
  review_note?: string
  created_at?: string
  updated_at?: string
}

export interface CompensatoryLeaveList {
  total: number
  skip: number
  limit: number
  requests: CompensatoryLeaveRequest[]
}

export async function listCompensatoryLeaveRequests(params?: {
  employee_id?: string
  status?: string
  skip?: number
  limit?: number
}): Promise<CompensatoryLeaveList> {
  const q = new URLSearchParams()
  if (params) Object.entries(params).forEach(([k, v]) => v !== undefined && q.set(k, String(v)))
  return apiFetchData<CompensatoryLeaveList>(`${BASE}/?${q}`)
}

export async function getCompensatoryLeaveRequest(id: string): Promise<CompensatoryLeaveRequest> {
  return apiFetchData<CompensatoryLeaveRequest>(`${BASE}/${id}`)
}

export async function createCompensatoryLeaveRequest(
  payload: Partial<CompensatoryLeaveRequest>
): Promise<CompensatoryLeaveRequest> {
  return apiFetchData<CompensatoryLeaveRequest>(`${BASE}/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function reviewCompensatoryLeaveRequest(
  id: string,
  payload: { status: 'approved' | 'rejected'; review_note?: string }
): Promise<CompensatoryLeaveRequest> {
  return apiFetchData<CompensatoryLeaveRequest>(`${BASE}/${id}/review`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}
