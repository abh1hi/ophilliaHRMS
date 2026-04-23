<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getRoster } from '../../services/roster.service'
import { listShiftTypes } from '../../services/shift-type.service'
import { listEmployees } from '../../services/employee.service'
import type { RosterEntry } from '../../services/roster.service'
import type { ShiftType } from '../../services/shift-type.service'
import type { Employee } from '../../services/employee.types'
import PageHeader from '../ui/PageHeader.vue'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { 
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
const employees = ref<Employee[]>([])
const errorMsg = ref('')

const shiftTypeMap = computed(() => Object.fromEntries(shiftTypes.value.map(t => [t.id, t])))
const employeeMap = computed(() => Object.fromEntries(employees.value.map(e => [e.id, e])))

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
    const [rosterData, shiftTypesData, employeesData] = await Promise.all([
      getRoster(fromDate.value, toDate.value),
      listShiftTypes(),
      listEmployees({ page: 1, page_size: 500 }),
    ])
    entries.value = rosterData
    shiftTypes.value = shiftTypesData
    employees.value = employeesData.data ?? []
  } catch (e: any) { errorMsg.value = e.message }
  finally { loading.value = false }
}

function employeeDisplay(employeeId: string) {
  const employee = employeeMap.value[employeeId]
  if (!employee) return employeeId.slice(0, 8)
  const fullName = `${employee.first_name ?? ''} ${employee.last_name ?? ''}`.trim()
  return fullName || employee.employee_code || employeeId.slice(0, 8)
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
  <div class="space-y-6">
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
      <PageHeader
        title="Roster"
        subtitle="Visualize weekly schedule assignments across your workforce"
      />

      <div class="flex items-center gap-3">
        <Card class="p-1 flex items-center gap-1 shadow-sm border">
           <Button variant="ghost" size="icon" @click="shiftWeek(-7)" class="h-8 w-8 text-muted-foreground hover:text-foreground">
             <ChevronLeft class="w-4 h-4" />
           </Button>
           
           <div class="flex items-center gap-3 px-2">
             <div class="relative group">
               <input type="date" v-model="fromDate" class="absolute inset-0 opacity-0 cursor-pointer" />
               <div class="flex flex-col text-left">
                  <span class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Start</span>
                  <span class="text-sm font-semibold text-foreground">{{ formatDay(fromDate).full }}</span>
               </div>
             </div>
             <ArrowRight class="w-4 h-4 text-muted-foreground" />
             <div class="relative group">
               <input type="date" v-model="toDate" class="absolute inset-0 opacity-0 cursor-pointer" />
               <div class="flex flex-col text-right">
                  <span class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">End</span>
                  <span class="text-sm font-semibold text-foreground">{{ formatDay(toDate).full }}</span>
               </div>
             </div>
           </div>

           <Button variant="ghost" size="icon" @click="shiftWeek(7)" class="h-8 w-8 text-muted-foreground hover:text-foreground">
             <ChevronRight class="w-4 h-4" />
           </Button>
        </Card>

        <Button variant="outline" class="h-10 text-xs font-semibold shadow-sm">
           <CalendarRange class="w-4 h-4 mr-2" /> View Monthly
        </Button>
      </div>
    </div>

    <!-- Loading State -->
    <Card v-if="loading" class="flex flex-col items-center justify-center py-24 gap-4 shadow-sm border">
      <div class="w-8 h-8 border-4 border-muted border-t-primary rounded-full animate-spin"></div>
      <p class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Loading roster…</p>
    </Card>

    <!-- Error State -->
    <Card v-else-if="errorMsg" class="p-4 border-destructive bg-destructive/10 flex items-center gap-3 shadow-sm">
      <AlertCircle class="w-5 h-5 text-destructive" />
      <p class="text-sm font-semibold text-destructive">{{ errorMsg }}</p>
    </Card>

    <!-- Empty State -->
    <Card v-else-if="employeeIds.length === 0" class="flex flex-col items-center justify-center py-24 border-dashed shadow-sm">
      <div class="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
        <Users class="w-8 h-8 text-muted-foreground/50" />
      </div>
      <p class="text-sm font-semibold text-muted-foreground">No schedule assignments found for this date range.</p>
    </Card>

    <!-- Roster Grid -->
    <Card v-else class="overflow-hidden shadow-sm border">
      <div class="overflow-x-auto scrollbar-hide">
        <Table>
          <TableHeader>
            <TableRow class="bg-muted/50 hover:bg-muted/50">
              <TableHead class="min-w-[200px] border-r">Employee</TableHead>
              <TableHead v-for="d in dateRange" :key="d" class="text-center border-r last:border-r-0 min-w-[120px]">
                <div class="flex flex-col items-center justify-center py-2">
                   <span class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{{ formatDay(d).day }}</span>
                   <span class="text-base font-semibold text-foreground">{{ formatDay(d).date }}</span>
                </div>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="empId in employeeIds" :key="empId" class="hover:bg-muted/50 transition-colors">
              <TableCell class="border-r py-4">
                <div class="flex items-center gap-3">
                   <div class="h-8 w-8 rounded bg-primary flex items-center justify-center text-xs font-bold text-primary-foreground shrink-0 shadow-sm">
                      {{ employeeDisplay(empId).slice(0, 2).toUpperCase() }}
                   </div>
                   <div class="flex flex-col">
                      <span class="text-sm font-semibold text-foreground">{{ employeeDisplay(empId) }}</span>
                      <span class="text-[10px] text-muted-foreground">{{ empId.slice(0, 8) }}…</span>
                   </div>
                </div>
              </TableCell>
              <TableCell v-for="d in dateRange" :key="d" class="text-center border-r last:border-r-0 p-2">
                <template v-for="shift in [getShiftForDate(empId, d)]" :key="d">
                  <div v-if="shift?.shift_type_id && shiftTypeMap[shift.shift_type_id]" class="flex justify-center">
                    <Badge 
                      variant="outline"
                      :style="{ 
                        backgroundColor: shiftTypeMap[shift.shift_type_id].color_code ? `${shiftTypeMap[shift.shift_type_id].color_code}15` : 'var(--muted)',
                        borderColor: shiftTypeMap[shift.shift_type_id].color_code || 'var(--border)',
                        color: shiftTypeMap[shift.shift_type_id].color_code || 'var(--foreground)'
                      }"
                      class="flex items-center gap-1.5 px-3 py-1 font-semibold whitespace-nowrap shadow-sm"
                      :title="`${shiftTypeMap[shift.shift_type_id].start_time} – ${shiftTypeMap[shift.shift_type_id].end_time}`"
                    >
                      <Clock class="w-3 h-3" />
                      {{ shiftTypeMap[shift.shift_type_id].name }}
                    </Badge>
                  </div>
                  <div v-else-if="shift" class="flex justify-center">
                    <Badge variant="outline" class="border-dashed text-muted-foreground bg-transparent">
                      Assigned
                    </Badge>
                  </div>
                </template>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
      
      <!-- Footer Summary -->
      <div class="bg-muted/30 px-6 py-4 border-t flex items-center justify-between">
         <div class="flex items-center gap-2 text-primary">
            <Info class="w-4 h-4" />
            <span class="text-xs font-semibold">Roster Active</span>
         </div>
         <p class="text-xs font-medium text-muted-foreground">Showing {{ employeeIds.length }} active employees across {{ dateRange.length }} days</p>
      </div>
    </Card>
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
