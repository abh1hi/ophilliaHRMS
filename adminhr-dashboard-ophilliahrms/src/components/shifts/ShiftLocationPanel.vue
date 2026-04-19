<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { Button } from '@/components/ui/button'
import { 
  Pencil, 
  Trash2, 
  Plus, 
  MapPin, 
  Navigation, 
  CheckCircle2, 
  XCircle,
  Info,
  Map,
  Compass
} from 'lucide-vue-next'
import { listShiftLocations, createShiftLocation, updateShiftLocation, deleteShiftLocation } from '../../services/shift-location.service'
import type { ShiftLocation } from '../../services/shift-location.service'

const rows = ref<ShiftLocation[]>([]); const loading = ref(false)
const drawerOpen = ref(false); const form = ref<Partial<ShiftLocation>>({})
const selected = ref<ShiftLocation | null>(null); const deleteTarget = ref<ShiftLocation | null>(null)
const saving = ref(false); const deleting = ref(false); const errorMsg = ref('')

const columns = [
  { key: 'name',          label: 'Location Site' },
  { key: 'address',       label: 'Physical Address' },
  { key: 'radius_meters', label: 'Perimeter (m)'    },
  { key: 'is_active',     label: 'Status'        },
]

async function load() { loading.value = true; try { rows.value = await listShiftLocations() } catch {} finally { loading.value = false } }
onMounted(load)

function openCreate() { selected.value = null; form.value = { radius_meters: 100 }; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: ShiftLocation) { selected.value = row; form.value = { ...row }; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateShiftLocation(selected.value.id, form.value)
    else await createShiftLocation(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return; deleting.value = true
  try { await deleteShiftLocation(deleteTarget.value.id); deleteTarget.value = null; load() } catch {} finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-10">
    <PageHeader 
      title="Operational Hubs" 
      subtitle="Define geofenced zones for synchronized attendance tracking" 
      action-label="Sync Hub" 
      @action="openCreate" 
    />

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No operational hubs identified yet.">
      <template #cell-name="{ value }">
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-xl bg-slate-100 flex items-center justify-center border border-white/40 shadow-sm shrink-0">
             <MapPin class="w-4 h-4 text-slate-500" />
          </div>
          <span class="font-bold text-slate-900 group-hover:text-primary transition-colors">{{ value }}</span>
        </div>
      </template>
      <template #cell-address="{ value }">
        <div class="flex items-center gap-2">
           <Map class="w-3.5 h-3.5 text-slate-300" />
           <span class="text-slate-500 text-[11px] font-medium max-w-xs truncate">{{ value || 'N/A — Digital Presence Only' }}</span>
        </div>
      </template>
      <template #cell-is_active="{ value }">
        <span :class="['inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm', value ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-slate-50 text-slate-400 border-slate-100']">
          <CheckCircle2 v-if="value" class="w-3 h-3 mr-1.5" />
          <XCircle v-else class="w-3 h-3 mr-1.5" />
          {{ value ? 'Live' : 'Archived' }}
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

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Modify Hub Coordinates' : 'Deploy Operational Hub'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-8 py-4">
        <div class="bg-indigo-50/30 p-4 rounded-2xl flex items-start gap-3 border border-indigo-100/50 mb-2">
           <Info class="w-4 h-4 text-indigo-500 mt-0.5" />
           <p class="text-[11px] text-indigo-700 font-medium leading-relaxed">
             Geofencing ensures employees check-in only from authorized physical locations. Accuracy of coordinates is critical for synchronization.
           </p>
        </div>

        <FormInput label="Hub Designation" v-model="form.name" required placeholder="e.g. Headquarters North" />
        <FormTextarea label="Logistics Address" v-model="form.address" placeholder="Specify physical entrance or building details..." />
        
        <div class="grid grid-cols-2 gap-6 p-6 bg-slate-50/50 rounded-[32px] border border-white/10 relative overflow-hidden">
           <Compass class="absolute -right-4 -top-4 w-16 h-16 text-slate-900/5 rotate-12" />
           <FormInput label="Latitudinal Point" type="number" v-model.number="form.latitude" placeholder="e.g. 28.6139" />
           <FormInput label="Longitudinal Point" type="number" v-model.number="form.longitude" placeholder="e.g. 77.2090" />
        </div>

        <div class="flex items-center gap-6 p-6 rounded-3xl border border-dashed border-slate-200">
           <div class="h-12 w-12 rounded-2xl bg-slate-50 flex items-center justify-center shrink-0">
              <Navigation class="w-5 h-5 text-slate-400" />
           </div>
           <div class="flex-1">
              <FormInput label="Radial Perimeter (meters)" type="number" v-model.number="form.radius_meters" />
           </div>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-4">
          <div class="flex-1">
             <p v-if="errorMsg" class="text-[10px] font-bold text-destructive uppercase tracking-tight animate-in fade-in">{{ errorMsg }}</p>
          </div>
          <div class="flex gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 font-bold uppercase tracking-widest text-[11px]">
               {{ saving ? 'Syncing...' : 'Persist' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog 
      :open="!!deleteTarget" 
      title="Decommission Hub?" 
      :message="`Are you certain you want to remove '${deleteTarget?.name}' from the operational network?`" 
      :loading="deleting" 
      @confirm="confirmDelete" 
      @cancel="deleteTarget = null" 
    />
  </div>
</template>
