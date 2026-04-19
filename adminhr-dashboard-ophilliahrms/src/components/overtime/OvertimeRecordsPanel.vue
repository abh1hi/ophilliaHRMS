<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Button } from '@/components/ui/button'
import DataTable from '../ui/DataTable.vue'
import { Clock, Users, TrendingUp, Download } from 'lucide-vue-next'
import { listAttendanceRecords } from '../../services/attendance.service'
import type { AttendanceRecord } from '../../services/attendance.service'

const records = ref<AttendanceRecord[]>([])
const loading = ref(false)
const employeeFilter = ref('')
const dateFrom = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().slice(0, 10))
const dateTo = ref(new Date().toISOString().slice(0, 10))

const otRecords = computed(() =>
  records.value.filter(r => (r.overtime_hours ?? 0) > 0)
)

const totalOtHours = computed(() =>
  otRecords.value.reduce((s, r) => s + (r.overtime_hours ?? 0), 0).toFixed(1)
)
const employeesWithOt = computed(() =>
  new Set(otRecords.value.map(r => r.employee_id)).size
)
const avgOt = computed(() => {
  const count = employeesWithOt.value
  return count > 0 ? (Number(totalOtHours.value) / count).toFixed(1) : '0'
})

const columns = [
  { key: 'employee_id', label: 'Employee ID' },
  { key: 'date',        label: 'Date'        },
  { key: 'clock_in',    label: 'Clock In'    },
  { key: 'clock_out',   label: 'Clock Out'   },
  { key: 'work_hours',  label: 'Regular Hrs' },
  { key: 'overtime_hours', label: 'OT Hours' },
  { key: 'status',      label: 'Status'      },
]

async function load() {
  loading.value = true
  try {
    const res = await listAttendanceRecords({
      date_from: dateFrom.value,
      date_to: dateTo.value,
      employee_id: employeeFilter.value || undefined,
      limit: 500,
    })
    records.value = res.records
  } catch {} finally { loading.value = false }
}

onMounted(load)

function fmtTime(dt?: string) {
  if (!dt) return '—'
  return new Date(dt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="space-y-8">
    <div>
      <h2 class="text-lg font-semibold text-slate-900">Overtime Records</h2>
      <p class="text-sm text-slate-500 mt-0.5">Auto-calculated overtime hours from employee clock-in/out data</p>
    </div>

    <!-- Stat cards -->
    <div class="grid grid-cols-3 gap-4">
      <div v-for="stat in [
        { label: 'Total OT Hours', value: totalOtHours + 'h', icon: Clock, color: 'indigo' },
        { label: 'Employees with OT', value: String(employeesWithOt), icon: Users, color: 'amber' },
        { label: 'Avg OT / Employee', value: avgOt + 'h', icon: TrendingUp, color: 'emerald' },
      ]" :key="stat.label"
        class="bg-white border border-slate-200 rounded-2xl p-5 flex items-center justify-between"
      >
        <div>
          <p class="text-xs text-slate-400 font-medium mb-1">{{ stat.label }}</p>
          <p class="text-2xl font-bold text-slate-900">{{ stat.value }}</p>
        </div>
        <div :class="`w-10 h-10 rounded-xl bg-${stat.color}-50 flex items-center justify-center`">
          <component :is="stat.icon" :class="`w-5 h-5 text-${stat.color}-500`" />
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-4 items-end">
      <div class="space-y-1">
        <label class="text-xs font-bold uppercase tracking-widest text-slate-500">From</label>
        <input type="date" v-model="dateFrom" class="px-3 py-2 rounded-xl border border-slate-200 text-sm bg-white" />
      </div>
      <div class="space-y-1">
        <label class="text-xs font-bold uppercase tracking-widest text-slate-500">To</label>
        <input type="date" v-model="dateTo" class="px-3 py-2 rounded-xl border border-slate-200 text-sm bg-white" />
      </div>
      <div class="space-y-1">
        <label class="text-xs font-bold uppercase tracking-widest text-slate-500">Employee ID</label>
        <input v-model="employeeFilter" placeholder="Filter by employee..." class="px-3 py-2 rounded-xl border border-slate-200 text-sm bg-white w-52" />
      </div>
      <Button @click="load" :disabled="loading" class="rounded-xl h-10 bg-slate-900 text-white hover:bg-slate-800 text-xs font-bold uppercase tracking-widest">
        {{ loading ? 'Loading...' : 'Apply' }}
      </Button>
    </div>

    <!-- Table -->
    <DataTable :columns="columns" :rows="otRecords" :loading="loading" empty-text="No overtime records found for this period.">
      <template #cell-clock_in="{ value }">{{ fmtTime(value) }}</template>
      <template #cell-clock_out="{ value }">{{ fmtTime(value) }}</template>
      <template #cell-work_hours="{ value }">
        <span class="text-sm text-slate-600">{{ value ? value.toFixed(1) + 'h' : '—' }}</span>
      </template>
      <template #cell-overtime_hours="{ value }">
        <span :class="[
          'font-bold text-sm px-2 py-0.5 rounded-lg',
          value > 4 ? 'bg-rose-100 text-rose-700' : value > 2 ? 'bg-amber-100 text-amber-700' : 'bg-indigo-100 text-indigo-700'
        ]">{{ value?.toFixed(1) }}h</span>
      </template>
      <template #cell-status="{ value }">
        <span class="text-xs text-slate-500 capitalize">{{ value }}</span>
      </template>
    </DataTable>
  </div>
</template>
