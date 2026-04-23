import { apiFetchData } from './http'

export interface RosterEntry {
  id: string
  schedule_id: string
  employee_id: string
  effective_from: string
  effective_to?: string | null
  is_active: number
  notes?: string | null
}

export async function getRoster(from_date: string, to_date: string, employee_id?: string): Promise<RosterEntry[]> {
  const params = new URLSearchParams({ from_date, to_date })
  if (employee_id) params.set('employee_id', employee_id)
  return apiFetchData<RosterEntry[]>(`/roster?${params.toString()}`)
}
