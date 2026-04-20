<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getRoster } from '../../services/roster.service'
import { listShiftTypes } from '../../services/shift-type.service'
import type { RosterEntry } from '../../services/roster.service'
import type { ShiftType } from '../../services/shift-type.service'
import PageHeader from '../ui/PageHeader.vue'
import FormInput from '../ui/FormInput.vue'
import { Button } from '@/components/ui/button'
import { 
  Calendar, 
  Users, 
  ArrowRight, 
  Clock, 
  Info, 
  AlertCircle,
  CalendarRange,
  ChevronLeft,
  ChevronRight
} from 'lucide-vue-next'

function getWeekRange() {
  const now = new Date()
  const day = now.getDay()
  const monday = new Date(now)
  monday.setDate(now.getDate() - (day === 0 ? 6 : day - 1))
  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)
  return {
    from: monday.toISOString().slice(0, 10),
    to: sunday.toISOString().slice(0, 10),
  }
}

const week = getWeekRange()
const fromDate = ref(week.from)
const toDate = ref(week.to)
const loading = ref(false)
const entries = ref<RosterEntry[]>([])
const shiftTypes = ref<ShiftType[]>([])
const errorMsg = ref('')

const shiftTypeMap = computed(() => Object.fromEntries(shiftTypes.value.map(t => [t.id, t])))

const dateRange = computed(() => {
  const dates: string[] = []
  const cursor = new Date(fromDate.value)
  const end = new Date(toDate.value)
  while (cursor <= end) {
    dates.push(cursor.toISOString().slice(0, 10))
    cursor.setDate(cursor.getDate() + 1)
  }
  return dates
})

const employeeIds = computed(() => [...new Set(entries.value.map(e => e.employee_id))])

function getShiftForDate(employeeId: string, dateStr: string): RosterEntry | undefined {
  return entries.value.find(e =>
    e.employee_id === employeeId &&
    e.effective_from <= dateStr &&
    (!e.effective_to || e.effective_to >= dateStr)
  )
}

async function loadRoster() {
  if (!fromDate.value || !toDate.value) return
  loading.value = true; errorMsg.value = ''
  try {
    const [rosterData, shiftTypesData] = await Promise.all([
      getRoster(fromDate.value, toDate.value),
      listShiftTypes(),
    ])
    entries.value = rosterData
    shiftTypes.value = shiftTypesData
  } catch (e: any) { errorMsg.value = e.message }
  finally { loading.value = false }
}

watch([fromDate, toDate], loadRoster, { immediate: true })

function formatDay(dateStr: string) {
  const d = new Date(dateStr)
  return { 
    day: d.toLocaleDateString('en', { weekday: 'short' }), 
    date: d.getDate(),
    full: d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
  }
}

function shiftWeek(days: number) {
  const start = new Date(fromDate.value)
  const end = new Date(toDate.value)
  start.setDate(start.getDate() + days)
  end.setDate(end.getDate() + days)
  fromDate.value = start.toISOString().slice(0, 10)
  toDate.value = end.toISOString().slice(0, 10)
}
</script>

