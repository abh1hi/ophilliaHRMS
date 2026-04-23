import { apiFetchAuth } from './http'

export interface ShiftLocation {
  id: string
  company_id: string
  name: string
  address?: string
  latitude?: number
  longitude?: number
  radius_meters: number
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export async function listShiftLocations(): Promise<ShiftLocation[]> {
  const res = await apiFetchAuth<{ total: number; geofences: ShiftLocation[] }>('/attendance/geofences')
  return res.geofences ?? []
}

export async function createShiftLocation(payload: Partial<ShiftLocation>): Promise<ShiftLocation> {
  const { name, latitude, longitude, radius_meters, address, is_active } = payload
  return apiFetchAuth<ShiftLocation>('/attendance/geofences', {
    method: 'POST',
    body: JSON.stringify({ name, latitude, longitude, radius_meters, address, is_active }),
  })
}

export async function updateShiftLocation(id: string, payload: Partial<ShiftLocation>): Promise<ShiftLocation> {
  const { name, latitude, longitude, radius_meters, address, is_active } = payload
  return apiFetchAuth<ShiftLocation>(`/attendance/geofences/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ name, latitude, longitude, radius_meters, address, is_active }),
  })
}

export async function deleteShiftLocation(id: string): Promise<void> {
  await apiFetchAuth<void>(`/attendance/geofences/${id}`, { method: 'DELETE' })
}
