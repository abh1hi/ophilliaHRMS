<template>
  <div class="h-full flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-base font-semibold text-slate-800">Google Keep Notes</h3>
      <button
        v-if="store.isConnected"
        @click="refresh"
        :disabled="loading"
        class="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50"
      >
        <RefreshCwIcon :class="['w-4 h-4', loading ? 'animate-spin' : '']" />
        Refresh
      </button>
    </div>

    <!-- Not connected -->
    <div v-if="!store.isConnected" class="flex-1 flex flex-col items-center justify-center text-center gap-3 py-16">
      <div class="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
        <StickyNoteIcon class="w-7 h-7 text-slate-400" />
      </div>
      <div>
        <p class="text-sm font-medium text-slate-700">Google not connected</p>
        <p class="text-xs text-slate-400 mt-1 max-w-xs">Connect your Google account to view Keep notes here.</p>
      </div>
      <button
        @click="store.startOAuth()"
        class="px-4 py-2 bg-slate-900 text-white text-sm rounded-lg hover:bg-slate-700"
      >
        Connect Google
      </button>
    </div>

    <!-- Workspace required notice -->
    <div v-else-if="notWorkspaceAccount" class="flex-1 flex flex-col items-center justify-center text-center gap-3 py-16">
      <div class="w-14 h-14 rounded-2xl bg-yellow-50 flex items-center justify-center">
        <AlertCircleIcon class="w-7 h-7 text-yellow-500" />
      </div>
      <div>
        <p class="text-sm font-medium text-slate-700">Google Workspace Required</p>
        <p class="text-xs text-slate-400 mt-1 max-w-xs leading-relaxed">
          Google Keep API is only available for Google Workspace accounts (G Suite).
          Personal Gmail accounts cannot access Keep notes via API.
        </p>
      </div>
    </div>

    <!-- Notes grid -->
    <div v-else class="flex-1 overflow-y-auto">
      <div v-if="loading" class="grid grid-cols-2 gap-3">
        <div v-for="i in 6" :key="i" class="h-28 bg-slate-100 animate-pulse rounded-xl" />
      </div>
      <div v-else-if="notes.length" class="grid grid-cols-2 gap-3">
        <div
          v-for="note in notes"
          :key="note.id"
          :style="{ backgroundColor: note.color ?? '#fef9c3' }"
          class="rounded-xl p-3 shadow-sm"
        >
          <p v-if="note.title" class="text-sm font-semibold text-slate-800 mb-1 truncate">{{ note.title }}</p>
          <p class="text-xs text-slate-600 line-clamp-4 leading-relaxed">{{ note.body }}</p>
          <p class="text-xs text-slate-400 mt-2">{{ formatTime(note.updated_at) }}</p>
        </div>
      </div>
      <div v-else class="flex flex-col items-center justify-center py-16 text-center">
        <StickyNoteIcon class="w-10 h-10 text-slate-300 mb-3" />
        <p class="text-sm text-slate-400">No Keep notes found.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RefreshCwIcon, StickyNoteIcon, AlertCircleIcon } from 'lucide-vue-next'
import { useGoogleStore } from '@/stores/google.store'
import { apiFetchData } from '@/services/http'

interface KeepNote {
  id: string
  title?: string
  body: string
  color?: string
  updated_at: string
}

const store = useGoogleStore()
const notes = ref<KeepNote[]>([])
const loading = ref(false)
const notWorkspaceAccount = ref(false)

onMounted(async () => {
  await store.fetchStatus()
  if (store.isConnected) await refresh()
})

async function refresh() {
  loading.value = true
  notWorkspaceAccount.value = false
  try {
    const result = await apiFetchData<KeepNote[]>('/calendar/google/notes')
    if (result) notes.value = result
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : ''
    if (msg.includes('workspace') || msg.includes('403')) {
      notWorkspaceAccount.value = true
    }
  } finally {
    loading.value = false
  }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric' })
}
</script>
