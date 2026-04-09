import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getAuthUrl,
  getIntegrationStatus,
  listGoogleCalendars,
  connectCalendars,
  triggerCalendarSync,
  triggerTaskSync,
  disconnectGoogle,
  type GoogleIntegration,
  type GoogleCalendarItem,
} from '@/services/calendar-google.service'

export const useGoogleStore = defineStore('google', () => {
  const integration = ref<GoogleIntegration | null>(null)
  const availableCalendars = ref<GoogleCalendarItem[]>([])
  const syncing = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isConnected = computed(() => integration.value?.status === 'active')
  const connectedCalendars = computed(() => integration.value?.connected_calendars ?? [])

  async function fetchStatus() {
    loading.value = true
    error.value = null
    try {
      integration.value = await getIntegrationStatus() ?? null
    } catch {
      integration.value = null
    } finally {
      loading.value = false
    }
  }

  async function startOAuth() {
    const resp = await getAuthUrl()
    if (resp?.auth_url) {
      window.location.href = resp.auth_url
    }
  }

  async function fetchGoogleCalendars() {
    loading.value = true
    try {
      availableCalendars.value = (await listGoogleCalendars()) ?? []
    } finally {
      loading.value = false
    }
  }

  async function connectSelectedCalendars(calendarIds: string[]) {
    const updated = await connectCalendars(calendarIds)
    if (updated) integration.value = updated
    return updated
  }

  async function syncCalendars() {
    syncing.value = true
    try {
      const result = await triggerCalendarSync()
      await fetchStatus()
      return result
    } finally {
      syncing.value = false
    }
  }

  async function syncTasks() {
    syncing.value = true
    try {
      const result = await triggerTaskSync()
      return result
    } finally {
      syncing.value = false
    }
  }

  async function disconnect() {
    await disconnectGoogle()
    integration.value = null
    availableCalendars.value = []
  }

  return {
    integration,
    availableCalendars,
    syncing,
    loading,
    error,
    isConnected,
    connectedCalendars,
    fetchStatus,
    startOAuth,
    fetchGoogleCalendars,
    connectSelectedCalendars,
    syncCalendars,
    syncTasks,
    disconnect,
  }
})
