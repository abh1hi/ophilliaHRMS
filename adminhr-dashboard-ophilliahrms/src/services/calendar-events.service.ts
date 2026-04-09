import { apiFetchData, apiFetchDirect } from './http'

const BASE_CAL = '/calendar/calendars'
const BASE_EVT = '/calendar/events'

export interface CalendarItem {
  id: string
  company_id: string
  workspace_id?: string
  name: string
  description?: string
  color?: string
  calendar_type: 'personal' | 'team' | 'company' | 'google_synced'
  owner_id: string
  is_default: boolean
  is_public: boolean
  google_calendar_id?: string
  public_share_token?: string
  created_at: string
  updated_at: string
}

export interface CalendarCreate {
  workspace_id?: string
  name: string
  description?: string
  color?: string
  calendar_type?: 'personal' | 'team' | 'company' | 'google_synced'
  is_public?: boolean
}

export interface CalendarUpdate {
  name?: string
  description?: string
  color?: string
  is_public?: boolean
  webhook_url?: string
}

export interface Attendee {
  employee_id: string
  rsvp_status: 'pending' | 'accepted' | 'declined' | 'tentative'
}

export interface CalendarEvent {
  id: string
  company_id: string
  calendar_id: string
  title: string
  description?: string
  location?: string
  event_type: 'meeting' | 'deadline' | 'reminder' | 'block' | 'holiday' | 'leave'
  start_time: string
  end_time: string
  all_day: boolean
  timezone: string
  rrule?: string
  recurrence_master_id?: string
  status: 'scheduled' | 'cancelled' | 'tentative'
  created_by: string
  attendees: Attendee[]
  color?: string
  reminder_minutes: number[]
  created_at: string
  updated_at: string
}

export interface EventCreate {
  calendar_id: string
  title: string
  description?: string
  location?: string
  event_type?: string
  start_time: string
  end_time: string
  all_day?: boolean
  timezone?: string
  rrule?: string
  attendees?: { employee_id: string }[]
  color?: string
  reminder_minutes?: number[]
}

export interface EventUpdate {
  title?: string
  description?: string
  location?: string
  event_type?: string
  start_time?: string
  end_time?: string
  all_day?: boolean
  timezone?: string
  rrule?: string
  color?: string
  reminder_minutes?: number[]
  status?: string
}

export interface RangeEvent extends CalendarEvent {
  recurrence_master_id?: string
}

// Calendars
export const listCalendars = (workspaceId?: string) =>
  apiFetchData<CalendarItem[]>(workspaceId ? `${BASE_CAL}?workspace_id=${workspaceId}` : BASE_CAL)

export const getCalendar = (id: string) =>
  apiFetchData<CalendarItem>(`${BASE_CAL}/${id}`)

export const createCalendar = (payload: CalendarCreate) =>
  apiFetchData<CalendarItem>(BASE_CAL, { method: 'POST', body: JSON.stringify(payload) })

export const updateCalendar = (id: string, payload: CalendarUpdate) =>
  apiFetchData<CalendarItem>(`${BASE_CAL}/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })

export const deleteCalendar = (id: string) =>
  apiFetchData<void>(`${BASE_CAL}/${id}`, { method: 'DELETE' })

export const shareCalendar = (id: string) =>
  apiFetchData<{ share_url: string; token: string }>(`${BASE_CAL}/${id}/share`, { method: 'POST' })

export const revokeShare = (id: string) =>
  apiFetchData<void>(`${BASE_CAL}/${id}/share`, { method: 'DELETE' })

export const getSharedCalendar = (token: string) =>
  apiFetchData<{ calendar: CalendarItem; events: CalendarEvent[] }>(`${BASE_CAL}/share/${token}`)

export const exportICS = async (id: string): Promise<Blob> => {
  const resp = await apiFetchDirect(`${BASE_CAL}/${id}/export.ics`)
  return resp.blob()
}

export const importICS = (calendarId: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  form.append('calendar_id', calendarId)
  return apiFetchData<{ created: number }>(`${BASE_CAL}/import`, { method: 'POST', body: form as unknown as BodyInit })
}

// Events
export const listEvents = (params: Record<string, string> = {}) => {
  const qs = new URLSearchParams(params).toString()
  return apiFetchData<CalendarEvent[]>(qs ? `${BASE_EVT}?${qs}` : BASE_EVT)
}

export const getRangeEvents = (start: string, end: string, calendarIds?: string[]) => {
  const params: Record<string, string> = { start, end }
  if (calendarIds?.length) params.calendar_ids = calendarIds.join(',')
  const qs = new URLSearchParams(params).toString()
  return apiFetchData<RangeEvent[]>(`${BASE_EVT}/range?${qs}`)
}

export const getEvent = (id: string) =>
  apiFetchData<CalendarEvent>(`${BASE_EVT}/${id}`)

export const createEvent = (payload: EventCreate) =>
  apiFetchData<CalendarEvent>(BASE_EVT, { method: 'POST', body: JSON.stringify(payload) })

export const updateEvent = (id: string, payload: EventUpdate) =>
  apiFetchData<CalendarEvent>(`${BASE_EVT}/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })

export const deleteEvent = (id: string) =>
  apiFetchData<void>(`${BASE_EVT}/${id}`, { method: 'DELETE' })

export const rsvpEvent = (id: string, status: 'accepted' | 'declined' | 'tentative') =>
  apiFetchData<CalendarEvent>(`${BASE_EVT}/${id}/rsvp`, { method: 'POST', body: JSON.stringify({ status }) })

export const updateOccurrence = (masterId: string, date: string, payload: EventUpdate) =>
  apiFetchData<void>(`${BASE_EVT}/${masterId}/occurrences/${date}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const skipOccurrence = (masterId: string, date: string) =>
  apiFetchData<void>(`${BASE_EVT}/${masterId}/occurrences/${date}`, { method: 'DELETE' })
