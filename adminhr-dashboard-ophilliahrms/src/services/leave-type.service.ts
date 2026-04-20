import { apiFetch, apiFetchData } from './http'

export interface LeaveType {
  id: string
  name: string
  days_allowed: number
  requires_approval: boolean
  is_active: boolean
  created_at: string
}

export const listLeaveTypes = (active_only = false) =>
  apiFetchData<LeaveType[]>(`/leave-types/?active_only=${active_only}`)

export const createLeaveType = (data: Partial<LeaveType>) =>
  apiFetchData<LeaveType>('/leave-types/', { method: 'POST', body: JSON.stringify(data) })

export const updateLeaveType = (id: string, data: Partial<LeaveType>) =>
  apiFetchData<LeaveType>(`/leave-types/${id}`, { method: 'PATCH', body: JSON.stringify(data) })

export const deleteLeaveType = (id: string) =>
  apiFetch(`/leave-types/${id}`, { method: 'DELETE' })
