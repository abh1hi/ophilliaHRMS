<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import { PencilIcon } from 'lucide-vue-next'
import { listLeavePeriods, createLeavePeriod, updateLeavePeriod } from '../../services/leave-period.service'
import type { LeavePeriod } from '../../services/leave-period.service'

const rows = ref<LeavePeriod[]>([])
const loading = ref(false)
const drawerOpen = ref(false)
const selected = ref<LeavePeriod | null>(null)
const form = ref<Partial<LeavePeriod>>({})
const saving = ref(false)
const errorMsg = ref('')

const columns = [
  { key: 'name', label: 'Period Name' },
  { key: 'from_date', label: 'From' },
  { key: 'to_date', label: 'To' },
  { key: 'is_active', label: 'Active' },
]

async function load() {
  loading.value = true
  try { rows.value = await listLeavePeriods(true) } catch {} finally { loading.value = false }
}
onMounted(load)

function openCreate() { selected.value = null; form.value = { is_active: 1 }; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: LeavePeriod) { selected.value = row; form.value = { ...row }; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateLeavePeriod(selected.value.id, form.value)
    else await createLeavePeriod(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Leave Periods" subtitle="Define fiscal or leave year periods" action-label="+ New Period" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No leave periods yet.">
      <template #cell-is_active="{ value }">
        <span :class="value ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ value ? 'Active' : 'Inactive' }}</span>
      </template>
      <template #actions="{ row }">
        <button @click="openEdit(row)" class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"><PencilIcon class="w-4 h-4" /></button>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Leave Period' : 'New Leave Period'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Period Name" :modelValue="form.name" @update:modelValue="form.name = $event" required />
        <FormInput label="From Date" type="date" :modelValue="form.from_date" @update:modelValue="form.from_date = $event" required />
        <FormInput label="To Date" type="date" :modelValue="form.to_date" @update:modelValue="form.to_date = $event" required />
        <div class="flex items-center gap-3">
          <input type="checkbox" id="period-active" :checked="!!form.is_active" @change="form.is_active = ($event.target as HTMLInputElement).checked ? 1 : 0" class="w-4 h-4 rounded" />
          <label for="period-active" class="text-sm font-medium text-slate-700">Active</label>
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="drawerOpen = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="save" :disabled="saving" class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
