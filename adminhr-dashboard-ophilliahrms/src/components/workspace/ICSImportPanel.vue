<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/40" @click="emit('close')" />
        <div class="relative w-full max-w-lg bg-white rounded-2xl shadow-xl flex flex-col overflow-hidden">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
            <h2 class="text-lg font-semibold text-slate-800">Import .ics File</h2>
            <button @click="emit('close')" class="p-1.5 rounded-lg hover:bg-slate-100">
              <XIcon class="w-5 h-5 text-slate-500" />
            </button>
          </div>

          <!-- Step 1: Pick file + calendar -->
          <div v-if="!preview" class="px-6 py-6 space-y-4">
            <!-- Calendar selector -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Import into Calendar</label>
              <select
                v-model="targetCalendarId"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
              >
                <option value="">Select calendar…</option>
                <option v-for="cal in calendars" :key="cal.id" :value="cal.id">{{ cal.name }}</option>
              </select>
            </div>

            <!-- Drop zone -->
            <div
              @dragover.prevent="dragging = true"
              @dragleave="dragging = false"
              @drop.prevent="onDrop"
              :class="[
                'border-2 border-dashed rounded-xl px-6 py-10 text-center transition-colors cursor-pointer',
                dragging ? 'border-blue-400 bg-blue-50' : 'border-slate-200 hover:border-slate-300',
              ]"
              @click="fileInput?.click()"
            >
              <UploadIcon class="w-8 h-8 text-slate-300 mx-auto mb-3" />
              <p class="text-sm font-medium text-slate-600">Drop your .ics file here</p>
              <p class="text-xs text-slate-400 mt-1">or click to browse</p>
              <p v-if="selectedFile" class="mt-3 text-sm font-medium text-blue-600">{{ selectedFile.name }}</p>
            </div>
            <input ref="fileInput" type="file" accept=".ics" class="hidden" @change="onFileChange" />

            <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
          </div>

          <!-- Step 2: Preview -->
          <div v-else class="px-6 py-4 space-y-3 max-h-96 overflow-y-auto">
            <p class="text-sm font-medium text-slate-700">
              Found <span class="text-blue-600">{{ preview.length }}</span> event(s) to import
            </p>
            <div class="space-y-2">
              <div
                v-for="(ev, i) in preview.slice(0, 20)"
                :key="i"
                class="flex items-start gap-3 px-3 py-2 bg-slate-50 rounded-lg border border-slate-100"
              >
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-slate-800 truncate">{{ ev.title }}</p>
                  <p class="text-xs text-slate-500">{{ formatTime(ev.start_time) }}</p>
                </div>
                <span v-if="ev.rrule" class="text-xs text-blue-500 flex-shrink-0">Recurring</span>
              </div>
              <p v-if="preview.length > 20" class="text-xs text-slate-400 text-center">
                … and {{ preview.length - 20 }} more
              </p>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-slate-200 flex justify-between gap-3">
            <button
              v-if="preview"
              @click="preview = null"
              class="px-4 py-2 text-sm text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50"
            >
              Back
            </button>
            <div class="flex gap-3 ml-auto">
              <button @click="emit('close')" class="px-4 py-2 text-sm text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50">
                Cancel
              </button>
              <button
                v-if="!preview"
                @click="parsefile"
                :disabled="!selectedFile || !targetCalendarId || parsing"
                class="px-4 py-2 text-sm font-medium text-white bg-slate-900 rounded-lg hover:bg-slate-700 disabled:opacity-50"
              >
                {{ parsing ? 'Parsing…' : 'Preview' }}
              </button>
              <button
                v-else
                @click="importEvents"
                :disabled="importing"
                class="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {{ importing ? 'Importing…' : `Import ${preview.length} events` }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { XIcon, UploadIcon } from 'lucide-vue-next'
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
  } else {
    error.value = 'Please drop a valid .ics file.'
  }
}

async function parsefile() {
  if (!selectedFile.value) return
  parsing.value = true
  error.value = null
  try {
    // Read ICS locally for preview using icalendar-like parsing
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
    error.value = e instanceof Error ? e.message : 'Failed to parse ICS file'
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
    error.value = e instanceof Error ? e.message : 'Import failed'
  } finally {
    importing.value = false
  }
}

function formatTime(raw: string) {
  if (!raw) return '—'
  // Parse basic iCal datetime e.g. 20260401T090000Z
  const clean = raw.replace(/[TZ]/g, ' ').trim()
  if (clean.length >= 8) {
    const d = clean.slice(0, 8)
    return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`
  }
  return raw
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
