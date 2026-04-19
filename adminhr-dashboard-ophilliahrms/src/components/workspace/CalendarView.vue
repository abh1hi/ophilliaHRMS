<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import listPlugin from '@fullcalendar/list'
import interactionPlugin from '@fullcalendar/interaction'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Plus, 
  Calendar as CalendarIcon, 
  List, 
  LayoutGrid, 
  Clock, 
  ChevronLeft, 
  ChevronRight,
  Filter,
  Monitor,
  Activity,
  Maximize2
} from 'lucide-vue-next'
import type { CalendarItem, RangeEvent } from '@/services/calendar-events.service'
import type { CalendarOptions } from '@fullcalendar/core'

const EVENT_TYPE_COLORS: Record<string, string> = {
  meeting: '#3b82f6',
  deadline: '#ef4444',
  reminder: '#f59e0b',
  block: '#64748b',
  holiday: '#f43f5e',
  leave: '#f97316',
}

interface Props {
  calendars: CalendarItem[]
  selectedCalendarIds: string[]
  events: RangeEvent[]
  loading?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'date-range-change', start: string, end: string): void
  (e: 'event-click', event: RangeEvent): void
  (e: 'date-select', start: string, end: string): void
  (e: 'event-drop', eventId: string, newStart: string, newEnd: string): void
  (e: 'toggle-calendar', calendarId: string): void
  (e: 'add-event'): void
}>()

const views = [
  { key: 'dayGridMonth', label: 'Month', icon: LayoutGrid },
  { key: 'timeGridWeek', label: 'Week', icon: Activity },
  { key: 'timeGridDay', label: 'Day', icon: Clock },
  { key: 'listWeek', label: 'List', icon: List },
]

const currentView = ref('dayGridMonth')
const fcRef = ref()

const fcEvents = computed(() =>
  props.events.map(ev => ({
    id: ev.id,
    title: ev.title,
    start: ev.start_time,
    end: ev.end_time,
    allDay: ev.all_day,
    backgroundColor: ev.color ?? EVENT_TYPE_COLORS[ev.event_type] ?? '#3b82f6',
    borderColor: 'transparent',
    extendedProps: ev,
  }))
)

const calendarOptions = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, timeGridPlugin, listPlugin, interactionPlugin],
  initialView: currentView.value,
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: '',
  },
  height: '100%',
  editable: true,
  selectable: true,
  selectMirror: true,
  dayMaxEvents: true,
  events: fcEvents.value,
  datesSet(info) {
    emit('date-range-change', info.startStr, info.endStr)
  },
  eventClick(info) {
    emit('event-click', info.event.extendedProps as RangeEvent)
  },
  select(info) {
    emit('date-select', info.startStr, info.endStr)
  },
  eventDrop(info) {
    emit('event-drop', info.event.id, info.event.startStr, info.event.endStr ?? info.event.startStr)
  },
}))

watch(currentView, () => {
  fcRef.value?.getApi()?.changeView(currentView.value)
})
</script>

