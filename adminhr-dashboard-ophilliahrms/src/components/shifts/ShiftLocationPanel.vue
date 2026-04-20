<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import FieldHint from '../ui/FieldHint.vue'
import MapLocationPicker from '../ui/MapLocationPicker.vue'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import {
  Pencil,
  Trash2,
  MapPin,
  Map,
  CheckCircle2,
  XCircle,
  List,
} from 'lucide-vue-next'
import { listShiftLocations, createShiftLocation, updateShiftLocation, deleteShiftLocation } from '../../services/shift-location.service'
import type { ShiftLocation } from '../../services/shift-location.service'

const rows = ref<ShiftLocation[]>([]); const loading = ref(false)
const modalOpen = ref(false)
const form = ref<Partial<ShiftLocation>>({})
const selected = ref<ShiftLocation | null>(null)
const deleteTarget = ref<ShiftLocation | null>(null)
const saving = ref(false); const deleting = ref(false); const errorMsg = ref('')
const activeView = ref<'list' | 'map'>('list')

const columns = [
  { key: 'name',          label: 'Location Name' },
  { key: 'address',       label: 'Address' },
  { key: 'radius_meters', label: 'Radius (m)' },
  { key: 'is_active',     label: 'Status' },
]

async function load() { loading.value = true; try { rows.value = await listShiftLocations() } catch {} finally { loading.value = false } }
onMounted(load)

function openCreate() {
  selected.value = null
  form.value = { latitude: 20.5937, longitude: 78.9629, radius_meters: 100 }
  errorMsg.value = ''
  modalOpen.value = true
}

function openEdit(row: ShiftLocation) {
  selected.value = row
  form.value = { ...row }
  errorMsg.value = ''
  modalOpen.value = true
}

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateShiftLocation(selected.value.id, form.value)
    else await createShiftLocation(form.value)
    modalOpen.value = false; load()
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
      title="Shift Locations"
      subtitle="Define geofenced zones for location-based attendance check-in"
      action-label="Add Location"
      @action="openCreate"
    />

    <!-- View toggle -->
    <div class="flex items-center gap-2">
      <Button
        :variant="activeView === 'list' ? 'default' : 'outline'"
        size="sm"
        @click="activeView = 'list'"
        class="rounded-full px-4 h-8 text-xs font-bold"
      >
        <List class="w-3.5 h-3.5 mr-1.5" /> List
      </Button>
      <Button
        :variant="activeView === 'map' ? 'default' : 'outline'"
        size="sm"
        @click="activeView = 'map'"
        class="rounded-full px-4 h-8 text-xs font-bold"
      >
        <Map class="w-3.5 h-3.5 mr-1.5" /> Map View
      </Button>
    </div>

    <!-- List View -->
    <DataTable v-if="activeView === 'list'" :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No shift locations yet. Add your first location.">
      <template #cell-name="{ value }">
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-xl bg-slate-100 flex items-center justify-center border border-white/40 shadow-sm shrink-0">
            <MapPin class="w-4 h-4 text-slate-500" />
          </div>
          <span class="font-bold text-slate-900">{{ value }}</span>
        </div>
      </template>
      <template #cell-address="{ value }">
        <span class="text-slate-500 text-[11px] font-medium max-w-xs truncate">{{ value || '—' }}</span>
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

    <!-- Map View (all locations) -->
    <div v-else class="rounded-[28px] border border-slate-200 overflow-hidden">
      <MapLocationPicker
        v-if="rows.length"
        :lat="rows[0].latitude || 20.5937"
        :lng="rows[0].longitude || 78.9629"
        :radius="rows[0].radius_meters || 100"
        @update:lat="() => {}"
        @update:lng="() => {}"
        @update:radius="() => {}"
      />
      <div v-else class="flex flex-col items-center justify-center py-16 text-slate-400">
        <MapPin class="w-10 h-10 mb-3 text-slate-200" />
        <p class="text-sm font-medium">No locations to display. Add your first location.</p>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <Dialog :open="modalOpen" @update:open="modalOpen = $event">
      <DialogContent class="max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{{ selected ? 'Edit Location' : 'Add Shift Location' }}</DialogTitle>
        </DialogHeader>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 py-4">
          <!-- Left: Map -->
          <div>
            <MapLocationPicker
              :lat="form.latitude ?? 20.5937"
              :lng="form.longitude ?? 78.9629"
              :radius="form.radius_meters ?? 100"
              @update:lat="form.latitude = $event"
              @update:lng="form.longitude = $event"
              @update:radius="form.radius_meters = $event"
            />
          </div>

          <!-- Right: Form -->
          <div class="space-y-5">
            <FormInput label="Location Name" v-model="form.name" required placeholder="e.g. Head Office, Warehouse A" />
            <FormTextarea label="Address" v-model="form.address" placeholder="Full address or entrance details…" />

            <div class="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-2xl border border-slate-200">
              <div>
                <div class="flex items-center gap-1 mb-1">
                  <span class="text-sm font-medium text-slate-700">Latitude</span>
                  <FieldHint text="Auto-filled from map. You don't need to edit manually — drag the marker or click on the map." />
                </div>
                <input
                  type="number"
                  :value="form.latitude"
                  @input="form.latitude = parseFloat(($event.target as HTMLInputElement).value)"
                  placeholder="e.g. 28.6139"
                  class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>
              <div>
                <div class="flex items-center gap-1 mb-1">
                  <span class="text-sm font-medium text-slate-700">Longitude</span>
                  <FieldHint text="Auto-filled from map. You don't need to edit manually — drag the marker or click on the map." />
                </div>
                <input
                  type="number"
                  :value="form.longitude"
                  @input="form.longitude = parseFloat(($event.target as HTMLInputElement).value)"
                  placeholder="e.g. 77.2090"
                  class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>
            </div>

            <div class="flex items-center gap-3">
              <input
                type="checkbox"
                id="loc-active"
                :checked="form.is_active !== false"
                @change="form.is_active = ($event.target as HTMLInputElement).checked"
                class="w-4 h-4 rounded border-slate-300"
              />
              <label for="loc-active" class="text-sm font-medium text-slate-700 cursor-pointer">Active (available for check-in)</label>
            </div>
          </div>
        </div>

        <DialogFooter>
          <p v-if="errorMsg" class="text-xs text-destructive font-medium mr-auto">{{ errorMsg }}</p>
          <Button variant="outline" @click="modalOpen = false" class="rounded-full px-6">Cancel</Button>
          <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
            {{ saving ? 'Saving…' : selected ? 'Update Location' : 'Save Location' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Location?"
      :message="`Remove '${deleteTarget?.name}'? Employees assigned to this location will need to be reassigned.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
