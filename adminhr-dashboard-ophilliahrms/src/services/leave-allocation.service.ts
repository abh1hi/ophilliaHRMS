import { apiFetchData } from './http'

const BASE = '/leave-allocations'

export interface LeaveAllocation {
  id: string
  company_id: string
  employee_id: string
  leave_type_id: string
  assignment_id?: string
  leave_period_id?: string
  from_date: string
  to_date: string
  new_leaves_allocated: number
  carry_forward_days: number
  total_leaves_allocated: number
  used_leaves: number
  leaves_pending_approval: number
  status: 'active' | 'expired' | 'cancelled'
  created_at?: string
  updated_at?: string
}

export interface LeaveAllocationList {
  total: number
  skip: number
  limit: number
  allocations: LeaveAllocation[]
}

export interface LeaveAdjustment {
  id: string
  company_id: string
  employee_id: string
  allocation_id: string
  adjustment_type: 'allocate' | 'reduce'
  adjustment_days: number
  reason?: string
  adjusted_by?: string
  adjustment_date?: string
  created_at?: string
}

export async function listLeaveAllocations(params?: {
  employee_id?: string
  leave_type_id?: string
  leave_period_id?: string
  status?: string
  skip?: number
  limit?: number
}): Promise<LeaveAllocationList> {
  const q = new URLSearchParams()
  if (params) Object.entries(params).forEach(([k, v]) => v !== undefined && q.set(k, String(v)))
  return apiFetchData<LeaveAllocationList>(`${BASE}/?${q}`)
}

export async function getLeaveAllocation(id: string): Promise<LeaveAllocation> {
  return apiFetchData<LeaveAllocation>(`${BASE}/${id}`)
}

export async function createLeaveAllocation(payload: Partial<LeaveAllocation>): Promise<LeaveAllocation> {
  return apiFetchData<LeaveAllocation>(`${BASE}/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateLeaveAllocation(id: string, payload: Partial<LeaveAllocation>): Promise<LeaveAllocation> {
  return apiFetchData<LeaveAllocation>(`${BASE}/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function adjustLeaveAllocation(
  allocationId: string,
  payload: { allocation_id: string; adjustment_type: 'allocate' | 'reduce'; adjustment_days: number; reason?: string }
): Promise<LeaveAdjustment> {
  return apiFetchData<LeaveAdjustment>(`${BASE}/${allocationId}/adjust`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
