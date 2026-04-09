<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import { PencilIcon, PlusIcon, Trash2Icon } from 'lucide-vue-next'
import { listLeaveBlockLists, createLeaveBlockList, updateLeaveBlockList } from '../../services/leave-block-list.service'
import type { LeaveBlockList, LeaveBlockListDate } from '../../services/leave-block-list.service'

const rows = ref<LeaveBlockList[]>([])
const loading = ref(false)
const drawerOpen = ref(false)
const selected = ref<LeaveBlockList | null>(null)
const form = ref<Partial<LeaveBlockList> & { dates: Partial<LeaveBlockListDate>[] }>({ dates: [] })
const saving = ref(false)
const errorMsg = ref('')

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'applies_to_company', label: 'Company-wide' },
  { key: 'is_active', label: 'Active' },
]

async function load() {
  loading.value = true
  try { rows.value = await listLeaveBlockLists(true) } catch {} finally { loading.value = false }
}
onMounted(load)

function openCreate() {
  selected.value = null
  form.value = { is_active: 1, applies_to_company: 1, dates: [{ block_date: '', reason: '' }] }
  errorMsg.value = ''; drawerOpen.value = true
}
function openEdit(row: LeaveBlockList) {
  selected.value = row
  form.value = { ...row, dates: row.dates.map(d => ({ ...d })) }
  errorMsg.value = ''; drawerOpen.value = true
}

function addDate() { form.value.dates.push({ block_date: '', reason: '' }) }
function removeDate(i: number) { form.value.dates.splice(i, 1) }

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateLeaveBlockList(selected.value.id, { name: form.value.name, applies_to_company: form.value.applies_to_company, is_active: form.value.is_active })
    else await createLeaveBlockList(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Leave Block Lists" subtitle="Define dates on which leave is blocked" action-label="+ New Block List" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No block lists yet.">
      <template #cell-applies_to_company="{ value }">
        <span :class="value ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-500'" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ value ? 'Yes' : 'No' }}</span>
      </template>
      <template #cell-is_active="{ value }">
        <span :class="value ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ value ? 'Active' : 'Inactive' }}</span>
      </template>
      <template #actions="{ row }">
        <button @click="openEdit(row)" class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"><PencilIcon class="w-4 h-4" /></button>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Block List' : 'New Block List'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Name" :modelValue="form.name" @update:modelValue="form.name = $event" required />
        <div class="flex gap-6">
          <div class="flex items-center gap-2">
            <input type="checkbox" id="bl-company" :checked="!!form.applies_to_company" @change="form.applies_to_company = ($event.target as HTMLInputElement).checked ? 1 : 0" class="w-4 h-4 rounded" />
            <label for="bl-company" class="text-sm font-medium text-slate-700">Applies Company-wide</label>
          </div>
          <div class="flex items-center gap-2">
            <input type="checkbox" id="bl-active" :checked="!!form.is_active" @change="form.is_active = ($event.target as HTMLInputElement).checked ? 1 : 0" class="w-4 h-4 rounded" />
            <label for="bl-active" class="text-sm font-medium text-slate-700">Active</label>
          </div>
        </div>

        <div v-if="!selected" class="space-y-3">
          <label class="block text-sm font-semibold text-slate-700">Blocked Dates</label>
          <div v-for="(d, i) in form.dates" :key="i" class="flex gap-2 items-end">
            <FormInput label="Date" type="date" :modelValue="d.block_date" @update:modelValue="d.block_date = $event" />
            <FormInput label="Reason" :modelValue="d.reason" @update:modelValue="d.reason = $event" />
            <button @click="removeDate(i)" class="mb-1 p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"><Trash2Icon class="w-4 h-4" /></button>
          </div>
          <button @click="addDate" class="text-sm text-slate-600 hover:text-slate-900 flex items-center gap-1"><PlusIcon class="w-4 h-4" /> Add Date</button>
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
