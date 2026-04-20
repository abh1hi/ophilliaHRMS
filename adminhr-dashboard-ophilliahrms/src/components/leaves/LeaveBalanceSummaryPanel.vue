<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Users } from 'lucide-vue-next'
import EmptyState from '../ui/EmptyState.vue'
import { listLeaveAllocations } from '../../services/leave-allocation.service'
import { listLeaveTypes } from '../../services/leave-type.service'
import type { LeaveAllocation } from '../../services/leave-allocation.service'
import type { LeaveType } from '../../services/leave-type.service'

const allocations = ref<LeaveAllocation[]>([])
const leaveTypes = ref<LeaveType[]>([])
const loading = ref(false)
const search = ref('')

async function load() {
  loading.value = true
  try {
    const [allocRes, typesRes] = await Promise.all([
      listLeaveAllocations({ skip: 0, limit: 500 }),
      listLeaveTypes(),
    ])
    allocations.value = allocRes.allocations
    leaveTypes.value = typesRes
  } catch {} finally { loading.value = false }
}
onMounted(load)

const typeMap = computed(() => Object.fromEntries(leaveTypes.value.map(t => [t.id, t.name])))

const groupedByEmployee = computed(() => {
  const map: Record<string, Record<string, { allocated: number; used: number }>> = {}
  for (const a of allocations.value) {
    if (a.status !== 'active') continue
    if (!map[a.employee_id]) map[a.employee_id] = {}
    const typeName = typeMap.value[a.leave_type_id] ?? a.leave_type_id
    if (!map[a.employee_id][typeName]) map[a.employee_id][typeName] = { allocated: 0, used: 0 }
    map[a.employee_id][typeName].allocated += a.total_leaves_allocated
    map[a.employee_id][typeName].used += a.used_leaves
  }
  return map
})

const uniqueTypeNames = computed(() => {
  const names = new Set<string>()
  for (const byType of Object.values(groupedByEmployee.value))
    Object.keys(byType).forEach(n => names.add(n))
  return Array.from(names).sort()
})

const filteredEmployees = computed(() => {
  const q = search.value.toLowerCase()
  return Object.keys(groupedByEmployee.value).filter(id => !q || id.toLowerCase().includes(q))
})

function remaining(emp: string, type: string) {
  const b = groupedByEmployee.value[emp]?.[type]
  if (!b) return null
  return b.allocated - b.used
}

function cellClass(rem: number | null, allocated: number) {
  if (rem === null) return 'text-slate-300'
  const pct = allocated > 0 ? rem / allocated : 0
  if (pct >= 0.5) return 'text-emerald-700 bg-emerald-50'
  if (pct >= 0.2) return 'text-amber-700 bg-amber-50'
  return 'text-rose-700 bg-rose-50'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-base font-semibold text-slate-900">Leave Balance Summary</h2>
        <p class="text-xs text-slate-500 mt-0.5">Active leave balances across all employees and types</p>
      </div>
      <div class="relative">
        <input
          v-model="search"
          placeholder="Search employee…"
          class="h-9 pl-3 pr-4 rounded-xl border border-slate-200 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-300 bg-white w-56"
        />
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="w-6 h-6 border-2 border-slate-300 border-t-slate-700 rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <EmptyState
      v-else-if="!filteredEmployees.length"
      :icon="Users"
      title="No leave balances found"
      description="Leave balances appear here once leave allocations are created for employees."
    />

    <!-- Grid table -->
    <div v-else class="overflow-x-auto rounded-2xl border border-slate-200/60 bg-white shadow-sm">
      <table class="w-full text-xs">
        <thead>
          <tr class="border-b border-slate-100 bg-slate-50">
            <th class="text-left px-5 py-3 font-bold uppercase tracking-widest text-[10px] text-slate-500 sticky left-0 bg-slate-50 min-w-[200px]">
              Employee
            </th>
            <th
              v-for="type in uniqueTypeNames"
              :key="type"
              class="text-center px-4 py-3 font-bold uppercase tracking-widest text-[10px] text-slate-500 whitespace-nowrap min-w-[120px]"
            >
              {{ type }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="empId in filteredEmployees"
            :key="empId"
            class="border-b border-slate-100/60 hover:bg-slate-50/50 transition-colors"
          >
            <td class="px-5 py-3 font-medium text-slate-700 sticky left-0 bg-white text-[11px]">
              <span class="font-mono text-slate-400">{{ empId.slice(0, 8) }}…</span>
            </td>
            <td
              v-for="type in uniqueTypeNames"
              :key="type"
              class="text-center px-4 py-3"
            >
              <template v-if="groupedByEmployee[empId]?.[type]">
                <span
                  :class="cellClass(remaining(empId, type), groupedByEmployee[empId][type].allocated)"
                  class="inline-flex items-center justify-center w-14 h-7 rounded-lg text-[11px] font-bold"
                >
                  {{ remaining(empId, type) }} / {{ groupedByEmployee[empId][type].allocated }}
                </span>
              </template>
              <span v-else class="text-slate-200">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Legend -->
    <div class="flex items-center gap-5 text-[10px] font-bold uppercase tracking-widest text-slate-400">
      <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-emerald-100 border border-emerald-200"></span> ≥ 50% remaining</span>
      <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-amber-100 border border-amber-200"></span> 20–49% remaining</span>
      <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-rose-100 border border-rose-200"></span> &lt; 20% remaining</span>
    </div>
  </div>
</template>
