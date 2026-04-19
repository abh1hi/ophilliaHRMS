<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { Button } from '@/components/ui/button'
import { 
  Pencil, 
  Trash2, 
  Plus, 
  UserPlus, 
  Calendar, 
  MapPin, 
  CheckCircle2, 
  XCircle,
  Info,
  Clock,
  Briefcase,
  CalendarClock,
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

const shiftTypeOptions = computed(() => [
  { value: '', label: '— Unspecified —' },
  ...shiftTypes.value.map(t => ({ value: t.id, label: t.name })),
])
const shiftLocationOptions = computed(() => [
  { value: '', label: '— Unspecified —' },
  ...shiftLocations.value.map(l => ({ value: l.id, label: l.name })),
])

const shiftTypeMap = computed(() => Object.fromEntries(shiftTypes.value.map(t => [t.id, t])))

const columns = [
  { key: 'employee_id',    label: 'Resource'    },
  { key: 'shift_type_id',  label: 'Framework'   },
  { key: 'effective_from', label: 'Commence'    },
  { key: 'effective_to',   label: 'Conclude'    },
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
      title="Temporal Mapping" 
      subtitle="Synchronize personnel with operational shift frameworks" 
      action-label="Map Resource" 
      @action="openCreate" 
    />

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No active temporal mappings identified.">
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
             class="w-2 h-2 rounded-full shrink-0 shadow-[0_0_8px_rgba(0,0,0,0.1)]"
          ></div>
          <span class="text-sm font-bold text-slate-900 tracking-tight">{{ shiftTypeMap[value].name }}</span>
        </div>
        <span v-else class="text-slate-300 text-[10px] font-black uppercase tracking-widest italic">Unmapped</span>
      </template>
      <template #cell-is_active="{ value }">
        <span :class="['inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm', value ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-slate-50 text-slate-400 border-slate-100']">
          <CheckCircle2 v-if="value" class="w-3 h-3 mr-1.5" />
          <XCircle v-else class="w-3 h-3 mr-1.5" />
          {{ value ? 'Active' : 'Archived' }}
        </span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <Button variant="ghost" size="icon" @click="openEdit(row)" class="h-9 w-9 rounded-xl text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-all">
             <Pencil class="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" @click="deleteTarget = row" class="h-9 w-9 rounded-xl text-slate-400 hover:text-destructive hover:bg-destructive/10 transition-all">
             <Trash2 class="w-4 h-4" />
          </Button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Recalibrate Mapping' : 'Initialize Personal Frame'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-8 py-4">
        <div class="bg-indigo-50/30 p-4 rounded-2xl flex items-start gap-3 border border-indigo-100/50 mb-2">
           <Info class="w-4 h-4 text-indigo-500 mt-0.5" />
           <p class="text-[11px] text-indigo-700 font-medium leading-relaxed">
             Mappings define how personnel interact with shift architectures over time. Overlapping mappings for the same employee should be avoided.
           </p>
        </div>

        <FormInput label="Personnel Linkage (UUID)" v-model="form.employee_id" required placeholder="Paste Resource Hardware ID" />
        
        <div class="grid grid-cols-2 gap-6 bg-slate-50/50 p-6 rounded-[32px] border border-white/10">
           <FormSelect label="Operational Architecture" v-model="form.shift_type_id" :options="shiftTypeOptions" />
           <FormSelect label="Deployment Hub" v-model="form.shift_location_id" :options="shiftLocationOptions" />
        </div>

        <div class="space-y-4">
           <div class="flex items-center gap-2 mb-2">
              <CalendarClock class="w-4 h-4 text-slate-400" />
              <span class="text-[10px] font-black uppercase tracking-widest text-slate-900">Temporal Window</span>
           </div>
           <div class="grid grid-cols-2 gap-6 p-6 rounded-3xl border border-dashed border-slate-200">
             <FormInput label="Commence Date" type="date" v-model="form.effective_from" required />
             <FormInput label="Conclude Date" type="date" v-model="form.effective_to" placeholder="Open-ended" />
           </div>
        </div>

        <FormTextarea label="Mapping Context" v-model="form.notes" placeholder="Specify any unique constraints for this deployment..." />
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-4">
          <div class="flex-1">
             <p v-if="errorMsg" class="text-[10px] font-bold text-destructive uppercase tracking-tight animate-in fade-in">{{ errorMsg }}</p>
          </div>
          <div class="flex gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 font-bold uppercase tracking-widest text-[11px]">
              {{ saving ? 'Syncing...' : 'Deploy' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog 
      :open="!!deleteTarget" 
      title="De-synchronize Mapping?" 
      :message="`Are you certain you want to remove this temporal mapping from the system architecture?`" 
      :loading="deleting" 
      @confirm="confirmDelete" 
      @cancel="deleteTarget = null" 
    />
  </div>
</template>
