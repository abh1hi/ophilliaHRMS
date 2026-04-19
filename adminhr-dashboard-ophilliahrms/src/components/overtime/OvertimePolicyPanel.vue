<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import FormInput from '../ui/FormInput.vue'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Info, IndianRupee, Globe, Pencil, Trash2, CheckCircle2 } from 'lucide-vue-next'
import {
  listOvertimePolicies,
  createOvertimePolicy,
  createFromTemplate,
  updateOvertimePolicy,
  deleteOvertimePolicy,
} from '../../services/overtime-policy.service'
import type { OvertimePolicy } from '../../services/overtime-policy.service'

const rows = ref<OvertimePolicy[]>([])
const loading = ref(false)
const drawerOpen = ref(false)
const selected = ref<OvertimePolicy | null>(null)
const deleteTarget = ref<OvertimePolicy | null>(null)
const saving = ref(false)
const deleting = ref(false)
const errorMsg = ref('')

type Scope = 'company' | 'department' | 'employee'
const scopeType = ref<Scope>('company')

const form = ref<Partial<OvertimePolicy>>({
  jurisdiction: 'CUSTOM',
  daily_ot_threshold_hours: 8,
  weekly_ot_threshold_hours: 40,
  max_daily_hours: 12,
  daily_ot_multiplier: 1.5,
  weekly_ot_multiplier: 1.5,
  weekend_multiplier: 1.5,
  holiday_multiplier: 2.0,
  prefer_comp_off: false,
  comp_off_ratio: 1.0,
})

const columns = [
  { key: 'scope',                   label: 'Scope'           },
  { key: 'jurisdiction',            label: 'Jurisdiction'    },
  { key: 'daily_ot_threshold_hours', label: 'Daily Threshold' },
  { key: 'daily_ot_multiplier',     label: 'Daily Rate'      },
  { key: 'holiday_multiplier',      label: 'Holiday Rate'    },
  { key: 'prefer_comp_off',         label: 'Comp-off'        },
  { key: 'is_active',               label: 'Status'          },
]

function scopeLabel(row: OvertimePolicy): string {
  if (row.employee_id)   return `Employee`
  if (row.department_id) return `Department`
  if (row.location_id)   return `Location`
  return 'Company-wide'
}

async function load() {
  loading.value = true
  try { rows.value = await listOvertimePolicies() } catch {} finally { loading.value = false }
}

onMounted(load)

function openCreate() {
  selected.value = null
  scopeType.value = 'company'
  form.value = {
    jurisdiction: 'CUSTOM',
    daily_ot_threshold_hours: 8, weekly_ot_threshold_hours: 40, max_daily_hours: 12,
    daily_ot_multiplier: 1.5, weekly_ot_multiplier: 1.5,
    weekend_multiplier: 1.5, holiday_multiplier: 2.0,
    prefer_comp_off: false, comp_off_ratio: 1.0,
  }
  errorMsg.value = ''
  drawerOpen.value = true
}

function openEdit(row: OvertimePolicy) {
  selected.value = row
  form.value = { ...row }
  scopeType.value = row.employee_id ? 'employee' : row.department_id ? 'department' : 'company'
  errorMsg.value = ''
  drawerOpen.value = true
}

function applyTemplate(key: 'INDIA_FACTORIES_ACT' | 'EU_WTD_48H') {
  if (key === 'INDIA_FACTORIES_ACT') {
    Object.assign(form.value, {
      jurisdiction: 'INDIA', compliance_profile: 'INDIA_FACTORIES_ACT',
      daily_ot_threshold_hours: 9, weekly_ot_threshold_hours: 48, max_daily_hours: 12,
      daily_ot_multiplier: 2.0, weekly_ot_multiplier: 2.0, weekend_multiplier: 2.0,
      holiday_multiplier: 2.0, prefer_comp_off: false, comp_off_ratio: 1.0,
    })
  } else {
    Object.assign(form.value, {
      jurisdiction: 'EU', compliance_profile: 'EU_WTD_48H',
      daily_ot_threshold_hours: 10, weekly_ot_threshold_hours: 48, max_daily_hours: 13,
      daily_ot_multiplier: 1.25, weekly_ot_multiplier: 1.5, weekend_multiplier: 1.5,
      holiday_multiplier: 2.0, prefer_comp_off: true, comp_off_ratio: 1.5,
    })
  }
}

