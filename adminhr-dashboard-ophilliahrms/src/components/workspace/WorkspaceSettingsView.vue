<template>
  <div class="max-w-2xl space-y-6">
    <div class="bg-white border border-slate-200 rounded-2xl p-6 space-y-4">
      <h3 class="text-base font-semibold text-slate-800">Workspace Settings</h3>

      <!-- Select workspace -->
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Manage Workspace</label>
        <div class="flex gap-2">
          <select
            v-model="selectedId"
            class="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
          >
            <option value="">Select a workspace…</option>
            <option v-for="ws in store.workspaces" :key="ws.id" :value="ws.id">{{ ws.name }}</option>
          </select>
          <button
            v-if="selectedId"
            @click="editWorkspace"
            class="px-3 py-2 text-sm border border-slate-200 rounded-lg hover:bg-slate-50"
          >
            Edit
          </button>
          <button
            v-if="selectedId"
            @click="confirmDelete"
            class="px-3 py-2 text-sm text-red-500 border border-red-200 rounded-lg hover:bg-red-50"
          >
            Delete
          </button>
        </div>
      </div>

      <p v-if="store.workspaces.length === 0" class="text-sm text-slate-400">No workspaces created yet.</p>
    </div>

    <!-- Google Integration -->
    <div class="bg-white border border-slate-200 rounded-2xl p-6 space-y-4">
      <h3 class="text-base font-semibold text-slate-800">Google Integration</h3>
      <GoogleConnectBanner />

      <!-- Connected calendars -->
      <div v-if="googleStore.isConnected" class="space-y-3">
        <div class="flex items-center justify-between">
          <p class="text-sm font-medium text-slate-700">Connected Google Calendars</p>
          <button
            @click="fetchGoogleCals"
            class="text-xs text-blue-600 hover:underline"
          >
            Manage
          </button>
        </div>
        <div v-if="googleStore.connectedCalendars.length" class="space-y-1.5">
          <div
            v-for="cal in googleStore.connectedCalendars"
            :key="cal.id"
            class="flex items-center gap-2 text-sm text-slate-700 px-3 py-2 bg-slate-50 rounded-lg"
          >
            <div class="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
            {{ cal.summary }}
            <span v-if="cal.primary" class="ml-auto text-xs text-slate-400">Primary</span>
          </div>
        </div>
        <p v-else class="text-xs text-slate-400">No calendars connected.</p>

        <!-- Google calendar selector -->
        <div v-if="showCalSelector" class="space-y-2">
          <div
            v-for="cal in googleStore.availableCalendars"
            :key="cal.id"
            class="flex items-center gap-2"
          >
            <input
              type="checkbox"
              :id="cal.id"
              :value="cal.id"
              v-model="selectedGoogleCals"
              class="rounded border-slate-300"
            />
            <label :for="cal.id" class="text-sm text-slate-700">{{ cal.summary }}</label>
          </div>
          <div class="flex gap-2">
            <button @click="saveGoogleCals" class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Save
            </button>
            <button @click="showCalSelector = false" class="px-3 py-1.5 text-sm text-slate-500">Cancel</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit panel -->
    <WorkspacePanel
      :open="showEdit"
      :workspace="editTarget"
      @close="showEdit = false"
      @saved="store.fetchWorkspaces()"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace.store'
import { useGoogleStore } from '@/stores/google.store'
import WorkspacePanel from './WorkspacePanel.vue'
import GoogleConnectBanner from './GoogleConnectBanner.vue'
import type { Workspace } from '@/services/calendar-workspace.service'

const store = useWorkspaceStore()
const googleStore = useGoogleStore()
const selectedId = ref('')
const showEdit = ref(false)
const editTarget = ref<Workspace | null>(null)
const showCalSelector = ref(false)
const selectedGoogleCals = ref<string[]>([])

onMounted(() => {
  store.fetchWorkspaces()
  googleStore.fetchStatus()
})

function editWorkspace() {
  editTarget.value = store.workspaces.find(w => w.id === selectedId.value) ?? null
  showEdit.value = true
}

async function confirmDelete() {
  if (!selectedId.value) return
  if (!confirm('Delete this workspace? This cannot be undone.')) return
  await store.remove(selectedId.value)
  selectedId.value = ''
}

async function fetchGoogleCals() {
  showCalSelector.value = true
  await googleStore.fetchGoogleCalendars()
  selectedGoogleCals.value = googleStore.connectedCalendars.map(c => c.id)
}

async function saveGoogleCals() {
  await googleStore.connectSelectedCalendars(selectedGoogleCals.value)
  showCalSelector.value = false
}
</script>
