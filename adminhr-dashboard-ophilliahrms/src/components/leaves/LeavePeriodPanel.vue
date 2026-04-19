<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import { Button } from '../ui/button'
import { Checkbox } from '../ui/checkbox'
import { Label } from '../ui/label'
import { Pencil } from 'lucide-vue-next'
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
    const payload = { ...form.value }
    if (selected.value) await updateLeavePeriod(selected.value.id, payload)
    else await createLeavePeriod(payload)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}
</script>

<template>
  <div class="space-y-8">
    <PageHeader 
      title="Leave Periods" 
      subtitle="Define fiscal or leave year periods" 
      action-label="New Period" 
      @action="openCreate" 
    />
    
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No leave periods yet.">
      <template #cell-is_active="{ value }">
        <span 
          :class="value ? 'bg-emerald-100/50 text-emerald-700 border-emerald-200/50' : 'bg-slate-100/50 text-slate-500 border-slate-200/50'" 
          class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
        >
          {{ value ? 'Active' : 'Inactive' }}
        </span>
      </template>
      <template #actions="{ row }">
        <Button variant="ghost" size="icon" @click="openEdit(row)" class="h-8 w-8 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-900">
          <Pencil class="w-4 h-4" />
        </Button>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Leave Period' : 'Create Leave Period'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6">
        <FormInput label="Period Name" :modelValue="form.name" @update:modelValue="form.name = $event" placeholder="e.g. Leave Year 2024-25" required />
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Start Date" type="date" :modelValue="form.from_date" @update:modelValue="form.from_date = $event" required />
          <FormInput label="End Date" type="date" :modelValue="form.to_date" @update:modelValue="form.to_date = $event" required />
        </div>
        <div class="flex items-center space-x-2 bg-muted/30 p-4 rounded-xl border border-dashed">
          <Checkbox id="period-active" :checked="!!form.is_active" @update:checked="form.is_active = $event ? 1 : 0" />
          <Label for="period-active" class="text-xs font-bold uppercase tracking-wider text-muted-foreground cursor-pointer">Active Period</Label>
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
              {{ saving ? 'Saving...' : 'Save Period' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
