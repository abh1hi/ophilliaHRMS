import { apiFetchData } from './http'

export interface OvertimeRequest {
  id: string
  company_id: string
  employee_id: string
  date: string
  requested_hours: number
  reason: string
  status: 'pending' | 'approved' | 'rejected'
  reviewed_by?: string
  review_note?: string
  created_at: string
  updated_at: string
}

export async function listOvertimeRequests(params?: {
  employee_id?: string
  status?: string
}): Promise<OvertimeRequest[]> {
  const q = new URLSearchParams()
  if (params?.employee_id) q.set('employee_id', params.employee_id)
  if (params?.status)      q.set('status', params.status)
  const qs = q.toString() ? `?${q.toString()}` : ''
  return apiFetchData<OvertimeRequest[]>(`/overtime/requests${qs}`)
}

export async function submitOvertimeRequest(payload: {
  date: string
  requested_hours: number
  reason: string
}): Promise<OvertimeRequest> {
  return apiFetchData<OvertimeRequest>('/overtime/requests', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function reviewOvertimeRequest(
  id: string,
  status: 'approved' | 'rejected',
  review_note?: string,
): Promise<OvertimeRequest> {
  return apiFetchData<OvertimeRequest>(`/overtime/requests/${id}/review`, {
    method: 'PATCH',
    body: JSON.stringify({ status, review_note }),
  })
}

export async function cancelOvertimeRequest(id: string): Promise<void> {
  await apiFetchData<void>(`/overtime/requests/${id}`, { method: 'DELETE' })
}
