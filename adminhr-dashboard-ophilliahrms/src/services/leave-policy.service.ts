import { apiFetchData } from './http'

const BASE = '/leave/leave-policies'

export interface LeavePolicyItem {
  id: string
  policy_id: string
  leave_type_id: string
  annual_allocation: number
  created_at?: string
}

export interface LeavePolicy {
  id: string
  company_id: string
  name: string
  description?: string
  is_active: number
  items: LeavePolicyItem[]
  created_at?: string
  updated_at?: string
}

export interface LeavePolicyAssignment {
  id: string
  company_id: string
  employee_id: string
  policy_id: string
  leave_period_id?: string
  assignment_based_on?: string
  effective_from?: string
  effective_to?: string
  status: 'active' | 'cancelled'
  created_at?: string
  updated_at?: string
}

export async function listLeavePolicies(includeInactive = false): Promise<LeavePolicy[]> {
  return apiFetchData<LeavePolicy[]>(`${BASE}/?include_inactive=${includeInactive}`)
}

export async function getLeavePolicy(id: string): Promise<LeavePolicy> {
  return apiFetchData<LeavePolicy>(`${BASE}/${id}`)
}

export async function createLeavePolicy(payload: Partial<LeavePolicy>): Promise<LeavePolicy> {
  return apiFetchData<LeavePolicy>(`${BASE}/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateLeavePolicy(id: string, payload: Partial<LeavePolicy>): Promise<LeavePolicy> {
  return apiFetchData<LeavePolicy>(`${BASE}/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function listLeavePolicyAssignments(employeeId?: string): Promise<LeavePolicyAssignment[]> {
  const q = employeeId ? `?employee_id=${employeeId}` : ''
  return apiFetchData<LeavePolicyAssignment[]>(`${BASE}/assignments/${q}`)
}

export async function assignLeavePolicy(payload: Partial<LeavePolicyAssignment>): Promise<LeavePolicyAssignment> {
  return apiFetchData<LeavePolicyAssignment>(`${BASE}/assignments/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function cancelLeavePolicyAssignment(assignmentId: string): Promise<LeavePolicyAssignment> {
  return apiFetchData<LeavePolicyAssignment>(`${BASE}/assignments/${assignmentId}/cancel`, {
    method: 'PATCH',
  })
}
