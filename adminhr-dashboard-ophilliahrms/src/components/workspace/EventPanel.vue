<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/40" @click="emit('close')" />
        <div class="relative w-full max-w-lg bg-white h-full shadow-xl flex flex-col">
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
            <h2 class="text-lg font-semibold text-slate-800">{{ isEdit ? 'Edit Event' : 'New Event' }}</h2>
            <button @click="emit('close')" class="p-1.5 rounded-lg hover:bg-slate-100">
              <XIcon class="w-5 h-5 text-slate-500" />
            </button>
          </div>

          <form class="flex-1 overflow-y-auto px-6 py-5 space-y-4">
            <!-- Title -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Title <span class="text-red-500">*</span></label>
              <input
                v-model="form.title"
                type="text"
                required
                placeholder="Event title"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
            </div>

            <!-- Calendar -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Calendar <span class="text-red-500">*</span></label>
              <select
                v-model="form.calendar_id"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
              >
                <option value="">Select calendar</option>
                <option v-for="cal in calendars" :key="cal.id" :value="cal.id">{{ cal.name }}</option>
              </select>
            </div>

            <!-- Type -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Event Type</label>
              <select
                v-model="form.event_type"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
              >
                <option value="meeting">Meeting</option>
                <option value="deadline">Deadline</option>
                <option value="reminder">Reminder</option>
                <option value="block">Block</option>
              </select>
            </div>

            <!-- All day toggle -->
            <div class="flex items-center gap-3">
              <input v-model="form.all_day" type="checkbox" id="all-day" class="rounded border-slate-300" />
              <label for="all-day" class="text-sm text-slate-700">All day</label>
            </div>

            <!-- Start / End -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1.5">Start</label>
                <input
                  v-model="form.start_time"
                  :type="form.all_day ? 'date' : 'datetime-local'"
                  class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1.5">End</label>
                <input
                  v-model="form.end_time"
                  :type="form.all_day ? 'date' : 'datetime-local'"
                  class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
                />
              </div>
            </div>

            <!-- Location -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Location</label>
              <input
                v-model="form.location"
                type="text"
                placeholder="Office, Zoom, etc."
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
              />
            </div>

            <!-- Description -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Description</label>
              <textarea
                v-model="form.description"
                rows="3"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none resize-none"
              />
            </div>

            <!-- Recurrence -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Recurrence</label>
              <select
                v-model="rrulePreset"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
              >
                <option value="">None</option>
                <option value="RRULE:FREQ=DAILY">Daily</option>
                <option value="RRULE:FREQ=WEEKLY">Weekly</option>
                <option value="RRULE:FREQ=MONTHLY">Monthly</option>
                <option value="RRULE:FREQ=YEARLY">Yearly</option>
                <option value="custom">Custom…</option>
              </select>
              <input
                v-if="rrulePreset === 'custom'"
                v-model="form.rrule"
                type="text"
                placeholder="RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR"
                class="mt-2 w-full px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono focus:outline-none"
              />
            </div>

            <!-- Color -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Color</label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="c in colors"
                  :key="c"
                  type="button"
                  @click="form.color = c"
                  :style="{ backgroundColor: c }"
                  :class="[
                    'w-7 h-7 rounded-full border-2 transition-all',
                    form.color === c ? 'border-slate-900 scale-110' : 'border-transparent',
                  ]"
                />
              </div>
            </div>

            <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
          </form>

          <div class="px-6 py-4 border-t border-slate-200 flex justify-end gap-3">
            <button type="button" @click="emit('close')" class="px-4 py-2 text-sm text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50">
              Cancel
            </button>
            <button
              @click="submit"
              :disabled="saving || !form.title.trim() || !form.calendar_id"
              class="px-4 py-2 text-sm font-medium text-white bg-slate-900 rounded-lg hover:bg-slate-700 disabled:opacity-50"
            >
              {{ saving ? 'Saving…' : isEdit ? 'Update' : 'Create' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { XIcon } from 'lucide-vue-next'
import { useCalendarStore } from '@/stores/calendar.store'
import type { CalendarItem, CalendarEvent } from '@/services/calendar-events.service'

interface Props {
  open: boolean
  event?: CalendarEvent | null
  defaultStart?: string
  defaultEnd?: string
  calendars: CalendarItem[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved'): void
}>()

const store = useCalendarStore()
const saving = ref(false)
const error = ref<string | null>(null)
const isEdit = computed(() => !!props.event)
const rrulePreset = ref('')
const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#64748b']

const defaultForm = () => ({
  title: '',
  calendar_id: props.calendars[0]?.id ?? '',
  event_type: 'meeting',
  all_day: false,
  start_time: props.defaultStart ?? '',
  end_time: props.defaultEnd ?? '',
  location: '',
  description: '',
  rrule: '',
  color: '#3b82f6',
})

const form = ref(defaultForm())

watch(() => props.open, (val) => {
  if (val) {
    error.value = null
    rrulePreset.value = ''
    if (props.event) {
      form.value = {
        title: props.event.title,
        calendar_id: props.event.calendar_id,
        event_type: props.event.event_type,
        all_day: props.event.all_day,
        start_time: props.event.start_time.slice(0, 16),
        end_time: props.event.end_time.slice(0, 16),
        location: props.event.location ?? '',
        description: props.event.description ?? '',
        rrule: props.event.rrule ?? '',
        color: props.event.color ?? '#3b82f6',
      }
      if (props.event.rrule) rrulePreset.value = 'custom'
    } else {
      form.value = defaultForm()
    }
  }
})

watch(rrulePreset, (val) => {
  if (val !== 'custom' && val !== '') form.value.rrule = val
  else if (val === '') form.value.rrule = ''
})

async function submit() {
  if (!form.value.title.trim() || !form.value.calendar_id) return
  saving.value = true
  error.value = null
  try {
    const payload = {
      title: form.value.title,
      calendar_id: form.value.calendar_id,
      event_type: form.value.event_type,
      all_day: form.value.all_day,
      start_time: form.value.all_day ? form.value.start_time + 'T00:00:00Z' : form.value.start_time + ':00Z',
      end_time: form.value.all_day ? form.value.end_time + 'T00:00:00Z' : form.value.end_time + ':00Z',
      location: form.value.location || undefined,
      description: form.value.description || undefined,
      rrule: form.value.rrule || undefined,
      color: form.value.color,
    }
    if (props.event) {
      await store.editEvent(props.event.id, payload)
    } else {
      await store.addEvent(payload)
    }
    emit('saved')
    emit('close')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to save event'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.25s; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
</style>
