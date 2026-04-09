<template>
  <div>
    <!-- Not connected -->
    <div
      v-if="!store.isConnected"
      class="flex items-center justify-between gap-4 px-5 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl"
    >
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
          <CalendarIcon class="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <p class="text-sm font-medium text-slate-800">Connect Google Calendar</p>
          <p class="text-xs text-slate-500">Sync your events, tasks and notes with Google Workspace</p>
        </div>
      </div>
      <button
        @click="store.startOAuth()"
        class="flex-shrink-0 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
      >
        Connect
      </button>
    </div>

    <!-- Connected -->
    <div v-else class="flex items-center justify-between gap-4 px-5 py-4 bg-green-50 border border-green-200 rounded-xl">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
          <CheckCircleIcon class="w-5 h-5 text-green-600" />
        </div>
        <div>
          <p class="text-sm font-medium text-slate-800">Google connected</p>
          <p class="text-xs text-slate-500">
            {{ store.integration?.google_email ?? '' }}
            <span v-if="store.integration?.last_synced_at">
              · Last synced {{ formatTime(store.integration.last_synced_at) }}
            </span>
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2 flex-shrink-0">
        <button
          @click="syncNow"
          :disabled="store.syncing"
          class="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-green-300 text-green-700 text-xs font-medium rounded-lg hover:bg-green-50 disabled:opacity-50 transition-colors"
        >
          <RefreshCwIcon :class="['w-3.5 h-3.5', store.syncing ? 'animate-spin' : '']" />
          {{ store.syncing ? 'Syncing…' : 'Sync Now' }}
        </button>
        <button
          @click="disconnect"
          class="px-3 py-1.5 text-xs text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
        >
          Disconnect
        </button>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="store.integration?.status === 'revoked'" class="mt-2 flex items-center gap-2 text-sm text-red-600 bg-red-50 px-4 py-2 rounded-lg">
      <AlertCircleIcon class="w-4 h-4 flex-shrink-0" />
      Google sync was revoked due to repeated errors. Please reconnect.
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { CalendarIcon, CheckCircleIcon, RefreshCwIcon, AlertCircleIcon } from 'lucide-vue-next'
import { useGoogleStore } from '@/stores/google.store'

const store = useGoogleStore()

onMounted(() => store.fetchStatus())

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function syncNow() {
  await store.syncCalendars()
}

async function disconnect() {
  if (!confirm('Disconnect Google account?')) return
  await store.disconnect()
}
</script>
