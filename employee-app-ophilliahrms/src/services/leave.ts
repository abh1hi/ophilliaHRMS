import { authHeaders } from './api'

const API_BASE = '/api/v1'

async function handleResponse<T>(res: Response): Promise<T> {
  const body = await res.json()
  if (!res.ok) {
    const msg = body?.error?.message ?? body?.detail ?? `Error ${res.status}`
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  return (body?.data ?? body) as T
}

export interface LeaveType {
  id: string
  name: string
  description?: string
  days_allowed: number
  requires_approval: boolean
}

export interface LeaveBalance {
  id: string
  employee_id: string
  leave_type_id: string
  total_days: number
  used_days: number
  pending_days: number
  year: number
  leave_type: LeaveType
}

export interface LeaveRequest {
  id: string
  employee_id: string
  leave_type_id: string
  start_date: string
  end_date: string
  duration_type: 'FULL_DAY' | 'HALF_DAY'
  is_emergency: boolean
  reason: string
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED'
  total_days: number
  manager_notes?: string
  created_at: string
  leave_type: LeaveType
}

export async function getLeaveTypes(): Promise<LeaveType[]> {
  const res = await fetch(`${API_BASE}/leave/types/`, { headers: authHeaders() })
  const data = await handleResponse<any>(res)
  return Array.isArray(data) ? data : (data.items ?? data.types ?? [])
}

export async function getLeaveBalances(employeeId: string): Promise<LeaveBalance[]> {
  const res = await fetch(`${API_BASE}/leave/balances/${employeeId}`, { headers: authHeaders() })
  const data = await handleResponse<any>(res)
  return Array.isArray(data) ? data : (data.items ?? data.balances ?? [])
}

export async function getLeaveHistory(page = 1): Promise<{ items: LeaveRequest[], meta: any }> {
  const res = await fetch(`${API_BASE}/leave/requests/?page=${page}`, { headers: authHeaders() })
  const data = await handleResponse<any>(res)
  return { items: Array.isArray(data) ? data : (data.items ?? []), meta: data.meta ?? {} }
}

export async function applyForLeave(payload: {
  employee_id: string
  leave_type_id: string
  start_date: string
  end_date: string
  duration_type: string
  is_emergency: boolean
  reason: string
}): Promise<LeaveRequest> {
  const res = await fetch(`${API_BASE}/leave/requests/`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  })
  return handleResponse<LeaveRequest>(res)
}
