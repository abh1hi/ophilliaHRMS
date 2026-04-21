<script setup lang="ts">
import { ref, computed } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Button } from '../ui/button'
import { Checkbox } from '../ui/checkbox'
import { Label } from '../ui/label'
import { Users, CheckSquare, Search, Hash, AlertCircle, CheckCircle2, UserCircle2, Info } from 'lucide-vue-next'
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

const isAllChecked = computed(() => employees.value.length > 0 && employees.value.every((e: any) => selectedIds.value.has(e.id)))

const attStatusOptions = [
  { value: 'present', label: 'Present' },
  { value: 'absent', label: 'Absent' },
  { value: 'half_day', label: 'Half Day' },
]

const resultStats = computed(() => {
  if (!results.value) return null
  return {
    total: results.value.length,
    success: results.value.filter((r: any) => r.success).length,
    failed: results.value.filter((r: any) => !r.success).length,
  }
})
</script>

<template>
  <div class="space-y-10">
    <PageHeader 
      title="Bulk Attendance" 
      subtitle="Rapid multi-employee attendance processing" 
    />

    <!-- Step 1: Filters -->
    <div class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-8 shadow-sm">
      <div class="flex items-center gap-2 mb-6 text-slate-900 dark:text-slate-50">
        <Users class="w-4 h-4 text-muted-foreground" />
        <h3 class="text-xs font-bold uppercase tracking-widest">Step 1 — Define Group</h3>
      </div>
      
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <FormInput label="Processing Date" type="date" v-model="date" required />
        <FormInput label="Department" v-model="departmentId" placeholder="Department UUID..." />
        <FormInput label="Branch" v-model="branchId" placeholder="Branch UUID..." />
      </div>
      
      <div class="mt-8 flex items-center justify-between">
        <p v-if="errorMsg" class="text-xs font-bold text-destructive uppercase tracking-tight">{{ errorMsg }}</p>
        <div v-else></div>
        <Button @click="loadEmployees" :disabled="loading" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800 shadow-lg shadow-slate-200">
          <Search class="w-4 h-4 mr-2" /> {{ loading ? 'Fetching...' : 'Fetch Employee List' }}
        </Button>
      </div>
    </div>

    <!-- Step 2: Employee list -->
    <div v-if="employees.length > 0" class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 overflow-hidden shadow-sm animate-in fade-in slide-in-from-top-4">
      <div class="flex items-center justify-between px-8 py-5 border-b border-white/10 bg-slate-50/50">
        <div class="flex items-center gap-2">
          <CheckSquare class="w-4 h-4 text-muted-foreground" />
          <h3 class="text-xs font-bold uppercase tracking-widest">Step 2 — Selection & Status</h3>
        </div>
        <div class="flex items-center space-x-2">
          <Checkbox id="bulk-all" :checked="isAllChecked" @update:checked="toggleAll($event)" />
          <Label for="bulk-all" class="text-[11px] font-bold uppercase tracking-widest text-muted-foreground cursor-pointer">
            Select All ({{ employees.length }})
          </Label>
        </div>
      </div>
      
      <div class="divide-y divide-white/10 max-h-[500px] overflow-y-auto">
        <div v-for="emp in employees" :key="emp.id" class="flex items-center gap-6 px-8 py-4 hover:bg-white/20 transition-colors">
          <Checkbox :checked="selectedIds.has(emp.id)" @update:checked="toggleEmployee(emp.id, $event)" />
          
          <div class="flex-1 flex items-center gap-3 min-w-0">
            <div class="h-8 w-8 rounded-full bg-muted/50 flex items-center justify-center border border-dashed text-muted-foreground">
              <UserCircle2 class="w-5 h-5" />
            </div>
            <div class="flex flex-col">
              <p class="text-[13px] font-bold text-slate-900">{{ emp.first_name }} {{ emp.last_name }}</p>
              <div class="flex items-center gap-1 opacity-60">
                <Hash class="w-3 h-3" />
                <span class="font-mono text-[10px]">{{ emp.id?.slice(0, 13) }}…</span>
              </div>
            </div>
          </div>
          
          <div class="w-40">
            <FormSelect 
              :modelValue="employeeStatus[emp.id]" 
              @update:modelValue="employeeStatus[emp.id] = $event" 
              :options="attStatusOptions"
              :disabled="!selectedIds.has(emp.id)"
            />
          </div>
        </div>
      </div>
      
      <div class="px-8 py-5 border-t border-white/10 bg-slate-50/50 flex items-center justify-between">
        <p class="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
          {{ selectedIds.size }} of {{ employees.length }} Selected
        </p>
        <Button @click="submitBulk" :disabled="submitting || selectedIds.size === 0" class="rounded-full px-10 bg-slate-900 text-white hover:bg-slate-800 shadow-lg shadow-slate-200">
          <CheckCircle2 class="w-4 h-4 mr-2" /> {{ submitting ? 'Processing...' : `Confirm & Save Attendance` }}
        </Button>
      </div>
    </div>

    <!-- Results Summary -->
    <div v-if="resultStats" class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-8 shadow-sm animate-in zoom-in-95">
      <div class="flex items-center gap-2 mb-8">
        <Info class="w-4 h-4 text-muted-foreground" />
        <h3 class="text-xs font-bold uppercase tracking-widest">Processing Results</h3>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="p-6 rounded-3xl bg-slate-50/50 border border-dashed text-center">
          <p class="text-3xl font-black text-slate-900 tracking-tighter">{{ resultStats.total }}</p>
          <p class="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mt-1">Processed</p>
        </div>
        <div class="p-6 rounded-3xl bg-emerald-50/50 border border-emerald-100 text-center">
          <p class="text-3xl font-black text-emerald-600 tracking-tighter">{{ resultStats.success }}</p>
          <p class="text-[10px] font-bold uppercase tracking-widest text-emerald-600/70 mt-1">Succeeded</p>
        </div>
        <div class="p-6 rounded-3xl bg-rose-50/50 border border-rose-100 text-center">
          <p class="text-3xl font-black text-rose-600 tracking-tighter">{{ resultStats.failed }}</p>
          <p class="text-[10px] font-bold uppercase tracking-widest text-rose-600/70 mt-1">Failed</p>
        </div>
      </div>
      
      <div v-if="resultStats.failed > 0" class="mt-8 space-y-2">
        <p class="text-[11px] font-bold text-destructive uppercase tracking-widest mb-3">Error Log</p>
        <div v-for="r in results?.filter((r: any) => !r.success)" :key="r.employee_id" class="flex items-center gap-3 text-[11px] p-3 rounded-xl bg-destructive/5 text-destructive border border-destructive/10">
          <AlertCircle class="w-3.5 h-3.5" />
          <span class="font-mono">{{ r.employee_id?.slice(0, 13) }}…</span>
          <span class="font-bold flex-1">{{ r.error }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
