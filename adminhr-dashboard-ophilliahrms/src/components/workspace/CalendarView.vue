<template>
  <div class="h-full flex flex-col">
    <!-- Calendar toolbar -->
    <div class="flex items-center justify-between mb-3 px-1 flex-shrink-0">
      <div class="flex items-center gap-2">
        <button
          v-for="v in views"
          :key="v.key"
          @click="currentView = v.key"
          :class="[
            'px-3 py-1.5 text-sm rounded-lg font-medium transition-colors',
            currentView === v.key
              ? 'bg-slate-900 text-white'
              : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50',
          ]"
        >
          {{ v.label }}
        </button>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="emit('add-event')"
          class="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 text-white text-sm rounded-lg hover:bg-slate-700 transition-colors"
        >
          <PlusIcon class="w-4 h-4" />
          New Event
        </button>
      </div>
    </div>

    <!-- Calendar legend (calendars filter) -->
    <div v-if="calendars.length" class="flex flex-wrap gap-2 mb-3 px-1 flex-shrink-0">
      <button
        v-for="cal in calendars"
        :key="cal.id"
        @click="emit('toggle-calendar', cal.id)"
        :class="[
          'flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium border transition-colors',
          selectedCalendarIds.includes(cal.id)
            ? 'text-white border-transparent'
            : 'bg-white text-slate-400 border-slate-200',
        ]"
        :style="selectedCalendarIds.includes(cal.id) ? { backgroundColor: cal.color ?? '#1e293b' } : {}"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-current" />
        {{ cal.name }}
      </button>
    </div>

    <!-- FullCalendar -->
    <div class="flex-1 min-h-0 bg-white rounded-xl border border-slate-200 overflow-hidden">
      <FullCalendar
        ref="fcRef"
        :options="calendarOptions"
        class="h-full"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import listPlugin from '@fullcalendar/list'
import interactionPlugin from '@fullcalendar/interaction'
import { PlusIcon } from 'lucide-vue-next'
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
  { key: 'dayGridMonth', label: 'Month' },
  { key: 'timeGridWeek', label: 'Week' },
  { key: 'timeGridDay', label: 'Day' },
  { key: 'listWeek', label: 'List' },
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
