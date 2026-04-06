<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { PencilIcon, Trash2Icon } from 'lucide-vue-next'
import { listShiftTypes, createShiftType, updateShiftType, deleteShiftType } from '../../services/shift-type.service'
import type { ShiftType } from '../../services/shift-type.service'

const rows = ref<ShiftType[]>([]); const loading = ref(false)
const drawerOpen = ref(false); const form = ref<Partial<ShiftType>>({})
const selected = ref<ShiftType | null>(null); const deleteTarget = ref<ShiftType | null>(null)
const saving = ref(false); const deleting = ref(false); const errorMsg = ref('')

const columns = [
  { key: 'name',       label: 'Shift Name'  },
  { key: 'start_time', label: 'Start'       },
  { key: 'end_time',   label: 'End'         },
  { key: 'break_minutes', label: 'Break (min)' },
  { key: 'is_overnight', label: 'Overnight' },
  { key: 'is_active',  label: 'Status'      },
]

async function load() { loading.value = true; try { rows.value = await listShiftTypes() } catch {} finally { loading.value = false } }
onMounted(load)

function openCreate() { selected.value = null; form.value = { break_minutes: 0, grace_period_minutes: 5, is_overnight: 0 }; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: ShiftType) { selected.value = row; form.value = { ...row }; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateShiftType(selected.value.id, form.value)
    else await createShiftType(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return; deleting.value = true
  try { await deleteShiftType(deleteTarget.value.id); deleteTarget.value = null; load() } catch {} finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Shift Types" subtitle="Define shift schedules with start/end times" action-label="+ New Shift Type" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No shift types defined yet.">
      <template #cell-name="{ row, value }">
        <div class="flex items-center gap-2">
          <span v-if="row.color_code" :style="{ backgroundColor: row.color_code }" class="w-3 h-3 rounded-full inline-block shrink-0"></span>
          <span>{{ value }}</span>
        </div>
      </template>
      <template #cell-is_overnight="{ value }">
        <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', value ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-500']">
          {{ value ? 'Yes' : 'No' }}
        </span>
      </template>
      <template #cell-is_active="{ value }">
        <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', value ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500']">
          {{ value ? 'Active' : 'Inactive' }}
        </span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end space-x-2">
          <button @click="openEdit(row)" class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"><PencilIcon class="w-4 h-4" /></button>
          <button @click="deleteTarget = row" class="p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"><Trash2Icon class="w-4 h-4" /></button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Shift Type' : 'New Shift Type'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Shift Name" :modelValue="form.name" @update:modelValue="form.name = $event" required placeholder="e.g. Morning Shift" />
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Start Time" type="time" :modelValue="form.start_time" @update:modelValue="form.start_time = $event" required />
          <FormInput label="End Time" type="time" :modelValue="form.end_time" @update:modelValue="form.end_time = $event" required />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Break (minutes)" type="number" :modelValue="String(form.break_minutes ?? 0)" @update:modelValue="form.break_minutes = Number($event)" />
          <FormInput label="Grace Period (minutes)" type="number" :modelValue="String(form.grace_period_minutes ?? 5)" @update:modelValue="form.grace_period_minutes = Number($event)" />
        </div>
        <div class="space-y-2">
          <label class="block text-sm font-semibold text-slate-700">Color Code</label>
          <div class="flex items-center gap-3">
            <input type="color" :value="form.color_code || '#94a3b8'" @input="form.color_code = ($event.target as HTMLInputElement).value"
              class="w-10 h-10 rounded-[12px] border border-slate-200/60 cursor-pointer" />
            <span class="text-sm text-slate-500">Roster display color</span>
          </div>
        </div>
        <label class="flex items-center space-x-3 cursor-pointer">
          <input type="checkbox" :checked="!!form.is_overnight"
            @change="form.is_overnight = ($event.target as HTMLInputElement).checked ? 1 : 0"
            class="w-4 h-4 rounded border-slate-300" />
          <span class="text-sm font-medium text-slate-700">Overnight shift (crosses midnight)</span>
        </label>
        <FormTextarea label="Description" :modelValue="form.description" @update:modelValue="form.description = $event" placeholder="Optional notes about this shift" />
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
    <ConfirmDialog :open="!!deleteTarget" title="Delete Shift Type?" :message="`Delete '${deleteTarget?.name}'?`" :loading="deleting" @confirm="confirmDelete" @cancel="deleteTarget = null" />
  </div>
</template>
