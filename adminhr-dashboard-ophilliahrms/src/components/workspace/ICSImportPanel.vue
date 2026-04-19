<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  X, 
  Upload, 
  FileUp, 
  Activity, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  Info,
  Layers,
  FileText,
  Zap,
  ArrowLeft
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormSelect from '../ui/FormSelect.vue'
import { importICS } from '@/services/calendar-events.service'
import type { CalendarItem } from '@/services/calendar-events.service'

interface PreviewEvent {
  title: string
  start_time: string
  end_time: string
  rrule?: string
}

interface Props {
  open: boolean
  calendars: CalendarItem[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'imported', count: number): void
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const targetCalendarId = ref('')
const dragging = ref(false)
const parsing = ref(false)
const importing = ref(false)
const error = ref<string | null>(null)
const preview = ref<PreviewEvent[] | null>(null)

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  preview.value = null
}

function onDrop(e: DragEvent) {
  dragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file && file.name.endsWith('.ics')) {
    selectedFile.value = file
    preview.value = null
    error.value = null
  } else {
    error.value = 'Incompatible file format. Please provide a valid .ics manifest.'
  }
}

async function parsefile() {
  if (!selectedFile.value) return
  parsing.value = true
  error.value = null
  try {
    const text = await selectedFile.value.text()
    const events: PreviewEvent[] = []
    const blocks = text.split('BEGIN:VEVENT')
    for (let i = 1; i < blocks.length; i++) {
      const block = blocks[i]
      const get = (key: string) => {
        const m = block.match(new RegExp(`^${key}[^:]*:(.*)`, 'm'))
        return m ? m[1].trim() : ''
      }
      events.push({
        title: get('SUMMARY') || 'Imported Event',
        start_time: get('DTSTART'),
        end_time: get('DTEND'),
        rrule: get('RRULE') || undefined,
      })
    }
    preview.value = events
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to parse technical manifest'
  } finally {
    parsing.value = false
  }
}

async function importEvents() {
  if (!selectedFile.value || !targetCalendarId.value) return
  importing.value = true
  error.value = null
  try {
    const result = await importICS(targetCalendarId.value, selectedFile.value)
    emit('imported', result?.created ?? 0)
    emit('close')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Synchronization protocol failed'
  } finally {
    importing.value = false
  }
}

