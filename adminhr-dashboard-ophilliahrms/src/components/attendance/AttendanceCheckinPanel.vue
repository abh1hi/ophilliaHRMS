<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import { RefreshCwIcon, EyeOffIcon } from 'lucide-vue-next'
import { listCheckins, createCheckin, fetchShiftForCheckin, toggleCheckinSkip } from '../../services/employee-checkin.service'
import type { EmployeeCheckin } from '../../services/employee-checkin.service'

const rows = ref<EmployeeCheckin[]>([])
const total = ref(0)
const loading = ref(false)
const drawerOpen = ref(false)
const form = ref<Partial<EmployeeCheckin & { log_datetime_local: string }>>({})
const saving = ref(false)
const errorMsg = ref('')
const togglingId = ref<string | null>(null)

// Filters
const filterEmployeeId = ref('')
const filterDateFrom = ref('')
const filterDateTo = ref('')
const filterLogType = ref('')

const columns = [
  { key: 'employee_id',     label: 'Employee'      },
  { key: 'log_datetime',    label: 'Date / Time'   },
  { key: 'log_type',        label: 'Type'          },
  { key: 'device_id',       label: 'Device'        },
  { key: 'location_name',   label: 'Location'      },
  { key: 'skip_auto_attendance', label: 'Skip'     },
]

async function load() {
  loading.value = true
  try {
    const res = await listCheckins({
      employee_id: filterEmployeeId.value || undefined,
      from_dt: filterDateFrom.value ? `${filterDateFrom.value}T00:00:00` : undefined,
      to_dt: filterDateTo.value ? `${filterDateTo.value}T23:59:59` : undefined,
      log_type: filterLogType.value as any || undefined,
      limit: 100,
    })
    rows.value = res.checkins
    total.value = res.total
  } catch {}
  finally { loading.value = false }
}

onMounted(load)

function openCreate() {
  form.value = { log_type: 'IN', log_datetime_local: new Date().toISOString().slice(0, 16) }
  errorMsg.value = ''
  drawerOpen.value = true
}

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    const payload: any = { ...form.value }
    if (payload.log_datetime_local) {
      payload.log_datetime = new Date(payload.log_datetime_local).toISOString()
      delete payload.log_datetime_local
    }
    await createCheckin(payload)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message }
  finally { saving.value = false }
}

async function handleFetchShift(id: string) {
  togglingId.value = id
  try { await fetchShiftForCheckin(id); load() } catch {}
  finally { togglingId.value = null }
}

async function handleToggleSkip(id: string) {
  togglingId.value = id
  try { await toggleCheckinSkip(id); load() } catch {}
  finally { togglingId.value = null }
}

function fmtDt(dt: string) {
  const d = new Date(dt)
  return `${d.toLocaleDateString('en')} ${d.toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' })}`
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Employee Checkins" subtitle="Biometric and manual IN/OUT log entries" action-label="+ Log Entry" @action="openCreate" />

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-[20px] px-5 py-4 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]">
      <input v-model="filterEmployeeId" placeholder="Employee ID" class="text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none focus:ring-2 focus:ring-slate-200 w-64" />
      <input type="date" v-model="filterDateFrom" class="text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none" />
      <span class="text-slate-300 self-center">→</span>
      <input type="date" v-model="filterDateTo" class="text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none" />
      <select v-model="filterLogType" class="text-sm border border-slate-200 rounded-[10px] px-3 py-2 outline-none">
        <option value="">All Types</option>
        <option value="IN">IN</option>
        <option value="OUT">OUT</option>
      </select>
      <button @click="load" class="px-5 py-2 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition-colors">Search</button>
    </div>

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="false" empty-text="No checkin logs found.">
      <template #cell-employee_id="{ value }">
        <span class="font-mono text-xs text-slate-400">{{ String(value).slice(0, 8) }}…</span>
      </template>
      <template #cell-log_datetime="{ value }">
        <span class="text-sm text-slate-700">{{ fmtDt(value) }}</span>
      </template>
      <template #cell-log_type="{ value }">
        <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold', value === 'IN' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-600']">{{ value }}</span>
      </template>
      <template #cell-device_id="{ value }">
        <span class="text-xs text-slate-400">{{ value || '—' }}</span>
      </template>
      <template #cell-location_name="{ value }">
        <span class="text-xs text-slate-500">{{ value || '—' }}</span>
      </template>
      <template #cell-skip_auto_attendance="{ value }">
        <span :class="['inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', value ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-400']">{{ value ? 'Skip' : 'Active' }}</span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <button @click="handleFetchShift(row.id)" :disabled="togglingId === row.id" class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-400 hover:text-slate-800 transition-colors" title="Re-resolve shift">
            <RefreshCwIcon class="w-4 h-4" />
          </button>
          <button @click="handleToggleSkip(row.id)" :disabled="togglingId === row.id" class="p-2 rounded-[10px] hover:bg-amber-50 text-slate-400 hover:text-amber-600 transition-colors" title="Toggle skip flag">
            <EyeOffIcon class="w-4 h-4" />
          </button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" title="Log Checkin Entry" width="w-full max-w-md" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Employee ID (UUID)" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" required placeholder="00000000-0000-0000-0000-000000000001" />
        <div>
          <p class="text-xs font-semibold text-slate-500 mb-1">Log Type</p>
          <div class="flex gap-3">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="radio" v-model="form.log_type" value="IN" class="accent-slate-900" /> <span class="text-sm font-medium text-emerald-600">IN</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="radio" v-model="form.log_type" value="OUT" class="accent-slate-900" /> <span class="text-sm font-medium text-rose-600">OUT</span>
            </label>
          </div>
        </div>
        <FormInput label="Date & Time" type="datetime-local" :modelValue="form.log_datetime_local" @update:modelValue="form.log_datetime_local = $event" required />
        <FormInput label="Device ID (optional)" :modelValue="form.device_id" @update:modelValue="form.device_id = $event" placeholder="BIO-001" />
        <FormInput label="Location Name (optional)" :modelValue="form.location_name" @update:modelValue="form.location_name = $event" placeholder="Main Office" />
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="drawerOpen = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="save" :disabled="saving" class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">{{ saving ? 'Saving...' : 'Log Entry' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
