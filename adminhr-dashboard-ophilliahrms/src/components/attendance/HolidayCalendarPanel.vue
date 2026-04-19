<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import { CalendarDays, Plus, Trash2, ChevronDown, ChevronUp, Info, MapPin } from 'lucide-vue-next'
import {
  listHolidayCalendars,
  createHolidayCalendar,
  updateHolidayCalendar,
  deleteHolidayCalendar,
  addHoliday,
  removeHoliday,
} from '../../services/holiday-calendar.service'
import type { HolidayCalendar, Holiday } from '../../services/holiday-calendar.service'

const now = new Date()
const selectedYear = ref(now.getFullYear())
const calendars = ref<HolidayCalendar[]>([])
const loading = ref(false)
const expandedCalendars = ref<Set<string>>(new Set())

const calendarDrawerOpen = ref(false)
const calendarForm = ref({ name: '', year: now.getFullYear(), location_id: '' })
const savingCalendar = ref(false)
const calendarError = ref('')

const deleteCalendarTarget = ref<HolidayCalendar | null>(null)
const deletingCalendar = ref(false)

const holidayForms = ref<Record<string, { name: string; date: string; holiday_type: string }>>({})
const savingHoliday = ref<Record<string, boolean>>({})
const deleteHolidayTarget = ref<{ calendarId: string; holiday: Holiday } | null>(null)
const deletingHoliday = ref(false)

const yearOptions = computed(() => {
  const y = now.getFullYear()
  return [y - 1, y, y + 1, y + 2]
})

async function load() {
  loading.value = true
  try { calendars.value = await listHolidayCalendars(selectedYear.value) }
  catch {} finally { loading.value = false }
}

onMounted(load)

function toggleExpand(id: string) {
  if (expandedCalendars.value.has(id)) expandedCalendars.value.delete(id)
  else expandedCalendars.value.add(id)
}

function holidayTypeColor(type: string) {
  if (type === 'public')     return 'bg-rose-100 text-rose-700 border-rose-200'
  if (type === 'optional')   return 'bg-amber-100 text-amber-700 border-amber-200'
  return 'bg-slate-100 text-slate-600 border-slate-200'
}

function holidayTypeLabel(type: string) {
  if (type === 'public')     return 'Public'
  if (type === 'optional')   return 'Optional'
  return 'Restricted'
}

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function createCalendar() {
  savingCalendar.value = true; calendarError.value = ''
  try {
    await createHolidayCalendar({
      name: calendarForm.value.name,
      year: calendarForm.value.year,
      location_id: calendarForm.value.location_id || undefined,
    })
    calendarDrawerOpen.value = false
    calendarForm.value = { name: '', year: now.getFullYear(), location_id: '' }
    load()
  } catch (e: any) { calendarError.value = e.message }
  finally { savingCalendar.value = false }
}

async function toggleActive(cal: HolidayCalendar) {
  try { await updateHolidayCalendar(cal.id, { is_active: !cal.is_active }); load() } catch {}
}

async function confirmDeleteCalendar() {
  if (!deleteCalendarTarget.value) return
  deletingCalendar.value = true
  try { await deleteHolidayCalendar(deleteCalendarTarget.value.id); deleteCalendarTarget.value = null; load() }
  catch {} finally { deletingCalendar.value = false }
}

function getHolidayForm(calendarId: string) {
  if (!holidayForms.value[calendarId]) {
    holidayForms.value[calendarId] = { name: '', date: '', holiday_type: 'public' }
  }
  return holidayForms.value[calendarId]
}

async function addHolidayToCalendar(calendarId: string) {
  const form = getHolidayForm(calendarId)
  if (!form.name || !form.date) return
  savingHoliday.value[calendarId] = true
  try {
    await addHoliday(calendarId, { name: form.name, date: form.date, holiday_type: form.holiday_type })
    holidayForms.value[calendarId] = { name: '', date: '', holiday_type: 'public' }
    load()
  } catch {}
  finally { savingHoliday.value[calendarId] = false }
}

