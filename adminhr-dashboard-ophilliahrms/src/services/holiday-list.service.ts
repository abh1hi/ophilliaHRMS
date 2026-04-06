import { apiFetchData } from './http'

const BASE = '/leave/holiday-lists'

export interface HolidayListEntry {
  id: string
  holiday_list_id: string
  date: string
  description?: string
  created_at?: string
}

export interface HolidayList {
  id: string
  company_id: string
  name: string
  from_date: string
  to_date: string
  is_active: number
  entries: HolidayListEntry[]
  created_at?: string
  updated_at?: string
}

export interface HolidayListAssignment {
  id: string
  company_id: string
  applicable_for: 'company' | 'employee'
  employee_id?: string
  holiday_list_id: string
  assignment_from: string
  created_at?: string
}

export async function listHolidayLists(includeInactive = false): Promise<HolidayList[]> {
  return apiFetchData<HolidayList[]>(`${BASE}/?include_inactive=${includeInactive}`)
}

export async function getHolidayList(id: string): Promise<HolidayList> {
  return apiFetchData<HolidayList>(`${BASE}/${id}`)
}

export async function createHolidayList(payload: Partial<HolidayList>): Promise<HolidayList> {
  return apiFetchData<HolidayList>(`${BASE}/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateHolidayList(id: string, payload: Partial<HolidayList>): Promise<HolidayList> {
  return apiFetchData<HolidayList>(`${BASE}/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function addHolidayListEntries(
  listId: string,
  entries: Partial<HolidayListEntry>[]
): Promise<HolidayListEntry[]> {
  return apiFetchData<HolidayListEntry[]>(`${BASE}/${listId}/entries`, {
    method: 'POST',
    body: JSON.stringify(entries),
  })
}

export async function listHolidayListAssignments(): Promise<HolidayListAssignment[]> {
  return apiFetchData<HolidayListAssignment[]>(`${BASE}/assignments/`)
}

export async function createHolidayListAssignment(
  payload: Partial<HolidayListAssignment>
): Promise<HolidayListAssignment> {
  return apiFetchData<HolidayListAssignment>(`${BASE}/assignments/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
