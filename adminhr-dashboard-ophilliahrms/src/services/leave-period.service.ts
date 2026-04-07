import { apiFetchData } from './http'

const BASE = '/leave-periods'

export interface LeavePeriod {
  id: string
  company_id: string
  name: string
  from_date: string
  to_date: string
  is_active: number
  optional_holiday_list_id?: string
  created_at?: string
  updated_at?: string
}

export async function listLeavePeriods(includeInactive = false): Promise<LeavePeriod[]> {
  return apiFetchData<LeavePeriod[]>(`${BASE}/?include_inactive=${includeInactive}`)
}

export async function getLeavePeriod(id: string): Promise<LeavePeriod> {
  return apiFetchData<LeavePeriod>(`${BASE}/${id}`)
}

export async function createLeavePeriod(payload: Partial<LeavePeriod>): Promise<LeavePeriod> {
  return apiFetchData<LeavePeriod>(`${BASE}/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateLeavePeriod(id: string, payload: Partial<LeavePeriod>): Promise<LeavePeriod> {
  return apiFetchData<LeavePeriod>(`${BASE}/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteLeavePeriod(id: string): Promise<LeavePeriod> {
  return apiFetchData<LeavePeriod>(`${BASE}/${id}`, { method: 'DELETE' })
}