async function confirmDeleteHoliday() {
  if (!deleteHolidayTarget.value) return
  deletingHoliday.value = true
  try {
    await removeHoliday(deleteHolidayTarget.value.calendarId, deleteHolidayTarget.value.holiday.id)
    deleteHolidayTarget.value = null; load()
  } catch {} finally { deletingHoliday.value = false }
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">Holiday Calendars</h2>
        <p class="text-sm text-slate-500 mt-0.5">Manage public and optional holidays used for pay calculations</p>
      </div>
      <Button @click="calendarDrawerOpen = true" class="rounded-xl bg-slate-900 text-white hover:bg-slate-800 h-10 text-xs font-bold uppercase tracking-widest flex items-center gap-2">
        <Plus class="w-4 h-4" /> New Calendar
      </Button>
    </div>

    <!-- Info banner -->
    <div class="bg-amber-50/60 border border-amber-100 rounded-2xl p-4 flex items-start gap-3">
      <Info class="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
      <p class="text-xs text-amber-800 leading-relaxed">
        Holidays in active calendars are used by the <strong>overtime engine</strong> to apply the holiday pay
        multiplier. Mark holidays as <strong>Public</strong> for mandatory days off, <strong>Optional</strong>
        for employee-choice holidays, or <strong>Restricted</strong> for limited-choice days.
      </p>
    </div>

    <!-- Year tabs -->
    <div class="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
      <button
        v-for="y in yearOptions" :key="y"
        @click="selectedYear = y; load()"
        :class="['px-5 py-2 rounded-lg text-[11px] font-bold uppercase tracking-widest transition-all', selectedYear === y ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900']"
      >{{ y }}</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-48 text-sm text-slate-400">Loading...</div>

    <!-- Empty state -->
    <div v-else-if="calendars.length === 0" class="bg-white border border-slate-200 rounded-2xl p-12 text-center">
      <CalendarDays class="w-10 h-10 text-slate-300 mx-auto mb-3" />
      <p class="text-sm text-slate-500 font-medium">No holiday calendars for {{ selectedYear }}</p>
      <p class="text-xs text-slate-400 mt-1">Create one to start managing holidays.</p>
    </div>

    <!-- Calendar cards -->
    <div v-else class="space-y-4">
      <div
        v-for="cal in calendars" :key="cal.id"
        class="bg-white border border-slate-200 rounded-2xl overflow-hidden"
      >
        <!-- Calendar header -->
        <div class="px-6 py-4 flex items-center gap-4">
          <div class="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center shrink-0">
            <CalendarDays class="w-5 h-5 text-indigo-500" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <h3 class="text-sm font-semibold text-slate-900">{{ cal.name }}</h3>
              <Badge :class="['text-[10px] font-bold border', cal.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-50 text-slate-400 border-slate-200']">
                {{ cal.is_active ? 'Active' : 'Inactive' }}
              </Badge>
              <Badge v-if="cal.location_id" variant="secondary" class="text-[10px] flex items-center gap-1">
                <MapPin class="w-2.5 h-2.5" /> Location-specific
              </Badge>
            </div>
            <p class="text-xs text-slate-400 mt-0.5">{{ cal.holidays?.length ?? 0 }} holiday{{ (cal.holidays?.length ?? 0) !== 1 ? 's' : '' }} · {{ cal.year }}</p>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button
              @click="toggleActive(cal)"
              :class="['w-10 h-5 rounded-full transition-colors shrink-0', cal.is_active ? 'bg-emerald-500' : 'bg-slate-200']"
              :title="cal.is_active ? 'Deactivate' : 'Activate'"
            >
              <div :class="['w-4 h-4 bg-white rounded-full shadow transition-transform mx-0.5', cal.is_active ? 'translate-x-5' : 'translate-x-0']" />
            </button>
            <Button variant="ghost" size="icon" @click="deleteCalendarTarget = cal" class="h-8 w-8 rounded-xl text-slate-400 hover:text-destructive hover:bg-destructive/10">
              <Trash2 class="w-4 h-4" />
            </Button>
            <button @click="toggleExpand(cal.id)" class="h-8 w-8 rounded-xl flex items-center justify-center text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-colors">
              <ChevronDown v-if="!expandedCalendars.has(cal.id)" class="w-4 h-4" />
              <ChevronUp v-else class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Expanded holidays -->
        <div v-if="expandedCalendars.has(cal.id)" class="border-t border-slate-100">
          <!-- Holiday list -->
          <div v-if="cal.holidays && cal.holidays.length > 0" class="divide-y divide-slate-50">
            <div
              v-for="h in cal.holidays.slice().sort((a, b) => a.date.localeCompare(b.date))"
              :key="h.id"
              class="px-6 py-3 flex items-center justify-between gap-4"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div class="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
                <div class="min-w-0">
                  <p class="text-sm font-medium text-slate-800 truncate">{{ h.name }}</p>
                  <p class="text-xs text-slate-400">{{ fmtDate(h.date) }}</p>
                </div>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <Badge :class="['text-[10px] font-bold border', holidayTypeColor(h.holiday_type)]">
                  {{ holidayTypeLabel(h.holiday_type) }}
                </Badge>
                <Button variant="ghost" size="icon" @click="deleteHolidayTarget = { calendarId: cal.id, holiday: h }" class="h-7 w-7 rounded-lg text-slate-400 hover:text-destructive hover:bg-destructive/10">
                  <Trash2 class="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          </div>
          <div v-else class="px-6 py-4 text-xs text-slate-400 text-center">No holidays added yet.</div>

          <!-- Add holiday form -->
          <div class="px-6 py-4 bg-slate-50/50 border-t border-slate-100">
            <p class="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">Add Holiday</p>
            <div class="flex flex-wrap gap-3 items-end">
              <div class="space-y-1 flex-1 min-w-[160px]">
                <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Name</label>
                <input
                  v-model="getHolidayForm(cal.id).name"
                  placeholder="e.g. Republic Day"
                  class="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>
              <div class="space-y-1">
                <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Date</label>
                <input
                  type="date"
                  v-model="getHolidayForm(cal.id).date"
                  class="px-3 py-2 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>
              <div class="space-y-1">
                <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Type</label>
                <select
                  v-model="getHolidayForm(cal.id).holiday_type"
                  class="px-3 py-2 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
                >
                  <option value="public">Public</option>
                  <option value="optional">Optional</option>
                  <option value="restricted">Restricted</option>
                </select>
              </div>
              <Button
                @click="addHolidayToCalendar(cal.id)"
                :disabled="savingHoliday[cal.id] || !getHolidayForm(cal.id).name || !getHolidayForm(cal.id).date"
                class="rounded-xl h-10 bg-slate-900 text-white hover:bg-slate-800 text-xs font-bold uppercase tracking-widest"
              >
                {{ savingHoliday[cal.id] ? 'Adding...' : 'Add' }}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- New Calendar drawer -->
    <SlideDrawer :open="calendarDrawerOpen" title="New Holiday Calendar" width="w-full max-w-md" @close="calendarDrawerOpen = false">
      <div class="space-y-6 py-4">
        <FormInput label="Calendar Name" v-model="calendarForm.name" placeholder="e.g. India 2026 Public Holidays" required />
        <div class="space-y-1">
          <label class="text-xs font-bold uppercase tracking-widest text-slate-500">Year</label>
          <input
            type="number" min="2020" max="2099"
            v-model.number="calendarForm.year"
            class="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
          />
        </div>
        <div class="space-y-1">
          <label class="text-xs font-bold uppercase tracking-widest text-slate-500">Location (optional)</label>
          <input
            v-model="calendarForm.location_id"
            placeholder="Location ID — leave blank for company-wide"
            class="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
          />
          <p class="text-[10px] text-slate-400">Leave blank to apply this calendar to all locations.</p>
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between gap-4">
          <p v-if="calendarError" class="text-[10px] font-bold text-destructive">{{ calendarError }}</p>
          <div class="flex gap-3 ml-auto">
            <Button variant="outline" @click="calendarDrawerOpen = false" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">Cancel</Button>
            <Button @click="createCalendar" :disabled="savingCalendar || !calendarForm.name" class="rounded-full px-8 h-10 bg-slate-900 text-white font-bold uppercase tracking-widest text-[11px]">
              {{ savingCalendar ? 'Creating...' : 'Create Calendar' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- Delete calendar confirm -->
    <ConfirmDialog
      :open="!!deleteCalendarTarget"
      title="Delete Calendar?"
      :message="`Delete '${deleteCalendarTarget?.name}'? All holidays in this calendar will be removed.`"
      :loading="deletingCalendar"
      @confirm="confirmDeleteCalendar"
      @cancel="deleteCalendarTarget = null"
    />

    <!-- Delete holiday confirm -->
    <ConfirmDialog
      :open="!!deleteHolidayTarget"
      title="Remove Holiday?"
      :message="`Remove '${deleteHolidayTarget?.holiday.name}' from this calendar?`"
      :loading="deletingHoliday"
      @confirm="confirmDeleteHoliday"
      @cancel="deleteHolidayTarget = null"
    />
  </div>
</template>
