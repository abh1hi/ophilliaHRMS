<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Button } from '@/components/ui/button'
import { 
  X, 
  Calendar, 
  MapPin, 
  RotateCw, 
  Clock, 
  Palette, 
  Info, 
  Hash, 
  Users, 
  Check,
  Zap,
  Activity,
  Layers
} from 'lucide-vue-next'
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

const calendarOptions = computed(() => 
  props.calendars.map(c => ({ value: c.id, label: c.name }))
)

const eventTypeOptions = [
  { value: 'meeting', label: 'Synchronous Meeting' },
  { value: 'deadline', label: 'Critical Deadline' },
  { value: 'reminder', label: 'Task Reminder' },
  { value: 'block', label: 'Availability Block' }
]

const recurrenceOptions = [
  { value: '', label: 'Single Execution' },
  { value: 'RRULE:FREQ=DAILY', label: 'Daily Cadence' },
  { value: 'RRULE:FREQ=WEEKLY', label: 'Weekly Iteration' },
  { value: 'RRULE:FREQ=MONTHLY', label: 'Monthly Cycle' },
  { value: 'RRULE:FREQ=YEARLY', label: 'Annual Phase' },
  { value: 'custom', label: 'Custom R-Rule...' }
]
</script>

<template>
  <SlideDrawer 
    :open="open" 
    :title="isEdit ? 'Event Recalibration' : 'Temporal Event Synchronization'" 
    width="w-full max-w-lg" 
    @close="emit('close')"
  >
    <div class="space-y-8 py-4">
      <div class="bg-indigo-50/30 p-4 rounded-2xl flex items-start gap-3 border border-indigo-100/50 mb-2">
         <Info class="w-4 h-4 text-indigo-500 mt-0.5" />
         <p class="text-[11px] text-indigo-700 font-medium leading-relaxed">
           Events represent scheduled temporal intersections. Configure duration and recurrence to optimize environmental synchronization and resource availability.
         </p>
      </div>

      <FormInput label="Event Identity" v-model="form.title" required placeholder="Describe the intersection objective..." />
      
      <div class="grid grid-cols-2 gap-6">
        <FormSelect label="Target temporal node" v-model="form.calendar_id" :options="calendarOptions" />
        <FormSelect label="Event Taxonomy" v-model="form.event_type" :options="eventTypeOptions" />
      </div>

      <div class="space-y-6">
        <div class="flex items-center justify-between p-4 bg-slate-50/50 rounded-2xl border border-white/10">
           <div class="flex items-center gap-3">
              <Clock class="w-4 h-4 text-slate-400" />
              <span class="text-[11px] font-bold text-slate-900 tracking-tight">Full-cycle temporal span</span>
           </div>
           <div class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors focus:outline-none" :class="form.all_day ? 'bg-indigo-600' : 'bg-slate-200'" @click="form.all_day = !form.all_day">
              <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" :class="form.all_day ? 'translate-x-6' : 'translate-x-1'" />
           </div>
        </div>

        <div class="grid grid-cols-2 gap-6 animate-in fade-in slide-in-from-top-2">
          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1">Initialization</label>
            <div class="relative group">
               <Calendar class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-slate-900 transition-colors pointer-events-none" />
               <input
                 v-model="form.start_time"
                 :type="form.all_day ? 'date' : 'datetime-local'"
                 class="w-full pl-10 pr-4 py-3 bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-2xl outline-none focus:ring-4 focus:ring-slate-900/5 transition-all"
               />
            </div>
          </div>
          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1">Termination</label>
            <div class="relative group">
               <Calendar class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-slate-900 transition-colors pointer-events-none" />
               <input
                 v-model="form.end_time"
                 :type="form.all_day ? 'date' : 'datetime-local'"
                 class="w-full pl-10 pr-4 py-3 bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-2xl outline-none focus:ring-4 focus:ring-slate-900/5 transition-all"
               />
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-6">
         <div class="flex items-center gap-2 mb-2">
            <Activity class="w-4 h-4 text-slate-400" />
            <span class="text-[10px] font-black uppercase tracking-widest text-slate-900">Contextual Metadata</span>
         </div>
         
         <div class="p-6 bg-slate-50/50 rounded-[32px] border border-white/10 space-y-6">
            <div class="space-y-3">
               <div class="flex items-center gap-2">
                  <MapPin class="w-3.5 h-3.5 text-slate-400" />
                  <label class="text-[10px] font-bold text-slate-600 uppercase tracking-tight">Geospatial / Virtual Location</label>
               </div>
               <input
                 v-model="form.location"
                 type="text"
                 placeholder="e.g. Virtual HQ, War Room 4..."
                 class="w-full bg-white border border-slate-200/60 text-slate-900 text-sm rounded-2xl px-4 py-3 outline-none focus:ring-4 focus:ring-slate-900/5 transition-all shadow-sm"
               />
            </div>

            <FormTextarea label="Operational Brief" v-model="form.description" placeholder="Specify depth and constraints..." />

            <div class="space-y-4">
              <FormSelect label="Recurrence Protocol" v-model="rrulePreset" :options="recurrenceOptions" />
              <div v-if="rrulePreset === 'custom'" class="animate-in fade-in zoom-in-95 space-y-2">
                 <div class="flex items-center gap-2">
                    <Hash class="w-3.5 h-3.5 text-slate-400" />
                    <label class="text-[10px] font-bold text-slate-600 uppercase tracking-tight">Raw R-Rule String</label>
                 </div>
                 <input
                   v-model="form.rrule"
                   type="text"
                   placeholder="RRULE:FREQ=WEEKLY;BYDAY=MO..."
                   class="w-full bg-slate-900 text-emerald-400 font-mono text-xs rounded-xl px-4 py-3 outline-none shadow-xl"
                 />
              </div>
            </div>
         </div>
      </div>

      <div class="space-y-4">
        <div class="flex items-center gap-2 mb-2">
           <Palette class="w-4 h-4 text-slate-400" />
           <span class="text-[10px] font-black uppercase tracking-widest text-slate-900">Aesthetic Focus</span>
        </div>
        <div class="p-6 bg-slate-50/50 rounded-[32px] border border-white/10 flex flex-wrap gap-3">
          <button
            v-for="c in colors"
            :key="c"
            type="button"
            @click="form.color = c"
            :style="{ backgroundColor: c }"
            class="w-8 h-8 rounded-full border-2 transition-all duration-300 relative group"
            :class="[
              form.color === c ? 'border-slate-900 scale-125' : 'border-white/40 hover:scale-110 shadow-sm',
            ]"
          >
             <Check v-if="form.color === c" class="absolute inset-0 m-auto w-3 h-3 text-white" />
          </button>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between gap-4">
        <div class="flex-1">
           <p v-if="error" class="text-[10px] font-bold text-destructive uppercase tracking-tight animate-in fade-in">{{ error }}</p>
        </div>
        <div class="flex gap-3">
          <Button variant="outline" @click="emit('close')" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">Cancel</Button>
          <Button 
            @click="submit" 
            :disabled="saving || !form.title.trim() || !form.calendar_id" 
            class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 font-bold uppercase tracking-widest text-[11px]"
          >
            {{ saving ? 'Syncing...' : isEdit ? 'Deploy Update' : 'Initialize Sequence' }}
          </Button>
        </div>
      </div>
    </template>
  </SlideDrawer>
</template>
