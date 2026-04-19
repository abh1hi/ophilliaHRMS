<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import { Button } from '../ui/button'
import { Checkbox } from '../ui/checkbox'
import { Label } from '../ui/label'
import { Pencil, Plus, Trash2 } from 'lucide-vue-next'
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
    const payload = { ...form.value }
    if (selected.value) await updateHolidayList(selected.value.id, payload)
    else await createHolidayList(payload)
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
  <div class="space-y-8">
    <PageHeader 
      title="Holiday Lists" 
      subtitle="Manage company and employee holiday calendars" 
      action-label="New List" 
      @action="openCreate" 
    />
    
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No holiday lists yet.">
      <template #cell-is_active="{ value }">
        <span 
          :class="value ? 'bg-emerald-100/50 text-emerald-700 border-emerald-200/50' : 'bg-slate-100/50 text-slate-500 border-slate-200/50'" 
          class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
        >
          {{ value ? 'Active' : 'Inactive' }}
        </span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <Button variant="ghost" size="icon" @click="openEntries(row)" title="Add Entries" class="h-8 w-8 rounded-lg hover:bg-emerald-50 text-slate-400 hover:text-emerald-600">
            <Plus class="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" @click="openEdit(row)" class="h-8 w-8 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-900">
            <Pencil class="w-4 h-4" />
          </Button>
        </div>
      </template>
    </DataTable>

    <!-- Create/Edit drawer -->
    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Holiday List' : 'Create Holiday List'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6">
        <FormInput label="List Name" :modelValue="form.name" @update:modelValue="form.name = $event" placeholder="e.g. National Holidays 2024" required />
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Valid From" type="date" :modelValue="form.from_date" @update:modelValue="form.from_date = $event" required />
          <FormInput label="Valid To" type="date" :modelValue="form.to_date" @update:modelValue="form.to_date = $event" required />
        </div>
        <div class="flex items-center space-x-2 bg-muted/30 p-4 rounded-xl border border-dashed">
          <Checkbox id="hl-active" :checked="!!form.is_active" @update:checked="form.is_active = $event ? 1 : 0" />
          <Label for="hl-active" class="text-xs font-bold uppercase tracking-wider text-muted-foreground cursor-pointer">Active List</Label>
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
              {{ saving ? 'Saving...' : 'Save List' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <!-- Add entries drawer -->
    <SlideDrawer :open="entriesDrawerOpen" :title="`Manage Holidays — ${entriesTarget?.name ?? ''}`" width="w-full max-w-xl" @close="entriesDrawerOpen = false">
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <h4 class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Holiday Entries</h4>
          <Button variant="ghost" size="sm" @click="addEntryRow" class="h-7 text-[10px] font-bold uppercase gap-1 hover:bg-slate-100">
            <Plus class="w-3 h-3" /> Add Row
          </Button>
        </div>

        <div class="space-y-3">
          <div v-for="(entry, i) in newEntries" :key="i" class="p-4 rounded-xl border border-slate-200/60 bg-muted/10 animate-in fade-in slide-in-from-top-1">
            <div class="grid grid-cols-12 gap-4 items-end">
              <div class="col-span-12 sm:col-span-4">
                <FormInput label="Date" type="date" :modelValue="entry.date" @update:modelValue="entry.date = $event" />
              </div>
              <div class="col-span-10 sm:col-span-7">
                <FormInput label="Description" :modelValue="entry.description" @update:modelValue="entry.description = $event" placeholder="e.g. Independence Day" />
              </div>
              <div class="col-span-2 sm:col-span-1 flex justify-end">
                <Button variant="ghost" size="icon" @click="removeEntryRow(i)" class="h-9 w-9 text-slate-400 hover:text-destructive hover:bg-destructive/10 rounded-lg">
                  <Trash2 class="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-end w-full gap-3">
          <Button variant="outline" @click="entriesDrawerOpen = false" class="rounded-full px-6">Cancel</Button>
          <Button @click="saveEntries" :disabled="addingEntries" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
            {{ addingEntries ? 'Saving...' : 'Save All Entries' }}
          </Button>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
