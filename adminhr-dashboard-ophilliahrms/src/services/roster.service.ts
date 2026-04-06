import { apiFetchData } from './http'
import type { ShiftAssignment } from './shift-assignment.service'

export type RosterEntry = ShiftAssignment

export async function getRoster(from_date: string, to_date: string, employee_id?: string): Promise<RosterEntry[]> {
  const params = new URLSearchParams({ from_date, to_date })
  if (employee_id) params.set('employee_id', employee_id)
  return apiFetchData<RosterEntry[]>(`/roster?${params.toString()}`)
}