function formatTime(raw: string) {
  if (!raw) return '—'
  const clean = raw.replace(/[TZ]/g, ' ').trim()
  if (clean.length >= 8) {
    const d = clean.slice(0, 8)
    return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`
  }
  return raw
}

const calendarOptions = computed(() => [
  { value: '', label: 'Select Destination Node' },
  ...props.calendars.map(cal => ({ value: cal.id, label: cal.name }))
])
</script>

<template>
  <SlideDrawer
    :open="open"
    title="Temporal Metadata Ingestion"
    description="Sync external calendar protocols with the local orchestration engine."
    side="right"
    width="max-w-md"
    @close="emit('close')"
  >
    <div class="h-full flex flex-col pt-4">
      <!-- Step 1: Configuration -->
      <div v-if="!preview" class="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
        <FormSelect
          label="Ingestion Target Node"
          v-model="targetCalendarId"
          :options="calendarOptions"
        />

        <div class="space-y-3">
          <p class="text-[11px] font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
            <FileText class="w-4 h-4 text-slate-400" />
            Technical Manifest Ingestion
          </p>
          
          <div
            @dragover.prevent="dragging = true"
            @dragleave="dragging = false"
            @drop.prevent="onDrop"
            :class="[
              'relative overflow-hidden group border border-dashed rounded-[32px] px-8 py-14 text-center transition-all cursor-pointer',
              dragging 
                ? 'border-indigo-400 bg-indigo-50/50 shadow-2xl shadow-indigo-100 scale-[0.98]' 
                : 'border-slate-200 bg-slate-50/30 hover:border-slate-300 hover:bg-white shadow-sm'
            ]"
            @click="fileInput?.click()"
          >
            <div class="absolute -right-8 -bottom-8 w-24 h-24 bg-indigo-100/20 rounded-full blur-2xl group-hover:bg-indigo-100/40 transition-colors" />
            
            <div class="relative z-10 space-y-4">
              <div class="w-16 h-16 rounded-[24px] bg-white border border-slate-100 shadow-sm mx-auto flex items-center justify-center group-hover:scale-110 transition-transform">
                <FileUp class="w-7 h-7 text-slate-400 group-hover:text-indigo-500 transition-colors" />
              </div>
              <div>
                <p class="text-[11px] font-black text-slate-900 uppercase tracking-widest leading-none">Drop Technical Manifest</p>
                <p class="text-[10px] text-slate-400 font-bold mt-2 uppercase tracking-tight">Support for .ics protocol only</p>
              </div>
              
              <div v-if="selectedFile" class="pt-4 animate-in zoom-in-95 duration-300">
                 <Badge variant="outline" class="h-8 px-4 bg-indigo-600 text-white border-transparent gap-2 shadow-lg shadow-indigo-200">
                   <CheckCircle2 class="w-3 h-3" />
                   {{ selectedFile.name }}
                 </Badge>
              </div>
            </div>
          </div>
          <input ref="fileInput" type="file" accept=".ics" class="hidden" @change="onFileChange" />
        </div>

        <div v-if="error" class="p-4 bg-rose-50 border border-rose-100 rounded-[20px] flex items-center gap-3 animate-in shake duration-500">
          <AlertCircle class="w-4 h-4 text-rose-500 flex-shrink-0" />
          <p class="text-[11px] font-bold text-rose-700 uppercase tracking-tight">{{ error }}</p>
        </div>
      </div>

      <!-- Step 2: Manifest Visualizer -->
      <div v-else class="flex-1 min-h-0 flex flex-col space-y-6 animate-in fade-in slide-in-from-left-4 duration-500">
        <div class="flex items-center justify-between px-1">
          <p class="text-[11px] font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
            <Layers class="w-4 h-4 text-slate-400" />
            Discovered Entropy Nodes
          </p>
          <Badge variant="secondary" class="h-5 px-2 bg-indigo-50 text-indigo-700 border-indigo-100 text-[9px] font-black uppercase tracking-widest">
            {{ preview.length }} Nodes Identified
          </Badge>
        </div>

        <div class="flex-1 overflow-y-auto no-scrollbar space-y-3 pb-6">
          <div
            v-for="(ev, i) in preview.slice(0, 50)"
            :key="i"
            class="flex items-center gap-4 p-4 bg-white/40 border border-slate-100 rounded-[24px] shadow-sm hover:shadow-md hover:border-slate-200 transition-all group"
          >
            <div class="w-10 h-10 rounded-xl bg-slate-50 group-hover:bg-indigo-50 border border-slate-100 flex items-center justify-center flex-shrink-0 transition-colors">
              <Activity class="w-4 h-4 text-slate-400 group-hover:text-indigo-500 transition-colors" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-[12px] font-bold text-slate-900 truncate uppercase tracking-tight leading-none mb-1.5">{{ ev.title }}</p>
              <p class="text-[10px] text-slate-400 font-bold uppercase tracking-tight flex items-center gap-1.5">
                <Clock class="w-3 h-3" /> {{ formatTime(ev.start_time) }}
              </p>
            </div>
            <Badge v-if="ev.rrule" variant="outline" class="h-5 rounded-full px-2 border-indigo-100 text-indigo-600 bg-indigo-50 text-[8px] font-black uppercase tracking-widest">Recurring</Badge>
          </div>
          <p v-if="preview.length > 50" class="text-[10px] text-slate-400 text-center font-bold uppercase py-4 border-t border-dashed border-slate-100">
            … Orchestration continues for {{ preview.length - 50 }} additional nodes
          </p>
        </div>
      </div>

      <!-- Control Interface -->
      <div class="mt-auto pt-8 border-t border-slate-100 flex items-center justify-between gap-4">
        <Button
          v-if="preview"
          variant="ghost"
          @click="preview = null"
          class="h-11 rounded-full px-6 text-slate-500 font-bold uppercase tracking-widest text-[10px]"
        >
          <ArrowLeft class="w-3.5 h-3.5 mr-2" />
          Edit Manifest
        </Button>
        <div class="flex items-center gap-3 ml-auto">
          <Button
            variant="ghost"
            @click="emit('close')"
            class="h-11 rounded-full px-6 text-slate-500 font-bold uppercase tracking-widest text-[10px]"
          >
            Abort
          </Button>
          <Button
            v-if="!preview"
            @click="parsefile"
            :disabled="!selectedFile || !targetCalendarId || parsing"
            class="h-11 rounded-full px-8 bg-slate-900 text-white hover:bg-black shadow-xl shadow-slate-200 disabled:opacity-20 font-bold uppercase tracking-widest text-[10px]"
          >
            <Activity v-if="parsing" class="w-3.5 h-3.5 mr-2 animate-spin" />
            {{ parsing ? 'Parsing Manifest...' : 'Analyze Protocol' }}
          </Button>
          <Button
            v-else
            @click="importEvents"
            :disabled="importing"
            class="h-11 rounded-full px-8 bg-emerald-600 text-white hover:bg-emerald-700 shadow-xl shadow-emerald-100 disabled:opacity-20 font-bold uppercase tracking-widest text-[10px]"
          >
            <Zap v-if="importing" class="w-3.5 h-3.5 mr-2 animate-spin" />
            {{ importing ? 'Synchronizing...' : `Commit ${preview.length} Nodes` }}
          </Button>
        </div>
      </div>
    </div>
  </SlideDrawer>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
