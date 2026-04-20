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
  CalendarClock,
  Calendar,
  CheckCircle2,
  XCircle,
  Layers,
  Clock,
} from 'lucide-vue-next'
import { listShiftSchedules, createShiftSchedule, updateShiftSchedule, deleteShiftSchedule } from '../../services/shift-schedule.service'
import type { ShiftSchedule } from '../../services/shift-schedule.service'

const rows = ref<ShiftSchedule[]>([]); const loading = ref(false)
const drawerOpen = ref(false); const form = ref<Partial<ShiftSchedule>>({})
const selected = ref<ShiftSchedule | null>(null); const deleteTarget = ref<ShiftSchedule | null>(null)
const saving = ref(false); const deleting = ref(false); const errorMsg = ref('')

const columns = [
  { key: 'name',           label: 'Schedule Name' },
  { key: 'effective_from', label: 'Start Date'    },
  { key: 'effective_to',   label: 'End Date'      },
  { key: 'is_active',      label: 'Status'        },
]

async function load() { loading.value = true; try { rows.value = await listShiftSchedules() } catch {} finally { loading.value = false } }
onMounted(load)

function openCreate() { selected.value = null; form.value = {}; errorMsg.value = ''; drawerOpen.value = true }
function openEdit(row: ShiftSchedule) { selected.value = row; form.value = { ...row }; errorMsg.value = ''; drawerOpen.value = true }

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateShiftSchedule(selected.value.id, form.value)
    else await createShiftSchedule(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return; deleting.value = true
  try { await deleteShiftSchedule(deleteTarget.value.id); deleteTarget.value = null; load() } catch {} finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-10">
    <PageHeader
      title="Shift Schedules"
      subtitle="Define and manage recurring shift rotation patterns"
      action-label="New Schedule"
      @action="openCreate"
    />

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No shift schedules yet.">
      <template #cell-name="{ value }">
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-xl bg-slate-100 flex items-center justify-center border border-white/40 shadow-sm shrink-0">
            <Layers class="w-4 h-4 text-slate-500" />
          </div>
          <span class="font-bold text-slate-900">{{ value }}</span>
        </div>
      </template>
      <template #cell-effective_from="{ value }">
        <div class="flex items-center gap-2">
          <Calendar class="w-3.5 h-3.5 text-slate-300" />
          <span class="text-slate-600 text-[11px] font-bold">{{ value || '—' }}</span>
        </div>
      </template>
      <template #cell-effective_to="{ value }">
        <div class="flex items-center gap-2">
          <Clock class="w-3.5 h-3.5 text-slate-300" />
          <span class="text-slate-600 text-[11px] font-bold">{{ value || 'Open-ended' }}</span>
        </div>
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

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Schedule' : 'New Shift Schedule'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6 py-4">
        <FormInput label="Schedule Name" v-model="form.name" required placeholder="e.g. Standard 3-Week Rotation" />
        <FormTextarea label="Description" v-model="form.description" placeholder="Describe the rotation logic or any special rules…" />

        <div class="space-y-3">
          <div class="flex items-center gap-2">
            <CalendarClock class="w-4 h-4 text-slate-400" />
            <span class="text-[10px] font-black uppercase tracking-widest text-slate-700">Validity Period</span>
          </div>
          <div class="grid grid-cols-2 gap-4 p-5 bg-slate-50/50 rounded-2xl border border-slate-100">
            <FormInput label="Start Date" type="date" v-model="form.effective_from" />
            <FormInput label="End Date" type="date" v-model="form.effective_to" />
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between gap-4 w-full">
          <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
          <div v-else />
          <div class="flex gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6 h-10">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800">
              {{ saving ? 'Saving…' : selected ? 'Update' : 'Create Schedule' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Shift Schedule?"
      :message="`Remove '${deleteTarget?.name}'? This cannot be undone.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
