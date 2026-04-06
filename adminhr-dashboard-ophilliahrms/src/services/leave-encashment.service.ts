import { apiFetchData } from './http'

const BASE = '/leave/leave-encashments'

export interface LeaveEncashment {
  id: string
  company_id: string
  employee_id: string
  leave_type_id: string
  leave_period_id?: string
  leave_allocation_id?: string
  leave_balance: number
  encashable_days: number
  encashment_amount?: number
  encashment_date?: string
  status: 'submitted' | 'paid' | 'cancelled'
  created_at?: string
  updated_at?: string
}

export interface LeaveEncashmentList {
  total: number
  skip: number
  limit: number
  encashments: LeaveEncashment[]
}

export async function listLeaveEncashments(params?: {
  employee_id?: string
  skip?: number
  limit?: number
}): Promise<LeaveEncashmentList> {
  const q = new URLSearchParams()
  if (params) Object.entries(params).forEach(([k, v]) => v !== undefined && q.set(k, String(v)))
  return apiFetchData<LeaveEncashmentList>(`${BASE}/?${q}`)
}

export async function getLeaveEncashment(id: string): Promise<LeaveEncashment> {
  return apiFetchData<LeaveEncashment>(`${BASE}/${id}`)
}

export async function createLeaveEncashment(payload: Partial<LeaveEncashment>): Promise<LeaveEncashment> {
  return apiFetchData<LeaveEncashment>(`${BASE}/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function cancelLeaveEncashment(id: string): Promise<LeaveEncashment> {
  return apiFetchData<LeaveEncashment>(`${BASE}/${id}/cancel`, { method: 'PATCH' })
}
