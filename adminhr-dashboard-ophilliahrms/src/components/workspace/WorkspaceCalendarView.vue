<template>
  <div class="h-[calc(100vh-12rem)] flex flex-col gap-4">
    <!-- Toolbar row: calendar management -->
    <div class="flex items-center gap-3 flex-shrink-0">
      <select
        v-model="activeWorkspaceId"
        @change="onWorkspaceChange"
        class="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
      >
        <option value="">All Calendars</option>
        <option v-for="ws in workspaceStore.workspaces" :key="ws.id" :value="ws.id">
          {{ ws.name }}
        </option>
      </select>
      <button
        @click="showCalendarPanel = true"
        class="flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-sm hover:bg-slate-50"
      >
        <PlusIcon class="w-3.5 h-3.5" />
        Add Calendar
      </button>
      <button
        @click="showICS = true"
        class="flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-sm hover:bg-slate-50"
      >
        <UploadIcon class="w-3.5 h-3.5" />
        Import .ics
      </button>
    </div>

    <!-- Calendar -->
    <CalendarView
      :calendars="calStore.calendars"
      :selected-calendar-ids="calStore.selectedCalendarIds"
      :events="calStore.rangeEvents"
      :loading="calStore.loading"
      @date-range-change="onRangeChange"
      @event-click="onEventClick"
      @date-select="onDateSelect"
      @event-drop="onEventDrop"
      @toggle-calendar="calStore.toggleCalendar"
      @add-event="showEventPanel = true"
    />

    <!-- Panels & modals -->
    <CalendarPanel
      :open="showCalendarPanel"
      :workspace-id="activeWorkspaceId || undefined"
      @close="showCalendarPanel = false"
      @saved="() => {}"
    />

    <EventPanel
      :open="showEventPanel"
      :event="editEvent"
      :default-start="selectStart"
      :default-end="selectEnd"
      :calendars="calStore.calendars"
      @close="showEventPanel = false; editEvent = null"
      @saved="() => {}"
    />

    <EventDetailModal
      :open="showEventDetail"
      :event="clickedEvent"
      @close="showEventDetail = false"
      @edit="onEditEvent"
    />

    <ICSImportPanel
      :open="showICS"
      :calendars="calStore.calendars"
      @close="showICS = false"
      @imported="onICSImported"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { PlusIcon, UploadIcon } from 'lucide-vue-next'
import { useWorkspaceStore } from '@/stores/workspace.store'
import { useCalendarStore } from '@/stores/calendar.store'
import CalendarView from './CalendarView.vue'
import CalendarPanel from './CalendarPanel.vue'
import EventPanel from './EventPanel.vue'
import EventDetailModal from './EventDetailModal.vue'
import ICSImportPanel from './ICSImportPanel.vue'
import type { RangeEvent } from '@/services/calendar-events.service'
import { updateEvent } from '@/services/calendar-events.service'

const workspaceStore = useWorkspaceStore()
const calStore = useCalendarStore()

const activeWorkspaceId = ref('')
const showCalendarPanel = ref(false)
const showEventPanel = ref(false)
const showEventDetail = ref(false)
const showICS = ref(false)
const editEvent = ref<RangeEvent | null>(null)
const clickedEvent = ref<RangeEvent | null>(null)
const selectStart = ref('')
const selectEnd = ref('')

onMounted(async () => {
  await workspaceStore.fetchWorkspaces()
  await calStore.fetchCalendars()
})

async function onWorkspaceChange() {
  await calStore.fetchCalendars(activeWorkspaceId.value || undefined)
}

function onRangeChange(start: string, end: string) {
  calStore.fetchRange(start, end)
}

function onEventClick(event: RangeEvent) {
  clickedEvent.value = event
  showEventDetail.value = true
}

function onDateSelect(start: string, end: string) {
  selectStart.value = start.slice(0, 16)
  selectEnd.value = end.slice(0, 16)
  editEvent.value = null
  showEventPanel.value = true
}

async function onEventDrop(eventId: string, newStart: string, newEnd: string) {
  const id = eventId.includes('_') ? eventId.split('_')[0] : eventId
  await updateEvent(id, { start_time: newStart, end_time: newEnd })
  if (calStore.currentRange) {
    calStore.fetchRange(calStore.currentRange.start, calStore.currentRange.end)
  }
}

function onEditEvent(event: RangeEvent) {
  editEvent.value = event
  showEventDetail.value = false
  showEventPanel.value = true
}

function onICSImported(count: number) {
  if (calStore.currentRange) {
    calStore.fetchRange(calStore.currentRange.start, calStore.currentRange.end)
  }
}
</script>
