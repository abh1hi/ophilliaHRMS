<script setup lang="ts">
import { ref } from 'vue'
import { 
  X, 
  Clock, 
  MapPin, 
  RefreshCw, 
  CheckCircle2, 
  Activity, 
  Trash2, 
  Pencil,
  Globe,
  Users,
  Info,
  Layers,
  ShieldCheck,
  Zap,
  Calendar
} from 'lucide-vue-next'
import { useCalendarStore } from '@/stores/calendar.store'
import { rsvpEvent } from '@/services/calendar-events.service'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
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
const showDeleteConfirm = ref(false)

const rsvpOptions = [
  { value: 'accepted' as const, label: 'Authorize', variant: 'outline' as const, class: 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100' },
  { value: 'tentative' as const, label: 'Conditional', variant: 'outline' as const, class: 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100' },
  { value: 'declined' as const, label: 'Reject', variant: 'outline' as const, class: 'bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100' },
]

function getEventConfig(type: string) {
  const map: Record<string, any> = {
    meeting: { color: 'bg-blue-600', badge: 'bg-blue-100 text-blue-700 border-blue-200', label: 'Matrix Meeting' },
    deadline: { color: 'bg-rose-600', badge: 'bg-rose-100 text-rose-700 border-rose-200', label: 'Terminal Deadline' },
    reminder: { color: 'bg-amber-500', badge: 'bg-amber-100 text-amber-700 border-amber-200', label: 'Sync Reminder' },
    block: { color: 'bg-slate-600', badge: 'bg-slate-100 text-slate-600 border-slate-200', label: 'Temporal Block' },
    holiday: { color: 'bg-rose-500', badge: 'bg-rose-100 text-rose-700 border-rose-200', label: 'System Holiday' },
    leave: { color: 'bg-orange-600', badge: 'bg-orange-100 text-orange-700 border-orange-200', label: 'Off-Grid Leave' },
  }
  return map[type] ?? { color: 'bg-slate-400', badge: 'bg-slate-100 text-slate-600', label: type }
}

function getRsvpBadgeClass(status: string) {
  const map: Record<string, string> = {
    accepted: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    declined: 'bg-rose-100 text-rose-700 border-rose-200',
    tentative: 'bg-amber-100 text-amber-700 border-amber-200',
    pending: 'bg-slate-100 text-slate-400 border-slate-200',
  }
  return map[status] ?? 'bg-slate-100 text-slate-400'
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

async function handleDelete() {
  if (!props.event) return
  showDeleteConfirm.value = false
  const id = props.event.recurrence_master_id ?? props.event.id
  await store.removeEvent(id)
  emit('close')
}
</script>

<template>
  <SlideDrawer
    :open="open"
    title="Temporal Synchronization Detail"
    description="Extended metadata for the orchestrated temporal node."
    side="right"
    width="max-w-md"
    @close="emit('close')"
  >
    <template #actions>
      <Button variant="ghost" size="icon" @click="emit('edit', event!)" class="h-9 w-9 rounded-xl hover:bg-slate-100">
        <Pencil class="w-4 h-4 text-slate-500" />
      </Button>
    </template>

    <div v-if="event" class="space-y-8 py-4 animate-in fade-in slide-in-from-right-4 duration-500">
      <!-- Accent Decoration -->
      <div class="h-1 w-24 rounded-full" :class="getEventConfig(event.event_type).color" />

      <!-- Primary Identification -->
      <div class="space-y-4">
        <Badge variant="outline" :class="['h-6 px-3 rounded-full text-[10px] font-black uppercase tracking-widest border transition-all', getEventConfig(event.event_type).badge]">
          {{ getEventConfig(event.event_type).label }}
        </Badge>
        <h2 class="text-2xl font-black text-slate-900 uppercase tracking-tight leading-tight">{{ event.title }}</h2>
      </div>

      <!-- Temporal & Spatial Calibration -->
      <div class="space-y-4 p-6 bg-slate-50/50 rounded-[32px] border border-slate-100 relative overflow-hidden group">
        <div class="absolute -right-8 -top-8 w-24 h-24 bg-white/40 rounded-full blur-2xl group-hover:bg-white/60 transition-colors" />
        
        <div class="flex items-center gap-4 text-sm relative z-10">
          <div class="w-10 h-10 rounded-2xl bg-white border border-slate-100 shadow-sm flex items-center justify-center">
            <Clock class="w-4 h-4 text-slate-400" />
          </div>
          <div>
            <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">Synchronization Period</p>
            <p class="text-[12px] font-bold text-slate-900 mt-1 uppercase tracking-tight">
              {{ formatTime(event.start_time) }} <span class="mx-1 text-slate-300">→</span> {{ formatTime(event.end_time) }}
            </p>
          </div>
          <Badge v-if="event.all_day" variant="outline" class="ml-auto h-5 bg-white text-[8px] font-black uppercase tracking-widest border-slate-200">Session Full</Badge>
        </div>

        <div v-if="event.location" class="flex items-center gap-4 text-sm relative z-10">
          <div class="w-10 h-10 rounded-2xl bg-white border border-slate-100 shadow-sm flex items-center justify-center">
            <MapPin class="w-4 h-4 text-slate-400" />
          </div>
          <div>
            <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">Environmental Coordinate</p>
            <p class="text-[12px] font-bold text-slate-900 mt-1 uppercase tracking-tight">{{ event.location }}</p>
          </div>
        </div>

        <div v-if="event.rrule" class="flex items-center gap-4 text-sm relative z-10">
          <div class="w-10 h-10 rounded-2xl bg-white border border-slate-100 shadow-sm flex items-center justify-center">
            <RefreshCw class="w-4 h-4 text-slate-400" />
          </div>
          <div>
            <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">Recurrence Protocol</p>
            <p class="text-[10px] font-mono font-bold text-indigo-600 mt-1 break-all">{{ event.rrule }}</p>
          </div>
        </div>
      </div>

      <!-- Payload Specification -->
      <div v-if="event.description" class="space-y-3">
        <p class="text-[11px] font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
          <Layers class="w-4 h-4 text-slate-400" />
          Synchronization Metadata
        </p>
        <div class="bg-indigo-50/30 border border-indigo-100 rounded-[24px] p-5 text-sm text-slate-600 leading-relaxed font-medium">
          {{ event.description }}
        </div>
      </div>

      <!-- Resource Manifest -->
      <div v-if="event.attendees?.length" class="space-y-4">
        <p class="text-[11px] font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
          <Users class="w-4 h-4 text-slate-400" />
          Synchronized Entities ({{ event.attendees.length }})
        </p>
        <div class="flex flex-wrap gap-2">
          <Badge
            v-for="a in event.attendees"
            :key="a.employee_id"
            variant="outline"
            :class="['h-7 rounded-lg px-2.5 text-[10px] font-bold uppercase tracking-tight border shadow-sm transition-all hover:bg-white', getRsvpBadgeClass(a.rsvp_status)]"
          >
            <span class="mr-1.5 opacity-50">{{ a.employee_id }}</span>
            <span class="font-black tracking-widest">{{ a.rsvp_status }}</span>
          </Badge>
        </div>
      </div>

      <!-- Authorization Protocol (RSVP) -->
      <div class="pt-8 border-t border-slate-100 space-y-4">
        <p class="text-[11px] font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
          <ShieldCheck class="w-4 h-4 text-slate-400" />
          Authorization Response
        </p>
        <div class="flex gap-2">
          <Button
            v-for="s in rsvpOptions"
            :key="s.value"
            @click="rsvp(s.value)"
            :variant="s.variant"
            :class="['flex-1 h-11 rounded-[16px] text-[10px] font-black uppercase tracking-widest shadow-sm transition-all hover:scale-[1.02]', s.class]"
          >
            {{ s.label }}
          </Button>
        </div>
      </div>

      <!-- Maintenance Interface -->
      <div class="pt-8 flex justify-between items-center">
        <Button
          variant="ghost"
          @click="showDeleteConfirm = true"
          class="h-10 rounded-full px-5 text-rose-500 hover:text-rose-600 hover:bg-rose-50 text-[10px] font-black uppercase tracking-widest"
        >
          <Trash2 class="w-3.5 h-3.5 mr-2" />
          Purge Protocol
        </Button>
      </div>
    </div>

    <!-- Deletion Invariant Confirmation -->
    <ConfirmDialog
      v-model:open="showDeleteConfirm"
      title="Purge Temporal Node"
      message="This action will permanently terminate the synchronization matrix for this event. Technical metadata will be purged across the environment."
      confirm-text="Confirm Purge"
      @confirm="handleDelete"
    />
  </SlideDrawer>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
