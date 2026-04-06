<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getRoster } from '../../services/roster.service'
import { listShiftTypes } from '../../services/shift-type.service'
import type { RosterEntry } from '../../services/roster.service'
import type { ShiftType } from '../../services/shift-type.service'

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
    [entries.value, shiftTypes.value] = await Promise.all([
      getRoster(fromDate.value, toDate.value),
      listShiftTypes(),
    ])
  } catch (e: any) { errorMsg.value = e.message }
  finally { loading.value = false }
}

watch([fromDate, toDate], loadRoster, { immediate: true })

function formatDay(dateStr: string) {
  const d = new Date(dateStr)
  return { day: d.toLocaleDateString('en', { weekday: 'short' }), date: d.getDate() }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-start justify-between flex-wrap gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-900">Roster</h2>
        <p class="text-sm text-slate-500 mt-0.5">Weekly shift view per employee</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2 bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[16px] px-4 py-2">
          <label class="text-xs text-slate-500 font-medium">From</label>
          <input type="date" v-model="fromDate" class="text-sm text-slate-900 bg-transparent outline-none" />
          <span class="text-slate-300">→</span>
          <label class="text-xs text-slate-500 font-medium">To</label>
          <input type="date" v-model="toDate" class="text-sm text-slate-900 bg-transparent outline-none" />
        </div>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-16 text-slate-400 text-sm">Loading roster…</div>
    <div v-else-if="errorMsg" class="text-rose-500 text-sm px-4">{{ errorMsg }}</div>
    <div v-else-if="employeeIds.length === 0" class="flex items-center justify-center py-16 text-slate-400 text-sm">No assignments in this date range.</div>
    <div v-else class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] overflow-hidden shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-slate-200/60">
              <th class="text-left px-5 py-4 font-semibold text-slate-500 text-xs uppercase tracking-wide w-32">Employee</th>
              <th v-for="d in dateRange" :key="d" class="px-3 py-4 text-center font-medium text-slate-500 text-xs min-w-[80px]">
                <div class="text-slate-400 text-[10px] uppercase">{{ formatDay(d).day }}</div>
                <div class="text-slate-700 font-bold text-sm mt-0.5">{{ formatDay(d).date }}</div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="empId in employeeIds" :key="empId" class="border-b border-slate-100 last:border-0 hover:bg-slate-50/50 transition-colors">
              <td class="px-5 py-3 font-mono text-xs text-slate-400">{{ empId.slice(0, 8) }}…</td>
              <td v-for="d in dateRange" :key="d" class="px-3 py-3 text-center">
                <template v-if="getShiftForDate(empId, d) as shift">
                  <span
                    v-if="shift?.shift_type_id && shiftTypeMap[shift.shift_type_id]"
                    :style="{ backgroundColor: shiftTypeMap[shift.shift_type_id].color_code || '#e2e8f0', color: '#1e293b' }"
                    class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap"
                    :title="`${shiftTypeMap[shift.shift_type_id].start_time} – ${shiftTypeMap[shift.shift_type_id].end_time}`"
                  >
                    {{ shiftTypeMap[shift.shift_type_id].name }}
                  </span>
                  <span v-else-if="shift" class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-500">Assigned</span>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
