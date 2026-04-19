import { apiFetchData } from './http'

export interface Holiday {
  id: string
  calendar_id: string
  name: string
  date: string
  holiday_type: 'public' | 'optional' | 'restricted'
  created_at: string
}

export interface HolidayCalendar {
  id: string
  company_id: string
  location_id?: string
  name: string
  year: number
  is_active: boolean
  holidays: Holiday[]
  created_at: string
  updated_at: string
}

export async function listHolidayCalendars(year?: number): Promise<HolidayCalendar[]> {
  const qs = year ? `?year=${year}` : ''
  return apiFetchData<HolidayCalendar[]>(`/holiday-calendars${qs}`)
}

export async function createHolidayCalendar(payload: {
  name: string
  year: number
  location_id?: string
}): Promise<HolidayCalendar> {
  return apiFetchData<HolidayCalendar>('/holiday-calendars', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateHolidayCalendar(
  id: string,
  payload: { name?: string; is_active?: boolean },
): Promise<HolidayCalendar> {
  return apiFetchData<HolidayCalendar>(`/holiday-calendars/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteHolidayCalendar(id: string): Promise<HolidayCalendar> {
  return apiFetchData<HolidayCalendar>(`/holiday-calendars/${id}`, { method: 'DELETE' })
}

export async function listHolidays(calendarId: string): Promise<Holiday[]> {
  return apiFetchData<Holiday[]>(`/holiday-calendars/${calendarId}/holidays`)
}

export async function addHoliday(
  calendarId: string,
  payload: { name: string; date: string; holiday_type: string },
): Promise<Holiday> {
  return apiFetchData<Holiday>(`/holiday-calendars/${calendarId}/holidays`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function removeHoliday(calendarId: string, holidayId: string): Promise<void> {
  await apiFetchData<void>(`/holiday-calendars/${calendarId}/holidays/${holidayId}`, {
    method: 'DELETE',
  })
}