<template>
  <div class="space-y-10">
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
      <PageHeader
        title="Roster"
        subtitle="Visualize weekly shift assignments across your workforce"
      />

      <div class="flex items-center gap-3">
        <div class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl border border-white/20 dark:border-white/10 rounded-[22px] p-2 flex items-center gap-2 shadow-sm">
           <Button variant="ghost" size="icon" @click="shiftWeek(-7)" class="h-9 w-9 rounded-xl text-slate-400 hover:text-slate-900">
             <ChevronLeft class="w-4 h-4" />
           </Button>
           
           <div class="flex items-center gap-4 px-2">
             <div class="relative">
               <input type="date" v-model="fromDate" class="absolute inset-0 opacity-0 cursor-pointer" />
               <div class="flex flex-col">
                  <span class="text-[9px] font-bold uppercase tracking-widest text-slate-400">Start</span>
                  <span class="text-xs font-black text-slate-900 dark:text-slate-100">{{ formatDay(fromDate).full }}</span>
               </div>
             </div>
             <ArrowRight class="w-3.5 h-3.5 text-slate-300" />
             <div class="relative">
               <input type="date" v-model="toDate" class="absolute inset-0 opacity-0 cursor-pointer" />
               <div class="flex flex-col text-right">
                  <span class="text-[9px] font-bold uppercase tracking-widest text-slate-400">End</span>
                  <span class="text-xs font-black text-slate-900 dark:text-slate-100">{{ formatDay(toDate).full }}</span>
               </div>
             </div>
           </div>

           <Button variant="ghost" size="icon" @click="shiftWeek(7)" class="h-9 w-9 rounded-xl text-slate-400 hover:text-slate-900">
             <ChevronRight class="w-4 h-4" />
           </Button>
        </div>

        <Button variant="outline" class="h-12 rounded-[22px] px-6 border-slate-200 text-[11px] font-bold uppercase tracking-widest">
           <CalendarRange class="w-4 h-4 mr-2" /> View Monthly
        </Button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-32 gap-4">
      <div class="w-10 h-10 border-4 border-slate-200 border-t-slate-900 rounded-full animate-spin"></div>
      <p class="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">Loading roster…</p>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMsg" class="p-6 rounded-[28px] bg-destructive/5 border border-destructive/20 flex items-center gap-4 animate-in fade-in slide-in-from-bottom-2">
      <AlertCircle class="w-5 h-5 text-destructive" />
      <p class="text-[11px] font-bold text-destructive uppercase tracking-widest">{{ errorMsg }}</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="employeeIds.length === 0" class="flex flex-col items-center justify-center py-32 bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl border border-dashed border-white/20 rounded-[40px]">
      <div class="h-20 w-20 rounded-full bg-slate-50 flex items-center justify-center mb-6">
        <Users class="w-10 h-10 text-slate-200" />
      </div>
      <p class="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground italic">No shift assignments found for this date range</p>
    </div>

    <!-- Roster Grid -->
    <div v-else class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl border border-white/20 dark:border-white/10 rounded-[40px] overflow-hidden shadow-sm animate-in zoom-in-95 duration-500">
      <div class="overflow-x-auto scrollbar-hide">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-slate-50/50 dark:bg-white/5">
              <th class="text-left px-10 py-8 font-black text-slate-900 dark:text-slate-100 text-[10px] uppercase tracking-[0.2em] border-r border-white/10 w-48">Employee</th>
              <th v-for="d in dateRange" :key="d" class="px-6 py-8 text-center border-r border-white/10 last:border-0">
                <div class="flex flex-col items-center gap-1">
                   <span class="text-slate-400 text-[9px] font-black uppercase tracking-widest">{{ formatDay(d).day }}</span>
                   <span class="text-slate-900 dark:text-white text-lg font-black tracking-tighter">{{ formatDay(d).date }}</span>
                </div>
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/10">
            <tr v-for="empId in employeeIds" :key="empId" class="group hover:bg-white/30 dark:hover:bg-white/5 transition-all">
              <td class="px-10 py-6 border-r border-white/10">
                <div class="flex items-center gap-3">
                   <div class="h-8 w-8 rounded-lg bg-slate-900 flex items-center justify-center text-[10px] font-black text-white shrink-0 shadow-lg">
                      {{ empId.slice(0, 2).toUpperCase() }}
                   </div>
                   <div class="flex flex-col">
                      <span class="text-[10px] font-black text-slate-900 dark:text-slate-100 tracking-tight">{{ empId.slice(0, 8) }}…</span>
                      <span class="text-[9px] font-bold text-muted-foreground uppercase tracking-widest">Active Employee</span>
                   </div>
                </div>
              </td>
              <td v-for="d in dateRange" :key="d" class="px-3 py-6 text-center border-r border-white/10 last:border-0">
                <template v-let="shift = getShiftForDate(empId, d)">
                  <div v-if="shift?.shift_type_id && shiftTypeMap[shift.shift_type_id]" class="flex justify-center animate-in zoom-in-95">
                    <div 
                      :style="{ 
                        backgroundColor: shiftTypeMap[shift.shift_type_id].color_code ? `${shiftTypeMap[shift.shift_type_id].color_code}15` : '#f1f5f9',
                        borderColor: shiftTypeMap[shift.shift_type_id].color_code || '#e2e8f0',
                        color: shiftTypeMap[shift.shift_type_id].color_code || '#64748b'
                      }"
                      class="inline-flex items-center gap-1.5 px-4 py-2 rounded-2xl border text-[10px] font-black uppercase tracking-widest whitespace-nowrap shadow-sm group-hover:scale-110 transition-transform cursor-help"
                      :title="`${shiftTypeMap[shift.shift_type_id].start_time} – ${shiftTypeMap[shift.shift_type_id].end_time}`"
                    >
                      <Clock class="w-3 h-3" />
                      {{ shiftTypeMap[shift.shift_type_id].name }}
                    </div>
                  </div>
                  <div v-else-if="shift" class="flex justify-center">
                    <span class="inline-flex items-center px-4 py-2 rounded-2xl border border-dashed border-slate-200 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Assigned</span>
                  </div>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Footer Summary -->
      <div class="bg-indigo-50/30 dark:bg-white/5 px-10 py-6 border-t border-white/10 flex items-center justify-between">
         <div class="flex items-center gap-2">
            <Info class="w-4 h-4 text-indigo-500" />
            <span class="text-[10px] font-bold text-indigo-600 uppercase tracking-widest">Roster Active</span>
         </div>
         <p class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Showing {{ employeeIds.length }} active employees across {{ dateRange.length }} days</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
