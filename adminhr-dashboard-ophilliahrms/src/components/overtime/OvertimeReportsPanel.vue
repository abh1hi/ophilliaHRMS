<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Button } from '@/components/ui/button'
import { TrendingUp, Clock, Award } from 'lucide-vue-next'
import { listAttendanceRecords } from '../../services/attendance.service'
import type { AttendanceRecord } from '../../services/attendance.service'

const records = ref<AttendanceRecord[]>([])
const loading = ref(false)

const now = new Date()
const selectedYear  = ref(now.getFullYear())
const selectedMonth = ref(now.getMonth() + 1)

const months = [
  'January','February','March','April','May','June',
  'July','August','September','October','November','December'
]

async function load() {
  loading.value = true
  const firstDay = `${selectedYear.value}-${String(selectedMonth.value).padStart(2, '0')}-01`
  const lastDay  = new Date(selectedYear.value, selectedMonth.value, 0).toISOString().slice(0, 10)
  try {
    const res = await listAttendanceRecords({ date_from: firstDay, date_to: lastDay, limit: 1000 })
    records.value = res.records.filter(r => (r.overtime_hours ?? 0) > 0)
  } catch {} finally { loading.value = false }
}

onMounted(load)

// Aggregate by employee
const byEmployee = computed(() => {
  const map = new Map<string, { employee_id: string; total_ot: number; days: number }>()
  for (const r of records.value) {
    const entry = map.get(r.employee_id) ?? { employee_id: r.employee_id, total_ot: 0, days: 0 }
    entry.total_ot += r.overtime_hours ?? 0
    entry.days += 1
    map.set(r.employee_id, entry)
  }
  return Array.from(map.values()).sort((a, b) => b.total_ot - a.total_ot)
})

const totalOt = computed(() => byEmployee.value.reduce((s, e) => s + e.total_ot, 0).toFixed(1))
const topEmployee = computed(() => byEmployee.value[0])
const maxOt = computed(() => byEmployee.value[0]?.total_ot ?? 1)
</script>

<template>
  <div class="space-y-8">
    <div>
      <h2 class="text-lg font-semibold text-slate-900">Overtime Reports</h2>
      <p class="text-sm text-slate-500 mt-0.5">Monthly overtime analysis by employee</p>
    </div>

    <!-- Month selector -->
    <div class="flex gap-3 items-end">
      <div class="space-y-1">
        <label class="text-xs font-bold uppercase tracking-widest text-slate-500">Month</label>
        <select v-model.number="selectedMonth" class="px-4 py-2.5 rounded-xl border border-slate-200 text-sm bg-white">
          <option v-for="(m, i) in months" :key="i" :value="i + 1">{{ m }}</option>
        </select>
      </div>
      <div class="space-y-1">
        <label class="text-xs font-bold uppercase tracking-widest text-slate-500">Year</label>
        <input type="number" v-model.number="selectedYear" min="2020" max="2099" class="w-24 px-3 py-2.5 rounded-xl border border-slate-200 text-sm bg-white" />
      </div>
      <Button @click="load" :disabled="loading" class="rounded-xl h-10 bg-slate-900 text-white hover:bg-slate-800 text-xs font-bold uppercase tracking-widest">
        {{ loading ? 'Loading...' : 'Load' }}
      </Button>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 gap-4">
      <div class="bg-white border border-slate-200 rounded-2xl p-5 flex items-center justify-between">
        <div>
          <p class="text-xs text-slate-400 font-medium mb-1">Total Overtime Hours</p>
          <p class="text-3xl font-bold text-slate-900">{{ totalOt }}h</p>
          <p class="text-xs text-slate-400 mt-1">{{ months[selectedMonth - 1] }} {{ selectedYear }}</p>
        </div>
        <div class="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center">
          <Clock class="w-6 h-6 text-indigo-500" />
        </div>
      </div>
      <div class="bg-white border border-slate-200 rounded-2xl p-5 flex items-center justify-between">
        <div>
          <p class="text-xs text-slate-400 font-medium mb-1">Top Overtime Employee</p>
          <p class="text-sm font-bold text-slate-900 truncate max-w-[160px]">
            {{ topEmployee ? topEmployee.employee_id.slice(0, 8) + '...' : '—' }}
          </p>
          <p class="text-xs text-amber-600 font-semibold mt-1">{{ topEmployee ? topEmployee.total_ot.toFixed(1) + 'h' : '—' }}</p>
        </div>
        <div class="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center">
          <Award class="w-6 h-6 text-amber-500" />
        </div>
      </div>
    </div>

    <!-- Employee breakdown -->
    <div class="bg-white border border-slate-200 rounded-2xl overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-100">
        <h3 class="text-sm font-semibold text-slate-900">Employee Breakdown</h3>
        <p class="text-xs text-slate-400 mt-0.5">Sorted by total overtime hours</p>
      </div>

      <div v-if="loading" class="p-8 text-center text-sm text-slate-400">Loading...</div>
      <div v-else-if="byEmployee.length === 0" class="p-8 text-center text-sm text-slate-400">
        No overtime recorded for this period.
      </div>
      <div v-else class="divide-y divide-slate-50">
        <div
          v-for="emp in byEmployee"
          :key="emp.employee_id"
          class="px-6 py-4 flex items-center gap-4"
        >
          <div class="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-600 shrink-0">
            {{ emp.employee_id.slice(0, 2).toUpperCase() }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-medium text-slate-700 truncate">{{ emp.employee_id.slice(0, 8) }}...</span>
              <span class="text-xs font-bold text-indigo-700 ml-2 shrink-0">{{ emp.total_ot.toFixed(1) }}h</span>
            </div>
            <!-- Progress bar -->
            <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                class="h-full bg-indigo-500 rounded-full transition-all"
                :style="{ width: `${(emp.total_ot / maxOt) * 100}%` }"
              />
            </div>
            <p class="text-[10px] text-slate-400 mt-1">{{ emp.days }} day{{ emp.days > 1 ? 's' : '' }} with OT</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