<template>
  <div class="h-full flex flex-col space-y-6 animate-in fade-in duration-700">
    <!-- Temporal Visualization Toolbar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 px-1">
      <div class="flex items-center p-1.5 bg-slate-900/5 backdrop-blur-md border border-slate-900/5 rounded-2xl w-fit">
        <Button
          v-for="v in views"
          :key="v.key"
          variant="ghost"
          size="sm"
          @click="currentView = v.key"
          :class="[
            'h-9 rounded-xl px-4 transition-all duration-300 font-bold uppercase tracking-widest text-[10px]',
            currentView === v.key
              ? 'bg-white text-slate-900 shadow-lg shadow-slate-200/50'
              : 'text-slate-500 hover:text-slate-900 hover:bg-white/50',
          ]"
        >
          <component :is="v.icon" class="w-3.5 h-3.5 mr-2" />
          {{ v.label }}
        </Button>
      </div>

      <div class="flex items-center gap-3">
        <Button
          @click="emit('add-event')"
          class="h-11 rounded-full px-6 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 font-bold uppercase tracking-widest text-[11px]"
        >
          <Plus class="w-4 h-4 mr-2" />
          Initialize Entry
        </Button>
      </div>
    </div>

    <!-- Node Filtering Section -->
    <div v-if="calendars.length" class="flex items-center gap-4 px-1 pb-2 overflow-x-auto no-scrollbar">
      <div class="flex items-center gap-2 shrink-0">
         <Filter class="w-3.5 h-3.5 text-slate-400" />
         <span class="text-[10px] font-black uppercase tracking-tight text-slate-400">Hub Filters:</span>
      </div>
      <div class="flex items-center gap-2">
        <Badge
          v-for="cal in calendars"
          :key="cal.id"
          variant="secondary"
          @click="emit('toggle-calendar', cal.id)"
          class="cursor-pointer h-7 rounded-full px-3 py-0 transition-all duration-300 border-none group select-none"
          :style="selectedCalendarIds.includes(cal.id) 
            ? { backgroundColor: cal.color ?? '#1e293b', color: '#fff', boxShadow: `0 4px 12px ${cal.color ?? '#1e293b'}40` } 
            : { backgroundColor: '#f1f5f9', color: '#94a3b8' }"
        >
          <span class="w-1.5 h-1.5 rounded-full mr-2 transition-transform group-hover:scale-125" :style="{ backgroundColor: selectedCalendarIds.includes(cal.id) ? '#fff' : cal.color ?? '#334155' }" />
          <span class="text-[10px] font-bold uppercase tracking-tight">{{ cal.name }}</span>
        </Badge>
      </div>
    </div>

    <!-- Calendar Environment Container -->
    <div class="flex-1 min-h-0 bg-white/40 backdrop-blur-xl rounded-[32px] border border-white/20 shadow-2xl shadow-slate-200/40 overflow-hidden relative">
      <div class="absolute inset-0 bg-gradient-to-tr from-indigo-50/20 via-transparent to-rose-50/20 pointer-events-none" />
      <div class="h-full relative z-10 p-6">
        <FullCalendar
          ref="fcRef"
          :options="calendarOptions"
          class="h-full fc-glass-morphic"
        />
      </div>
    </div>
  </div>
</template>

<style>
/* FullCalendar Premium Overrides */
.fc-glass-morphic {
  --fc-border-color: rgba(226, 232, 240, 0.5);
  --fc-button-bg-color: transparent;
  --fc-button-border-color: rgba(226, 232, 240, 0.8);
  --fc-button-text-color: #475569;
  --fc-button-hover-bg-color: #f8fafc;
  --fc-button-active-bg-color: #f1f5f9;
  --fc-today-bg-color: rgba(241, 245, 249, 0.5);
  font-family: inherit;
}

.fc .fc-toolbar-title {
  font-size: 1.25rem !important;
  font-weight: 800 !important;
  color: #0f172a;
  text-transform: uppercase;
  letter-spacing: -0.025em;
}

.fc .fc-button-primary {
  background-color: #fff !important;
  border: 1px solid #e2e8f0 !important;
  color: #475569 !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  font-size: 10px !important;
  letter-spacing: 0.05em !important;
  padding: 0.5rem 1rem !important;
  border-radius: 12px !important;
  transition: all 0.2s !important;
}

.fc .fc-button-primary:hover {
  background-color: #f8fafc !important;
  border-color: #cbd5e1 !important;
}

.fc .fc-button-primary:not(:disabled).fc-button-active,
.fc .fc-button-primary:not(:disabled):active {
  background-color: #0f172a !important;
  border-color: #0f172a !important;
  color: #fff !important;
}

.fc .fc-view-harness {
  background: transparent !important;
}

.fc .fc-col-header-cell {
  background: #f8fafc !important;
  padding: 12px 0 !important;
  border-bottom: 2px solid #e2e8f0 !important;
}

.fc .fc-col-header-cell-cushion {
  font-size: 11px !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  color: #64748b !important;
}

.fc-event {
  border-radius: 8px !important;
  padding: 4px 8px !important;
  font-weight: 600 !important;
  font-size: 11px !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
  border: none !important;
  transition: transform 0.2s !important;
}

.fc-event:hover {
  transform: scale(1.02) !important;
  z-index: 50 !important;
}

.fc-theme-standard td, .fc-theme-standard th {
  border-color: rgba(226, 232, 240, 0.4) !important;
}

.fc .fc-scrollgrid {
  border: none !important;
}
</style>