async function save() {
  saving.value = true; errorMsg.value = ''
  const payload = { ...form.value }
  if (scopeType.value !== 'employee')   delete payload.employee_id
  if (scopeType.value !== 'department') delete payload.department_id
  try {
    if (selected.value) await updateOvertimePolicy(selected.value.id, payload)
    else await createOvertimePolicy(payload)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function confirmDelete() {
  if (!deleteTarget.value) return; deleting.value = true
  try { await deleteOvertimePolicy(deleteTarget.value.id); deleteTarget.value = null; load() }
  catch {} finally { deleting.value = false }
}
</script>

<template>
  <div class="space-y-10">
    <PageHeader
      title="Overtime Policies"
      subtitle="Configure overtime thresholds, multipliers, and compliance rules"
      action-label="New Policy"
      @action="openCreate"
    />

    <div class="bg-amber-50/60 border border-amber-100 rounded-2xl p-4 flex items-start gap-3">
      <Info class="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
      <p class="text-xs text-amber-800 leading-relaxed">
        Overtime policies define when overtime begins and the pay multiplier applied. Use the
        <strong>India Factories Act</strong> template (2× daily OT after 9h) or the
        <strong>EU Working Time Directive</strong> template (1.25× after 10h) to pre-fill compliant
        settings.
      </p>
    </div>

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No overtime policies configured yet.">
      <template #cell-scope="{ row }">
        <span class="text-xs font-medium text-slate-600">{{ scopeLabel(row) }}</span>
      </template>
      <template #cell-jurisdiction="{ row }">
        <Badge variant="secondary" class="text-[10px]">{{ row.compliance_profile || row.jurisdiction }}</Badge>
      </template>
      <template #cell-daily_ot_threshold_hours="{ value }">
        <span class="text-sm text-slate-700">{{ value }}h</span>
      </template>
      <template #cell-daily_ot_multiplier="{ value }">
        <span class="font-semibold text-indigo-700">{{ value }}×</span>
      </template>
      <template #cell-holiday_multiplier="{ value }">
        <span class="font-semibold text-rose-600">{{ value }}×</span>
      </template>
      <template #cell-prefer_comp_off="{ value }">
        <span :class="['text-xs font-medium', value ? 'text-emerald-700' : 'text-slate-500']">
          {{ value ? 'Comp-off' : 'Cash' }}
        </span>
      </template>
      <template #cell-is_active="{ value }">
        <span :class="['inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold', value ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-50 text-slate-400']">
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

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit OT Policy' : 'New Overtime Policy'" width="w-full max-w-xl" @close="drawerOpen = false">
      <div class="space-y-6 py-4">

        <!-- Template quick-pick -->
        <div v-if="!selected" class="space-y-2">
          <Label class="text-xs font-bold uppercase tracking-widest text-slate-500">Quick-fill from compliance template</Label>
          <div class="grid grid-cols-2 gap-3">
            <button
              @click="applyTemplate('INDIA_FACTORIES_ACT')"
              class="p-4 rounded-2xl border-2 border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/30 transition-all text-left group"
            >
              <div class="flex items-center gap-2 mb-2">
                <IndianRupee class="w-4 h-4 text-indigo-600" />
                <span class="text-xs font-black uppercase tracking-widest text-slate-900">India Factories Act</span>
              </div>
              <p class="text-[10px] text-slate-500 leading-relaxed">2× OT after 9h/day · 48h/week · Cash payment required</p>
            </button>
            <button
              @click="applyTemplate('EU_WTD_48H')"
              class="p-4 rounded-2xl border-2 border-slate-200 hover:border-emerald-400 hover:bg-emerald-50/30 transition-all text-left group"
            >
              <div class="flex items-center gap-2 mb-2">
                <Globe class="w-4 h-4 text-emerald-600" />
                <span class="text-xs font-black uppercase tracking-widest text-slate-900">EU Working Time Directive</span>
              </div>
              <p class="text-[10px] text-slate-500 leading-relaxed">1.25× OT after 10h/day · 48h/week avg · Comp-off preferred</p>
            </button>
          </div>
        </div>

        <!-- Scope -->
        <div class="space-y-2">
          <Label class="text-xs font-bold uppercase tracking-widest text-slate-500">Applies To</Label>
          <div class="flex gap-2">
            <button
              v-for="s in [{ key: 'company', label: 'Company-wide' }, { key: 'department', label: 'Department' }, { key: 'employee', label: 'Employee' }]"
              :key="s.key"
              @click="scopeType = s.key as Scope"
              :class="['px-4 py-2 rounded-xl text-[11px] font-bold uppercase tracking-widest transition-all', scopeType === s.key ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200']"
            >{{ s.label }}</button>
          </div>
          <FormInput v-if="scopeType === 'department'" label="Department ID" v-model="form.department_id" placeholder="UUID" />
          <FormInput v-if="scopeType === 'employee'" label="Employee ID" v-model="form.employee_id" placeholder="UUID" />
        </div>

        <!-- Jurisdiction -->
        <div class="space-y-2">
          <Label class="text-xs font-bold uppercase tracking-widest text-slate-500">Jurisdiction</Label>
          <select v-model="form.jurisdiction" class="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900">
            <option value="INDIA">India</option>
            <option value="EU">European Union</option>
            <option value="CUSTOM">Custom</option>
          </select>
        </div>

        <!-- Thresholds -->
        <div class="space-y-2">
          <Label class="text-xs font-bold uppercase tracking-widest text-slate-500">Thresholds</Label>
          <div class="grid grid-cols-3 gap-4 p-4 bg-slate-50/50 rounded-2xl border">
            <FormInput label="Daily OT After (h)" type="number" v-model.number="form.daily_ot_threshold_hours" />
            <FormInput label="Weekly OT After (h)" type="number" v-model.number="form.weekly_ot_threshold_hours" />
            <FormInput label="Max Daily Hours" type="number" v-model.number="form.max_daily_hours" />
          </div>
        </div>

        <!-- Multipliers -->
        <div class="space-y-2">
          <Label class="text-xs font-bold uppercase tracking-widest text-slate-500">Pay Multipliers</Label>
          <div class="grid grid-cols-2 gap-4 p-4 bg-slate-50/50 rounded-2xl border">
            <FormInput label="Daily OT Rate (×)" type="number" step="0.25" v-model.number="form.daily_ot_multiplier" />
            <FormInput label="Weekly OT Rate (×)" type="number" step="0.25" v-model.number="form.weekly_ot_multiplier" />
            <FormInput label="Weekend Rate (×)" type="number" step="0.25" v-model.number="form.weekend_multiplier" />
            <FormInput label="Holiday Rate (×)" type="number" step="0.25" v-model.number="form.holiday_multiplier" />
          </div>
        </div>

        <!-- Comp-off -->
        <div class="flex items-center justify-between p-4 rounded-2xl border">
          <div>
            <p class="text-xs font-bold uppercase tracking-widest text-slate-900">Prefer Comp-off</p>
            <p class="text-[10px] text-slate-400 mt-0.5">Pay overtime as time off instead of cash</p>
          </div>
          <button
            @click="form.prefer_comp_off = !form.prefer_comp_off"
            :class="['w-12 h-6 rounded-full transition-colors', form.prefer_comp_off ? 'bg-emerald-500' : 'bg-slate-200']"
          >
            <div :class="['w-5 h-5 bg-white rounded-full shadow transition-transform mx-0.5', form.prefer_comp_off ? 'translate-x-6' : 'translate-x-0']" />
          </button>
        </div>
        <FormInput v-if="form.prefer_comp_off" label="Comp-off Ratio (h off per 1h OT)" type="number" step="0.25" v-model.number="form.comp_off_ratio" />
      </div>

      <template #footer>
        <div class="flex items-center justify-between gap-4">
          <p v-if="errorMsg" class="text-[10px] font-bold text-destructive uppercase tracking-tight">{{ errorMsg }}</p>
          <div class="flex gap-3 ml-auto">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800 shadow-xl font-bold uppercase tracking-widest text-[11px]">
              {{ saving ? 'Saving...' : 'Save Policy' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Delete OT Policy?"
      :message="`Remove this overtime policy? Existing records will not be affected.`"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>
