import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  listCalendars,
  createCalendar,
  updateCalendar,
  deleteCalendar,
  getRangeEvents,
  createEvent,
  updateEvent,
  deleteEvent,
  type CalendarItem,
  type CalendarCreate,
  type CalendarUpdate,
  type RangeEvent,
  type EventCreate,
  type EventUpdate,
} from '@/services/calendar-events.service'

export const useCalendarStore = defineStore('calendar', () => {
  const calendars = ref<CalendarItem[]>([])
  const selectedCalendarIds = ref<string[]>([])
  const rangeEvents = ref<RangeEvent[]>([])
  const currentRange = ref<{ start: string; end: string } | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchCalendars(workspaceId?: string) {
    loading.value = true
    error.value = null
    try {
      calendars.value = (await listCalendars(workspaceId)) ?? []
      if (calendars.value.length && selectedCalendarIds.value.length === 0) {
        selectedCalendarIds.value = calendars.value.map(c => c.id)
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load calendars'
    } finally {
      loading.value = false
    }
  }

  async function fetchRange(start: string, end: string) {
    loading.value = true
    error.value = null
    try {
      currentRange.value = { start, end }
      rangeEvents.value = (await getRangeEvents(start, end, selectedCalendarIds.value)) ?? []
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load events'
    } finally {
      loading.value = false
    }
  }

  function toggleCalendar(id: string) {
    const idx = selectedCalendarIds.value.indexOf(id)
    if (idx === -1) {
      selectedCalendarIds.value.push(id)
    } else {
      selectedCalendarIds.value.splice(idx, 1)
    }
    if (currentRange.value) {
      fetchRange(currentRange.value.start, currentRange.value.end)
    }
  }

  async function addCalendar(payload: CalendarCreate) {
    const cal = await createCalendar(payload)
    if (cal) {
      calendars.value.push(cal)
      selectedCalendarIds.value.push(cal.id)
    }
    return cal
  }

  async function editCalendar(id: string, payload: CalendarUpdate) {
    const cal = await updateCalendar(id, payload)
    if (cal) {
      const idx = calendars.value.findIndex(c => c.id === id)
      if (idx !== -1) calendars.value[idx] = cal
    }
    return cal
  }

  async function removeCalendar(id: string) {
    await deleteCalendar(id)
    calendars.value = calendars.value.filter(c => c.id !== id)
    selectedCalendarIds.value = selectedCalendarIds.value.filter(i => i !== id)
  }

  async function addEvent(payload: EventCreate) {
    const ev = await createEvent(payload)
    if (ev && currentRange.value) {
      await fetchRange(currentRange.value.start, currentRange.value.end)
    }
    return ev
  }

  async function editEvent(id: string, payload: EventUpdate) {
    const ev = await updateEvent(id, payload)
    if (currentRange.value) await fetchRange(currentRange.value.start, currentRange.value.end)
    return ev
  }

  async function removeEvent(id: string) {
    await deleteEvent(id)
    rangeEvents.value = rangeEvents.value.filter(e => e.id !== id && !e.id.startsWith(id + '_'))
  }

  return {
    calendars,
    selectedCalendarIds,
    rangeEvents,
    currentRange,
    loading,
    error,
    fetchCalendars,
    fetchRange,
    toggleCalendar,
    addCalendar,
    editCalendar,
    removeCalendar,
    addEvent,
    editEvent,
    removeEvent,
  }
})
