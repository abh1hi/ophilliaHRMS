<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import {
  Pencil,
  Trash2,
  Plus,
  Clock,
  Moon,
  Sun,
  Palette,
  Info,
  CheckCircle2,
  XCircle
} from 'lucide-vue-next'
import { listShiftTypes, createShiftType, updateShiftType, deleteShiftType } from '../../services/shift-type.service'
import type { ShiftType } from '../../services/shift-type.service'

const rows = ref<ShiftType[]>([]); const loading = ref(false)
const drawerOpen = ref(false); const form = ref<Partial<ShiftType>>({})
const selected = ref<ShiftType | null>(null); const deleteTarget = ref<ShiftType | null>(null)
const saving = ref(false); const deleting = ref(false); const errorMsg = ref('')

const columns = [
  { key: 'name',              label: 'Name'            },
  { key: 'start_time',        label: 'Start Time'      },
  { key: 'end_time',          label: 'End Time'        },
  { key: 'break_minutes',     label: 'Break (min)'     },
  { key: 'is_night_shift',    label: 'Night Shift'     },
  { key: 'is_active',         label: 'Status'          },
]

async function load() { loading.value = true; try { rows.value = await listShiftTypes() } catch {} finally { loading.value = false } }
onMounted(load)

function openCreate() {
  selected.value = null
  form.value = { break_minutes: 0, grace_period_minutes: 5, is_night_shift: false }
  errorMsg.value = ''
  drawerOpen.value = true
}
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
  <div class="space-y-10">
    <PageHeader
      title="Shift Types"
      subtitle="Define work shift patterns and schedules"
      action-label="New Shift Type"
      @action="openCreate"
    />

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No shift types created yet.">
      <template #cell-name="{ row, value }">
        <div class="flex items-center gap-3">
          <div
            v-if="row.color_code"
            :style="{ backgroundColor: row.color_code }"
            class="w-8 h-8 rounded-xl border border-white/20 shadow-sm shrink-0 flex items-center justify-center"
          >
            <Clock v-if="!row.is_night_shift" class="w-4 h-4 text-white/80" />
            <Moon v-else class="w-4 h-4 text-white/80" />
          </div>
          <span class="font-bold text-slate-900 group-hover:text-primary transition-colors">{{ value }}</span>
        </div>
      </template>
      <template #cell-is_night_shift="{ value }">
        <span :class="['inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm', value ? 'bg-indigo-50 text-indigo-700 border-indigo-100' : 'bg-amber-50 text-amber-700 border-amber-100']">
          <Moon v-if="value" class="w-3 h-3 mr-1.5" />
          <Sun v-else class="w-3 h-3 mr-1.5" />
          {{ value ? 'Night Shift' : 'Day Shift' }}
        </span>
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
          <Button variant="ghost" size="icon" @click="openEdit(row)" class="h-9 w-9 rounded-xl text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-all">
            <Pencil class="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" @click="deleteTarget = row" class="h-9 w-9 rounded-xl text-slate-400 hover:text-destructive hover:bg-destructive/10 transition-all">
            <Trash2 class="w-4 h-4" />
          </Button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Shift Type' : 'New Shift Type'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-8 py-4">
        <div class="bg-indigo-50/30 p-4 rounded-2xl flex items-start gap-3 border border-indigo-100/50 mb-2">
          <Info class="w-4 h-4 text-indigo-500 mt-0.5" />
          <p class="text-[11px] text-indigo-700 font-medium leading-relaxed">
            Define the timing for this shift. Work hours per day are used to calculate overtime thresholds automatically.
          </p>
        </div>

        <FormInput label="Shift Name" v-model="form.name" required placeholder="e.g. Morning, Night, Afternoon" />

        <div class="grid grid-cols-2 gap-6 p-6 bg-slate-50/50 rounded-3xl border border-white/10">
          <FormInput label="Start Time" type="time" v-model="form.start_time" required />
          <FormInput label="End Time" type="time" v-model="form.end_time" required />
        </div>

        <div class="grid grid-cols-2 gap-6">
          <FormInput label="Work Hours / Day" type="number" v-model.number="form.work_hours_per_day" placeholder="8" />
          <FormInput label="Break Duration (min)" type="number" v-model.number="form.break_minutes" />
        </div>

        <FormInput label="Grace Period (min)" type="number" v-model.number="form.grace_period_minutes" />

        <div class="flex items-center justify-between p-6 rounded-3xl border border-dashed hover:border-slate-300 transition-colors">
          <div class="flex items-center gap-4">
            <div class="relative group">
              <input
                type="color"
                :value="form.color_code || '#6366f1'"
                @input="form.color_code = ($event.target as HTMLInputElement).value"
                class="w-12 h-12 rounded-2xl border-2 border-white shadow-xl cursor-pointer"
              />
              <div class="absolute -top-1 -right-1 w-4 h-4 bg-white rounded-full flex items-center justify-center shadow-sm">
                <Palette class="w-2.5 h-2.5 text-slate-400" />
              </div>
            </div>
            <div>
              <Label class="text-xs font-bold uppercase tracking-widest text-slate-900">Colour Label</Label>
              <p class="text-[10px] text-muted-foreground mt-0.5">Shown in roster view</p>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <Checkbox
              id="night-shift-toggle"
              :checked="!!form.is_night_shift"
              @update:checked="form.is_night_shift = $event"
            />
            <Label for="night-shift-toggle" class="text-xs font-bold text-slate-700 cursor-pointer">Night Shift</Label>
          </div>
        </div>

        <FormTextarea label="Description" v-model="form.description" placeholder="Optional notes about this shift" />
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-4">
          <div class="flex-1">
            <p v-if="errorMsg" class="text-[10px] font-bold text-destructive uppercase tracking-tight animate-in fade-in">{{ errorMsg }}</p>
          </div>
          <div class="flex gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 font-bold uppercase tracking-widest text-[11px]">
              {{ saving ? 'Saving...' : 'Save' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete Shift Type?"
      :message="`Are you sure you want to delete the '${deleteTarget?.name}' shift type?`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
