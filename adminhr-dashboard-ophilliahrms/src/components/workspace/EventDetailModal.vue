<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="open && event" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/40" @click="emit('close')" />
        <div class="relative w-full max-w-md bg-white rounded-2xl shadow-xl flex flex-col max-h-[90vh] overflow-hidden">
          <!-- Color bar -->
          <div class="h-2 flex-shrink-0" :style="{ backgroundColor: event.color ?? eventTypeColor(event.event_type) }" />

          <!-- Header -->
          <div class="flex items-start justify-between px-6 py-4">
            <div class="flex-1 min-w-0">
              <span
                :class="[
                  'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium mb-2 capitalize',
                  typeBadgeClass(event.event_type),
                ]"
              >
                {{ event.event_type }}
              </span>
              <h2 class="text-lg font-semibold text-slate-800 truncate">{{ event.title }}</h2>
            </div>
            <button @click="emit('close')" class="ml-3 p-1.5 rounded-lg hover:bg-slate-100 flex-shrink-0">
              <XIcon class="w-5 h-5 text-slate-500" />
            </button>
          </div>

          <!-- Details -->
          <div class="flex-1 overflow-y-auto px-6 pb-4 space-y-3">
            <!-- Time -->
            <div class="flex items-center gap-2.5 text-sm text-slate-600">
              <ClockIcon class="w-4 h-4 flex-shrink-0 text-slate-400" />
              <span>{{ formatTime(event.start_time) }} – {{ formatTime(event.end_time) }}</span>
              <span v-if="event.all_day" class="text-xs bg-slate-100 px-1.5 py-0.5 rounded">All day</span>
            </div>

            <!-- Location -->
            <div v-if="event.location" class="flex items-center gap-2.5 text-sm text-slate-600">
              <MapPinIcon class="w-4 h-4 flex-shrink-0 text-slate-400" />
              <span>{{ event.location }}</span>
            </div>

            <!-- Recurrence -->
            <div v-if="event.rrule" class="flex items-center gap-2.5 text-sm text-slate-600">
              <RefreshCwIcon class="w-4 h-4 flex-shrink-0 text-slate-400" />
              <span class="font-mono text-xs">{{ event.rrule }}</span>
            </div>

            <!-- Description -->
            <div v-if="event.description" class="text-sm text-slate-600 bg-slate-50 rounded-lg p-3 leading-relaxed">
              {{ event.description }}
            </div>

            <!-- Attendees -->
            <div v-if="event.attendees?.length">
              <p class="text-xs font-medium text-slate-500 mb-2">Attendees ({{ event.attendees.length }})</p>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="a in event.attendees"
                  :key="a.employee_id"
                  :class="['px-2 py-0.5 rounded-full text-xs', rsvpClass(a.rsvp_status)]"
                >
                  {{ a.employee_id }} · {{ a.rsvp_status }}
                </span>
              </div>
            </div>

            <!-- RSVP -->
            <div class="border-t border-slate-100 pt-3">
              <p class="text-xs font-medium text-slate-500 mb-2">Your RSVP</p>
              <div class="flex gap-2">
                <button
                  v-for="s in rsvpOptions"
                  :key="s.value"
                  @click="rsvp(s.value)"
                  :class="[
                    'px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                    s.class,
                  ]"
                >
                  {{ s.label }}
                </button>
              </div>
            </div>
          </div>

          <!-- Footer actions -->
          <div class="px-6 py-3 border-t border-slate-200 flex justify-end gap-2">
            <button
              @click="emit('edit', event)"
              class="px-3 py-1.5 text-sm text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50"
            >
              Edit
            </button>
            <button
              @click="confirmDelete"
              class="px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { XIcon, ClockIcon, MapPinIcon, RefreshCwIcon } from 'lucide-vue-next'
import { useCalendarStore } from '@/stores/calendar.store'
import { rsvpEvent } from '@/services/calendar-events.service'
import type { RangeEvent } from '@/services/calendar-events.service'

interface Props {
  open: boolean
  event: RangeEvent | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit', event: RangeEvent): void
}>()

const store = useCalendarStore()

const rsvpOptions = [
  { value: 'accepted' as const, label: 'Accept', class: 'text-green-700 border-green-200 hover:bg-green-50' },
  { value: 'tentative' as const, label: 'Maybe', class: 'text-yellow-700 border-yellow-200 hover:bg-yellow-50' },
  { value: 'declined' as const, label: 'Decline', class: 'text-red-700 border-red-200 hover:bg-red-50' },
]

function eventTypeColor(type: string) {
  const map: Record<string, string> = {
    meeting: '#3b82f6', deadline: '#ef4444', reminder: '#f59e0b',
    block: '#64748b', holiday: '#f43f5e', leave: '#f97316',
  }
  return map[type] ?? '#3b82f6'
}

function typeBadgeClass(type: string) {
  const map: Record<string, string> = {
    meeting: 'bg-blue-100 text-blue-700',
    deadline: 'bg-red-100 text-red-700',
    reminder: 'bg-yellow-100 text-yellow-700',
    block: 'bg-slate-100 text-slate-600',
    holiday: 'bg-rose-100 text-rose-700',
    leave: 'bg-orange-100 text-orange-700',
  }
  return map[type] ?? 'bg-slate-100 text-slate-600'
}

function rsvpClass(status: string) {
  const map: Record<string, string> = {
    accepted: 'bg-green-100 text-green-700',
    declined: 'bg-red-100 text-red-700',
    tentative: 'bg-yellow-100 text-yellow-700',
    pending: 'bg-slate-100 text-slate-600',
  }
  return map[status] ?? 'bg-slate-100 text-slate-600'
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

async function rsvp(status: 'accepted' | 'declined' | 'tentative') {
  if (!props.event) return
  const id = props.event.recurrence_master_id ?? props.event.id
  await rsvpEvent(id, status)
}

async function confirmDelete() {
  if (!props.event) return
  if (!confirm('Delete this event?')) return
  const id = props.event.recurrence_master_id ?? props.event.id
  await store.removeEvent(id)
  emit('close')
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
