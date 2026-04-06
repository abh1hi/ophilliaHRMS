import { apiFetchData } from './http'

const BASE = '/leave/leave-block-lists'

export interface LeaveBlockListDate {
  id: string
  block_list_id: string
  block_date: string
  reason?: string
}

export interface LeaveBlockListAllowed {
  id: string
  block_list_id: string
  approver_employee_id: string
}

export interface LeaveBlockList {
  id: string
  company_id: string
  name: string
  applies_to_company: number
  is_active: number
  dates: LeaveBlockListDate[]
  allowed_users: LeaveBlockListAllowed[]
  created_at?: string
  updated_at?: string
}

export async function listLeaveBlockLists(includeInactive = false): Promise<LeaveBlockList[]> {
  return apiFetchData<LeaveBlockList[]>(`${BASE}/?include_inactive=${includeInactive}`)
}

export async function getLeaveBlockList(id: string): Promise<LeaveBlockList> {
  return apiFetchData<LeaveBlockList>(`${BASE}/${id}`)
}

export async function createLeaveBlockList(payload: Partial<LeaveBlockList>): Promise<LeaveBlockList> {
  return apiFetchData<LeaveBlockList>(`${BASE}/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateLeaveBlockList(id: string, payload: Partial<LeaveBlockList>): Promise<LeaveBlockList> {
  return apiFetchData<LeaveBlockList>(`${BASE}/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}
