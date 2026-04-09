<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import { PencilIcon, PlusIcon, Trash2Icon } from 'lucide-vue-next'
import { listHolidayLists, createHolidayList, updateHolidayList, addHolidayListEntries } from '../../services/holiday-list.service'
import type { HolidayList, HolidayListEntry } from '../../services/holiday-list.service'

const rows = ref<HolidayList[]>([])
const loading = ref(false)
const drawerOpen = ref(false)
const selected = ref<HolidayList | null>(null)
const form = ref<Partial<HolidayList>>({})
const saving = ref(false)
const errorMsg = ref('')

// Entries drawer
const entriesDrawerOpen = ref(false)
const entriesTarget = ref<HolidayList | null>(null)
const newEntries = ref<Array<{ date: string; description: string }>>([])
const addingEntries = ref(false)

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'from_date', label: 'From' },
  { key: 'to_date', label: 'To' },
  { key: 'is_active', label: 'Active' },
]

async function load() {
  loading.value = true
  try { rows.value = await listHolidayLists(true) } catch {} finally { loading.value = false }
}
onMounted(load)

function openCreate() { selected.value = null; form.value = { is_active: 1 }; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: HolidayList) { selected.value = row; form.value = { ...row }; errorMsg.value = ''; drawerOpen.value = true }
function openEntries(row: HolidayList) { entriesTarget.value = row; newEntries.value = [{ date: '', description: '' }]; entriesDrawerOpen.value = true }

function addEntryRow() { newEntries.value.push({ date: '', description: '' }) }
function removeEntryRow(i: number) { newEntries.value.splice(i, 1) }

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateHolidayList(selected.value.id, form.value)
    else await createHolidayList(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function saveEntries() {
  if (!entriesTarget.value) return
  addingEntries.value = true
  try {
    await addHolidayListEntries(entriesTarget.value.id, newEntries.value.filter(e => e.date))
    entriesDrawerOpen.value = false; load()
  } catch {} finally { addingEntries.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Holiday Lists" subtitle="Manage company and employee holiday calendars" action-label="+ New List" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No holiday lists yet.">
      <template #cell-is_active="{ value }">
        <span :class="value ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ value ? 'Active' : 'Inactive' }}</span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end space-x-2">
          <button @click="openEntries(row)" title="Add Entries" class="p-2 rounded-[10px] hover:bg-emerald-50 text-slate-400 hover:text-emerald-600 transition-colors"><PlusIcon class="w-4 h-4" /></button>
          <button @click="openEdit(row)" class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"><PencilIcon class="w-4 h-4" /></button>
        </div>
      </template>
    </DataTable>

    <!-- Create/Edit drawer -->
    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Holiday List' : 'New Holiday List'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Name" :modelValue="form.name" @update:modelValue="form.name = $event" required />
        <FormInput label="From Date" type="date" :modelValue="form.from_date" @update:modelValue="form.from_date = $event" required />
        <FormInput label="To Date" type="date" :modelValue="form.to_date" @update:modelValue="form.to_date = $event" required />
        <div class="flex items-center gap-3">
          <input type="checkbox" id="hl-active" :checked="!!form.is_active" @change="form.is_active = ($event.target as HTMLInputElement).checked ? 1 : 0" class="w-4 h-4 rounded" />
          <label for="hl-active" class="text-sm font-medium text-slate-700">Active</label>
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

    <!-- Add entries drawer -->
    <SlideDrawer :open="entriesDrawerOpen" :title="`Add Holidays — ${entriesTarget?.name ?? ''}`" width="w-full max-w-lg" @close="entriesDrawerOpen = false">
      <div class="space-y-3">
        <div v-for="(entry, i) in newEntries" :key="i" class="flex gap-2 items-end">
          <FormInput label="Date" type="date" :modelValue="entry.date" @update:modelValue="entry.date = $event" />
          <FormInput label="Description" :modelValue="entry.description" @update:modelValue="entry.description = $event" />
          <button @click="removeEntryRow(i)" class="mb-1 p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"><Trash2Icon class="w-4 h-4" /></button>
        </div>
        <button @click="addEntryRow" class="text-sm text-slate-600 hover:text-slate-900 flex items-center gap-1"><PlusIcon class="w-4 h-4" /> Add Row</button>
      </div>
      <template #footer>
        <div class="flex justify-end space-x-3">
          <button @click="entriesDrawerOpen = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
          <button @click="saveEntries" :disabled="addingEntries" class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">{{ addingEntries ? 'Saving...' : 'Save Entries' }}</button>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
