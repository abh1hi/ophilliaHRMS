<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Button } from '../ui/button'
import { RefreshCw, EyeOff, Search, Plus, MapPin, Tablet } from 'lucide-vue-next'
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
const filterLogType = ref('ALL')

const columns = [
  { key: 'employee_id',     label: 'Employee'      },
  { key: 'log_datetime',    label: 'Date / Time'   },
  { key: 'log_type',        label: 'Type'          },
  { key: 'device_id',       label: 'Device'        },
  { key: 'location_name',   label: 'Location'      },
  { key: 'skip_auto_attendance', label: 'Processing' },
]

async function load() {
  loading.value = true
  try {
    const res = await listCheckins({
      employee_id: filterEmployeeId.value || undefined,
      from_dt: filterDateFrom.value ? `${filterDateFrom.value}T00:00:00` : undefined,
      to_dt: filterDateTo.value ? `${filterDateTo.value}T23:59:59` : undefined,
      log_type: filterLogType.value === 'ALL' ? undefined : (filterLogType.value as any),
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
  return `${d.toLocaleDateString('en')} @ ${d.toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' })}`
}

const typeOptions = [
  { value: 'ALL', label: 'All Types' },
  { value: 'IN', label: 'IN Entries' },
  { value: 'OUT', label: 'OUT Entries' },
]
</script>

<template>
  <div class="space-y-8">
    <PageHeader 
      title="Attendance Checkins" 
      subtitle="Biometric and manual clock-in/out logs" 
      action-label="Log Entry" 
      @action="openCreate" 
    />

    <!-- Filters -->
    <div class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-6 shadow-sm">
      <div class="flex flex-wrap items-end gap-4">
        <div class="flex-1 min-w-[200px]">
          <FormInput label="Employee ID" :modelValue="filterEmployeeId" @update:modelValue="filterEmployeeId = $event" placeholder="Search UUID..." />
        </div>
        <div class="w-40">
          <FormInput label="From Date" type="date" :modelValue="filterDateFrom" @update:modelValue="filterDateFrom = $event" />
        </div>
        <div class="w-40">
          <FormInput label="To Date" type="date" :modelValue="filterDateTo" @update:modelValue="filterDateTo = $event" />
        </div>
        <div class="w-40">
          <FormSelect label="Log Type" :modelValue="filterLogType" @update:modelValue="filterLogType = $event" :options="typeOptions" />
        </div>
        <Button @click="load" class="rounded-full px-6 bg-slate-900 text-white hover:bg-slate-800">
          <Search class="w-4 h-4 mr-2" /> Search
        </Button>
      </div>
    </div>

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="false" empty-text="No checkin logs found.">
      <template #cell-employee_id="{ value }">
        <span class="font-mono text-[10px] text-muted-foreground bg-muted/30 px-2 py-0.5 rounded border border-dashed">{{ String(value).slice(0, 13) }}…</span>
      </template>
      <template #cell-log_datetime="{ value }">
        <div class="flex flex-col">
          <span class="text-xs font-bold text-slate-900 dark:text-slate-100">{{ new Date(value).toLocaleDateString() }}</span>
          <span class="text-[10px] text-muted-foreground">{{ new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}</span>
        </div>
      </template>
      <template #cell-log_type="{ value }">
        <span 
          :class="[
            'inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border', 
            value === 'IN' ? 'bg-emerald-100/50 text-emerald-700 border-emerald-200/50' : 'bg-rose-100/50 text-rose-600 border-rose-200/50'
          ]"
        >
          {{ value }}
        </span>
      </template>
      <template #cell-device_id="{ value }">
        <div class="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <Tablet class="w-3 h-3" /> {{ value || '—' }}
        </div>
      </template>
      <template #cell-location_name="{ value }">
        <div class="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <MapPin class="w-3 h-3" /> {{ value || '—' }}
        </div>
      </template>
      <template #cell-skip_auto_attendance="{ value }">
        <span 
          :class="['inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-widest border', value ? 'bg-amber-100/50 text-amber-700 border-amber-200/50' : 'bg-slate-100/50 text-slate-500 border-slate-200/50']"
        >
          {{ value ? 'Skipped' : 'Processed' }}
        </span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <Button variant="ghost" size="icon" @click="handleFetchShift(row.id)" :disabled="togglingId === row.id" class="h-8 w-8 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-900" title="Re-resolve shift">
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': togglingId === row.id }" />
          </Button>
          <Button variant="ghost" size="icon" @click="handleToggleSkip(row.id)" :disabled="togglingId === row.id" class="h-8 w-8 rounded-lg hover:bg-amber-50 text-slate-400 hover:text-amber-600" title="Toggle skip flag">
            <EyeOff class="w-4 h-4" />
          </Button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" title="Log Checkin Entry" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6">
        <FormInput label="Employee ID" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" required placeholder="Employee UUID" />
        
        <div class="space-y-2">
          <p class="text-[11px] font-bold text-muted-foreground uppercase tracking-widest ml-1">Type of Entry</p>
          <div class="flex p-1.5 bg-muted/30 rounded-2xl border border-dashed gap-2">
            <Button 
              class="flex-1 rounded-xl font-bold uppercase tracking-wider text-[10px]" 
              :variant="form.log_type === 'IN' ? 'default' : 'ghost'"
              @click="form.log_type = 'IN'"
            >
              IN Entry
            </Button>
            <Button 
              class="flex-1 rounded-xl font-bold uppercase tracking-wider text-[10px]" 
              :variant="form.log_type === 'OUT' ? 'destructive' : 'ghost'"
              @click="form.log_type = 'OUT'"
            >
              OUT Entry
            </Button>
          </div>
        </div>

        <FormInput label="Log Date & Time" type="datetime-local" :modelValue="form.log_datetime_local" @update:modelValue="form.log_datetime_local = $event" required />
        
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Device Identifier" :modelValue="form.device_id" @update:modelValue="form.device_id = $event" placeholder="e.g. BIO-01" />
          <FormInput label="Location Name" :modelValue="form.location_name" @update:modelValue="form.location_name = $event" placeholder="e.g. Lobby" />
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="errorMsg" class="text-[11px] text-destructive font-bold uppercase tracking-tight">{{ errorMsg }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800 shadow-lg shadow-slate-200 dark:shadow-none">
              {{ saving ? 'Saving...' : 'Log Entry' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
