import { apiFetchData } from './http'

export interface ShiftLocation {
  id: string
  company_id: string
  name: string
  address?: string
  latitude?: number
  longitude?: number
  radius_meters: number
  is_active: number
  created_at?: string
  updated_at?: string
}

export async function listShiftLocations(): Promise<ShiftLocation[]> {
  return apiFetchData<ShiftLocation[]>('/shift-locations')
}

export async function createShiftLocation(payload: Partial<ShiftLocation>): Promise<ShiftLocation> {
  return apiFetchData<ShiftLocation>('/shift-locations', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateShiftLocation(id: string, payload: Partial<ShiftLocation>): Promise<ShiftLocation> {
  return apiFetchData<ShiftLocation>(`/shift-locations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteShiftLocation(id: string): Promise<void> {
  await apiFetchData<void>(`/shift-locations/${id}`, { method: 'DELETE' })
}
