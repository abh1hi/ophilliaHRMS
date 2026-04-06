<script setup lang="ts">
import { ref } from 'vue'
import { UsersIcon, CheckSquareIcon } from 'lucide-vue-next'
import { getEmployeesForBulk } from '../../services/attendance.service'
import { apiFetchData } from '../../services/http'

const departmentId = ref('')
const branchId = ref('')
const date = ref(new Date().toISOString().slice(0, 10))
const employees = ref<any[]>([])
const selectedIds = ref<Set<string>>(new Set())
const employeeStatus = ref<Record<string, string>>({})
const loading = ref(false)
const submitting = ref(false)
const results = ref<any[] | null>(null)
const errorMsg = ref('')

async function loadEmployees() {
  loading.value = true; errorMsg.value = ''; results.value = null
  try {
    employees.value = await getEmployeesForBulk(
      departmentId.value || undefined,
      branchId.value || undefined,
    )
    // Pre-select all and default status to present
    selectedIds.value = new Set(employees.value.map((e: any) => e.id))
    employees.value.forEach((e: any) => { employeeStatus.value[e.id] = 'present' })
  } catch (e: any) { errorMsg.value = e.message }
  finally { loading.value = false }
}

function toggleAll(checked: boolean) {
  if (checked) selectedIds.value = new Set(employees.value.map((e: any) => e.id))
  else selectedIds.value = new Set()
}

function toggleEmployee(id: string, checked: boolean) {
  if (checked) selectedIds.value.add(id)
  else selectedIds.value.delete(id)
}

async function submitBulk() {
  if (selectedIds.value.size === 0) return
  submitting.value = true; errorMsg.value = ''; results.value = null
  try {
    const entries = [...selectedIds.value].map(id => ({
      employee_id: id,
      status: employeeStatus.value[id] ?? 'present',
    }))
    const res = await apiFetchData<any>('/attendance/school-mode/bulk', {
      method: 'POST',
      body: JSON.stringify({ date: date.value, entries }),
    })
    results.value = res.results ?? []
  } catch (e: any) { errorMsg.value = e.message }
  finally { submitting.value = false }
}

const allChecked = () => employees.value.length > 0 && employees.value.every((e: any) => selectedIds.value.has(e.id))
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-start justify-between">
      <div>
        <h2 class="text-xl font-bold text-slate-900">Bulk Attendance Tool</h2>
        <p class="text-sm text-slate-500 mt-0.5">Mark attendance for a group of employees at once</p>
      </div>
    </div>

    <!-- Step 1: Filters -->
    <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 space-y-5 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
      <h3 class="text-sm font-semibold text-slate-700">Step 1 — Select Employees</h3>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label class="text-xs font-semibold text-slate-500 block mb-1">Date</label>
          <input type="date" v-model="date" class="w-full text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none focus:ring-2 focus:ring-slate-200" />
        </div>
        <div>
          <label class="text-xs font-semibold text-slate-500 block mb-1">Department ID (optional)</label>
          <input v-model="departmentId" placeholder="UUID" class="w-full text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none focus:ring-2 focus:ring-slate-200" />
        </div>
        <div>
          <label class="text-xs font-semibold text-slate-500 block mb-1">Branch ID (optional)</label>
          <input v-model="branchId" placeholder="UUID" class="w-full text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none focus:ring-2 focus:ring-slate-200" />
        </div>
      </div>
      <button @click="loadEmployees" :disabled="loading" class="flex items-center gap-2 px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">
        <UsersIcon class="w-4 h-4" /> {{ loading ? 'Loading…' : 'Load Employees' }}
      </button>
      <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p>
    </div>

    <!-- Step 2: Employee list -->
    <div v-if="employees.length > 0" class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)] overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200/60">
        <h3 class="text-sm font-semibold text-slate-700">Step 2 — Set Status &amp; Submit</h3>
        <label class="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
          <input type="checkbox" :checked="allChecked()" @change="toggleAll(($event.target as HTMLInputElement).checked)" class="accent-slate-900 w-4 h-4" />
          Select All ({{ employees.length }})
        </label>
      </div>
      <div class="divide-y divide-slate-100">
        <div v-for="emp in employees" :key="emp.id" class="flex items-center gap-4 px-6 py-3 hover:bg-slate-50/50 transition-colors">
          <input type="checkbox" :checked="selectedIds.has(emp.id)" @change="toggleEmployee(emp.id, ($event.target as HTMLInputElement).checked)" class="accent-slate-900 w-4 h-4 shrink-0" />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-800">{{ emp.first_name ?? '' }} {{ emp.last_name ?? '' }} <span class="font-mono text-xs text-slate-400 ml-1">{{ emp.id?.slice(0, 8) }}…</span></p>
          </div>
          <select v-model="employeeStatus[emp.id]" :disabled="!selectedIds.has(emp.id)" class="text-sm border border-slate-200 rounded-[10px] px-3 py-1.5 outline-none disabled:opacity-40">
            <option value="present">Present</option>
            <option value="absent">Absent</option>
            <option value="half_day">Half Day</option>
          </select>
        </div>
      </div>
      <div class="px-6 py-4 border-t border-slate-100">
        <button @click="submitBulk" :disabled="submitting || selectedIds.size === 0" class="flex items-center gap-2 px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">
          <CheckSquareIcon class="w-4 h-4" /> {{ submitting ? 'Marking…' : `Mark ${selectedIds.size} Employees` }}
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="results" class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[24px] p-6 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
      <h3 class="text-sm font-semibold text-slate-700 mb-4">Results</h3>
      <div class="grid grid-cols-3 gap-4 mb-4">
        <div class="text-center p-3 bg-slate-50 rounded-[14px]">
          <p class="text-2xl font-bold text-slate-900">{{ results.length }}</p>
          <p class="text-xs text-slate-500 mt-0.5">Total</p>
        </div>
        <div class="text-center p-3 bg-emerald-50 rounded-[14px]">
          <p class="text-2xl font-bold text-emerald-700">{{ results.filter((r: any) => r.success).length }}</p>
          <p class="text-xs text-emerald-600 mt-0.5">Succeeded</p>
        </div>
        <div class="text-center p-3 bg-rose-50 rounded-[14px]">
          <p class="text-2xl font-bold text-rose-600">{{ results.filter((r: any) => !r.success).length }}</p>
          <p class="text-xs text-rose-500 mt-0.5">Failed</p>
        </div>
      </div>
      <div v-for="r in results.filter((r: any) => !r.success)" :key="r.employee_id" class="text-xs text-rose-600 py-1">
        <span class="font-mono">{{ r.employee_id?.slice(0, 8) }}…</span> — {{ r.error }}
      </div>
    </div>
  </div>
</template>
