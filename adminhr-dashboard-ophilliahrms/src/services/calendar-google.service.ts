import { apiFetchData } from './http'

const BASE = '/calendar/google'

export interface GoogleIntegration {
  id: string
  company_id: string
  employee_id: string
  google_email?: string
  status: 'active' | 'revoked' | 'expired'
  connected_calendars: { id: string; summary: string; primary: boolean }[]
  last_synced_at?: string
  sync_error_count: number
  created_at: string
  updated_at: string
}

export interface GoogleCalendarItem {
  id: string
  summary: string
  description?: string
  primary: boolean
  accessRole: string
  backgroundColor?: string
}

export interface AuthUrlResponse {
  auth_url: string
}

export const getAuthUrl = () =>
  apiFetchData<AuthUrlResponse>(`${BASE}/auth/url`)

export const getIntegrationStatus = () =>
  apiFetchData<GoogleIntegration>(`${BASE}/status`)

export const listGoogleCalendars = () =>
  apiFetchData<GoogleCalendarItem[]>(`${BASE}/calendars`)

export const connectCalendars = (calendarIds: string[]) =>
  apiFetchData<GoogleIntegration>(`${BASE}/calendars/connect`, {
    method: 'POST',
    body: JSON.stringify({ calendar_ids: calendarIds }),
  })

export const triggerCalendarSync = () =>
  apiFetchData<{ synced: number; failed: number }>(`${BASE}/sync/calendar`, { method: 'POST' })

export const triggerTaskSync = () =>
  apiFetchData<{ synced: number; failed: number }>(`${BASE}/sync/tasks`, { method: 'POST' })

export const disconnectGoogle = () =>
  apiFetchData<void>(`${BASE}/disconnect`, { method: 'DELETE' })
