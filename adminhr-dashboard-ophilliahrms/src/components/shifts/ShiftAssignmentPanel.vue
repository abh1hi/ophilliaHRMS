<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import EntitySearchSelect from '../ui/EntitySearchSelect.vue'
import FormSelect from '../ui/FormSelect.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { Button } from '@/components/ui/button'
import {
  Pencil,
  Trash2,
  UserPlus,
  CheckCircle2,
  XCircle,
  CalendarClock,
  Info,
  ArrowRight
} from 'lucide-vue-next'
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

const shiftTypeOptions = computed(() => shiftTypes.value.map(t => ({ value: t.id, label: t.name })))
const shiftLocationOptions = computed(() => shiftLocations.value.map(l => ({ value: l.id, label: l.name })))

const shiftTypeMap = computed(() => Object.fromEntries(shiftTypes.value.map(t => [t.id, t])))
const locationMap = computed(() => Object.fromEntries(shiftLocations.value.map(l => [l.id, l.name])))

const columns = [
  { key: 'employee_id',    label: 'Employee'    },
  { key: 'shift_type_id',  label: 'Shift Type'  },
  { key: 'shift_location_id', label: 'Location' },
  { key: 'effective_from', label: 'Start Date'  },
  { key: 'effective_to',   label: 'End Date'    },
  { key: 'is_active',      label: 'Status'      },
]

async function load() {
  loading.value = true
  try {
    const [assignments, types, locations] = await Promise.all([
      listShiftAssignments(), listShiftTypes(), listShiftLocations()
    ])
    rows.value = assignments
    shiftTypes.value = types
    shiftLocations.value = locations
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
    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur()
    }
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return; deleting.value = true
  try { await deleteShiftAssignment(deleteTarget.value.id); deleteTarget.value = null; load() } catch {} finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-10">
    <PageHeader
      title="Shift Assignments"
      subtitle="Assign employees to shift types and locations"
      action-label="Assign Employee"
      @action="openCreate"
    />

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No shift assignments yet.">
      <template #cell-employee_id="{ value }">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-lg bg-slate-900 flex items-center justify-center text-[10px] font-black text-white shrink-0 shadow-sm">
            {{ value?.slice(0, 2).toUpperCase() }}
          </div>
          <span class="font-mono text-[11px] font-bold text-slate-500 uppercase tracking-tight">{{ value?.slice(0, 8) }}…</span>
        </div>
      </template>
      <template #cell-shift_type_id="{ value }">
        <div v-if="value && shiftTypeMap[value]" class="flex items-center gap-2.5">
          <div
            v-if="shiftTypeMap[value].color_code"
            :style="{ backgroundColor: shiftTypeMap[value].color_code }"
            class="w-2 h-2 rounded-full shrink-0"
          ></div>
          <span class="text-sm font-bold text-slate-900">{{ shiftTypeMap[value].name }}</span>
        </div>
        <span v-else class="text-slate-300 text-[10px] font-bold uppercase">—</span>
      </template>
      <template #cell-shift_location_id="{ value }">
        <span class="text-sm text-slate-700">{{ locationMap[value] ?? '—' }}</span>
      </template>
      <template #cell-is_active="{ value }">
        <span :class="['inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm', value ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-slate-50 text-slate-400 border-slate-100']">
          <CheckCircle2 v-if="value" class="w-3 h-3 mr-1.5" />
          <XCircle v-else class="w-3 h-3 mr-1.5" />
          {{ value ? 'Active' : 'Inactive' }}
        </span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <Button variant="ghost" size="icon" @click="openEdit(row)" class="h-9 w-9 rounded-xl text-slate-400 hover:text-slate-900 hover:bg-slate-100">
            <Pencil class="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" @click="deleteTarget = row" class="h-9 w-9 rounded-xl text-slate-400 hover:text-destructive hover:bg-destructive/10">
            <Trash2 class="w-4 h-4" />
          </Button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Shift Assignment' : 'New Shift Assignment'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6 py-4">
        <div class="bg-indigo-50/30 p-4 rounded-2xl flex items-start gap-3 border border-indigo-100/50">
          <Info class="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" />
          <p class="text-[11px] text-indigo-700 font-medium leading-relaxed">
            Search for an employee by name or ID. Overlapping assignments for the same employee should be avoided.
          </p>
        </div>

        <EntitySearchSelect
          :modelValue="form.employee_id ?? ''"
          @update:modelValue="form.employee_id = $event as string"
          label="Employee"
          entity="employee"
          placeholder="Search employee by name…"
          required
        />

        <div class="grid grid-cols-2 gap-4 bg-slate-50/50 p-5 rounded-2xl border border-slate-100">
          <FormSelect label="Shift Type" v-model="form.shift_type_id" :options="shiftTypeOptions" placeholder="— Select shift type —" />
          <FormSelect label="Location" v-model="form.shift_location_id" :options="shiftLocationOptions" placeholder="— Select location —" />
        </div>

        <div class="space-y-3">
          <div class="flex items-center gap-2">
            <CalendarClock class="w-4 h-4 text-slate-400" />
            <span class="text-[10px] font-black uppercase tracking-widest text-slate-700">Assignment Period</span>
          </div>
          <div class="grid grid-cols-2 gap-4 p-5 rounded-2xl border border-dashed border-slate-200">
            <FormInput label="Start Date" type="date" v-model="form.effective_from" required />
            <FormInput label="End Date" type="date" v-model="form.effective_to" placeholder="Open-ended" />
          </div>
        </div>

        <FormTextarea label="Notes" v-model="form.notes" placeholder="Any special notes for this assignment…" />
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-4 w-full">
          <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
          <div v-else />
          <div class="flex gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6 h-10">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800">
              {{ saving ? 'Saving…' : selected ? 'Update' : 'Assign' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Remove Shift Assignment?"
      message="Are you sure you want to remove this shift assignment?"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
