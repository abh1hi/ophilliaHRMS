<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  Plus, 
  Upload, 
  Activity, 
  Layers, 
  FileUp, 
  Info,
  Calendar as CalendarIcon,
  Globe
} from 'lucide-vue-next'
import { useWorkspaceStore } from '@/stores/workspace.store'
import { useCalendarStore } from '@/stores/calendar.store'
import { Button } from '@/components/ui/button'
import FormSelect from '../ui/FormSelect.vue'
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

const workspaceOptions = computed(() => [
  { value: '', label: 'Global Topology (All Hubs)' },
  ...workspaceStore.workspaces.map(ws => ({ value: ws.id, label: ws.name }))
])
</script>

<template>
  <div class="h-[calc(100vh-10rem)] flex flex-col gap-6 animate-in fade-in duration-700">
    <!-- Temporal Orchestration Toolbar -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-6 px-1">
      <div class="flex flex-col sm:flex-row items-end gap-6 flex-1">
        <div class="w-full sm:w-72">
          <FormSelect 
            label="Hub Environment Selection" 
            v-model="activeWorkspaceId" 
            :options="workspaceOptions" 
            @update:model-value="onWorkspaceChange"
          />
        </div>
        
        <div class="flex items-center gap-3">
          <Button
            variant="outline"
            @click="showCalendarPanel = true"
            class="h-11 rounded-full px-6 border-slate-200 bg-white/50 backdrop-blur-md text-slate-900 hover:bg-white text-[10px] font-black uppercase tracking-widest shadow-sm"
          >
            <Plus class="w-3.5 h-3.5 mr-2" />
            Add Calendar Node
          </Button>
          <Button
            variant="outline"
            @click="showICS = true"
            class="h-11 rounded-full px-6 border-slate-200 bg-white/50 backdrop-blur-md text-slate-900 hover:bg-white text-[10px] font-black uppercase tracking-widest shadow-sm"
          >
            <FileUp class="w-3.5 h-3.5 mr-2" />
            Import Protocol (.ics)
          </Button>
        </div>
      </div>

      <div class="hidden lg:flex items-center gap-3 py-2 px-4 bg-indigo-50/30 border border-indigo-100/50 rounded-2xl">
         <Info class="w-3.5 h-3.5 text-indigo-500" />
         <span class="text-[10px] font-bold text-indigo-700 uppercase tracking-tight">Active Matrix Visualization Mode</span>
      </div>
    </div>

    <!-- Active Temporal Visualization -->
    <div class="flex-1 min-h-0">
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
    </div>

    <!-- Interface Calibration Layers -->
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
