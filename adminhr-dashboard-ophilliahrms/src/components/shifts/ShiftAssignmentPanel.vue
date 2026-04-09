<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { PencilIcon, Trash2Icon } from 'lucide-vue-next'
import { listShiftAssignments, createShiftAssignment, updateShiftAssignment, deleteShiftAssignment } from '../../services/shift-assignment.service'
import { listShiftTypes } from '../../services/shift-type.service'
import { listShiftLocations } from '../../services/shift-location.service'
import type { ShiftAssignment } from '../../services/shift-assignment.service'
import type { ShiftType } from '../../services/shift-type.service'
import type { ShiftLocation } from '../../services/shift-location.service'

const rows = ref<ShiftAssignment[]>([]); const loading = ref(false)
const shiftTypes = ref<ShiftType[]>([]); const shiftLocations = ref<ShiftLocation[]>([])
const drawerOpen = ref(false); const form = ref<Partial<ShiftAssignment>>({})
const selected = ref<ShiftAssignment | null>(null); const deleteTarget = ref<ShiftAssignment | null>(null)
const saving = ref(false); const deleting = ref(false); const errorMsg = ref('')

const shiftTypeOptions = computed(() => [
  { value: '', label: '— None —' },
  ...shiftTypes.value.map(t => ({ value: t.id, label: t.name })),
])
const shiftLocationOptions = computed(() => [
  { value: '', label: '— None —' },
  ...shiftLocations.value.map(l => ({ value: l.id, label: l.name })),
])

const shiftTypeMap = computed(() => Object.fromEntries(shiftTypes.value.map(t => [t.id, t])))

const columns = [
  { key: 'employee_id',    label: 'Employee ID'    },
  { key: 'shift_type_id',  label: 'Shift Type'     },
  { key: 'effective_from', label: 'From'           },
  { key: 'effective_to',   label: 'To'             },
  { key: 'is_active',      label: 'Status'         },
]

async function load() {
  loading.value = true
  try {
    [rows.value, shiftTypes.value, shiftLocations.value] = await Promise.all([
      listShiftAssignments(), listShiftTypes(), listShiftLocations()
    ])
  } catch {} finally { loading.value = false }
}
onMounted(load)

function openCreate() { selected.value = null; form.value = {}; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: ShiftAssignment) { selected.value = row; form.value = { ...row }; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    const payload = {
      ...form.value,
      shift_type_id: form.value.shift_type_id || undefined,
      shift_location_id: form.value.shift_location_id || undefined,
    }
    if (selected.value) await updateShiftAssignment(selected.value.id, payload)
    else await createShiftAssignment(payload)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return; deleting.value = true
  try { await deleteShiftAssignment(deleteTarget.value.id); deleteTarget.value = null; load() } catch {} finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Shift Assignments" subtitle="Assign shifts to employees with effective date ranges" action-label="+ New Assignment" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No assignments yet.">
      <template #cell-employee_id="{ value }">
        <span class="font-mono text-xs text-slate-500">{{ value?.slice(0, 8) }}…</span>
      </template>
      <template #cell-shift_type_id="{ value }">
        <div v-if="value && shiftTypeMap[value]" class="flex items-center gap-2">
          <span v-if="shiftTypeMap[value].color_code" :style="{ backgroundColor: shiftTypeMap[value].color_code }" class="w-2.5 h-2.5 rounded-full shrink-0"></span>
          <span class="text-sm">{{ shiftTypeMap[value].name }}</span>
        </div>
        <span v-else class="text-slate-400 text-xs">—</span>
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

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Assignment' : 'New Shift Assignment'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Employee ID" :modelValue="form.employee_id" @update:modelValue="form.employee_id = $event" required placeholder="Employee UUID" />
        <FormSelect label="Shift Type" :modelValue="form.shift_type_id ?? ''" :options="shiftTypeOptions" @update:modelValue="form.shift_type_id = $event || undefined" />
        <FormSelect label="Shift Location" :modelValue="form.shift_location_id ?? ''" :options="shiftLocationOptions" @update:modelValue="form.shift_location_id = $event || undefined" />
        <div class="grid grid-cols-2 gap-4">
          <FormInput label="Effective From" type="date" :modelValue="form.effective_from" @update:modelValue="form.effective_from = $event" required />
          <FormInput label="Effective To" type="date" :modelValue="form.effective_to" @update:modelValue="form.effective_to = $event || undefined" placeholder="Leave blank for indefinite" />
        </div>
        <FormTextarea label="Notes" :modelValue="form.notes" @update:modelValue="form.notes = $event" placeholder="Optional notes" />
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
    <ConfirmDialog :open="!!deleteTarget" title="Remove Assignment?" :message="`Remove shift assignment for this employee?`" :loading="deleting" @confirm="confirmDelete" @cancel="deleteTarget = null" />
  </div>
</template>
