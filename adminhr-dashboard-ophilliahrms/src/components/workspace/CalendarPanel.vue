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
  Globe, 
  Palette, 
  Info, 
  Lock, 
  Unlock, 
  Layers, 
  Activity,
  Zap,
  Check
} from 'lucide-vue-next'
import { useCalendarStore } from '@/stores/calendar.store'
import type { CalendarItem } from '@/services/calendar-events.service'

interface Props {
  open: boolean
  calendar?: CalendarItem | null
  workspaceId?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved', calendar: CalendarItem): void
}>()

const store = useCalendarStore()
const saving = ref(false)
const error = ref<string | null>(null)
const isEdit = computed(() => !!props.calendar)
const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#64748b']

const form = ref({
  name: '',
  description: '',
  calendar_type: 'team' as 'personal' | 'team' | 'company',
  color: '#3b82f6',
  is_public: false,
})

watch(() => props.open, (val) => {
  if (val) {
    error.value = null
    if (props.calendar) {
      form.value = {
        name: props.calendar.name,
        description: props.calendar.description ?? '',
        calendar_type: (props.calendar.calendar_type as 'personal' | 'team' | 'company') ?? 'team',
        color: props.calendar.color ?? '#3b82f6',
        is_public: props.calendar.is_public,
      }
    } else {
      form.value = { name: '', description: '', calendar_type: 'team', color: '#3b82f6', is_public: false }
    }
  }
})

async function submit() {
  if (!form.value.name.trim()) return
  saving.value = true
  error.value = null
  try {
    let cal: CalendarItem | undefined | null
    if (props.calendar) {
      cal = await store.editCalendar(props.calendar.id, {
        name: form.value.name,
        description: form.value.description || undefined,
        color: form.value.color,
        is_public: form.value.is_public,
      })
    } else {
      cal = await store.addCalendar({
        workspace_id: props.workspaceId,
        name: form.value.name,
        description: form.value.description || undefined,
        calendar_type: form.value.calendar_type,
        color: form.value.color,
        is_public: form.value.is_public,
      })
    }
    if (cal) emit('saved', cal)
    emit('close')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to save calendar'
  } finally {
    saving.value = false
  }
}

const typeOptions = [
  { value: 'personal', label: 'Individual Focus' },
  { value: 'team', label: 'Collective Sync' },
  { value: 'company', label: 'Global Topology' }
]
</script>

<template>
  <SlideDrawer 
    :open="open" 
    :title="isEdit ? 'Recalibrate Temporal Node' : 'Initialize Temporal Axis'" 
    width="w-full max-w-md" 
    @close="emit('close')"
  >
    <div class="space-y-8 py-4">
      <div class="bg-indigo-50/30 p-4 rounded-2xl flex items-start gap-3 border border-indigo-100/50 mb-2">
         <Info class="w-4 h-4 text-indigo-500 mt-0.5" />
         <p class="text-[11px] text-indigo-700 font-medium leading-relaxed">
           Calendars serve as temporal containers for event orchestration. Selection of type and visibility calibration defines the reach of this temporal instance.
         </p>
      </div>

      <FormInput label="Node Identity" v-model="form.name" required maxlength="200" placeholder="e.g. Sprint Cadence Beta" />
      <FormTextarea label="Operational Brief" v-model="form.description" placeholder="Specify depth and temporal constraints..." />
      <FormSelect label="Topology Type" v-model="form.calendar_type" :options="typeOptions" />

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

      <div class="space-y-4">
        <div class="flex items-center gap-2 mb-2">
           <Unlock class="w-4 h-4 text-slate-400" />
           <span class="text-[10px] font-black uppercase tracking-widest text-slate-900">Visibility Calibration</span>
        </div>
        <div class="p-6 bg-slate-50/50 rounded-[32px] border border-white/10 flex items-center gap-4 group cursor-pointer" @click="form.is_public = !form.is_public">
           <div class="h-10 w-10 rounded-2xl bg-white border border-slate-200 flex items-center justify-center transition-all group-hover:scale-110 shadow-sm">
              <component :is="form.is_public ? Globe : Lock" class="w-5 h-5" :class="form.is_public ? 'text-blue-500' : 'text-slate-400'" />
           </div>
           <div class="flex-1">
              <p class="text-[11px] font-bold text-slate-900 tracking-tight">Public Temporal Broadcast</p>
              <p class="text-[10px] text-slate-400 font-medium">Expose this calendar to external data consumption</p>
           </div>
           <div class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors focus:outline-none" :class="form.is_public ? 'bg-blue-600' : 'bg-slate-200'">
              <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" :class="form.is_public ? 'translate-x-6' : 'translate-x-1'" />
           </div>
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
            :disabled="saving || !form.name.trim()" 
            class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 font-bold uppercase tracking-widest text-[11px]"
          >
            {{ saving ? 'Syncing...' : isEdit ? 'Deploy Update' : 'Initialize Node' }}
          </Button>
        </div>
      </div>
    </template>
  </SlideDrawer>
</template>

