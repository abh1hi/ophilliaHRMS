<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Button } from '@/components/ui/button'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import FormInput from '@/components/ui/FormInput.vue'
import FormSelect from '@/components/ui/FormSelect.vue'
import DataTable from '@/components/ui/DataTable.vue'
import SlideDrawer from '@/components/ui/SlideDrawer.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import {
  FileText,
  Settings2,
  Coins,
  Save,
  Plus,
  Search,
  ShieldCheck,
  Building2,
  PieChart,
  Pencil,
  Trash2,
} from 'lucide-vue-next'
import { payrollService } from '@/services/payroll.service'

// ── Salary Structures ────────────────────────────────────────────────────────

const structures = ref<any[]>([])
const structuresLoading = ref(false)
const structureDrawerOpen = ref(false)
const selectedStructure = ref<any | null>(null)
const structureSaving = ref(false)
const structureError = ref('')
const deleteTarget = ref<any | null>(null)
const deleting = ref(false)

const structureForm = ref({
  name: '',
  description: '',
  basic_pct: 50,
  hra_pct: 20,
  allowances_pct: 30,
  pf_pct: 12,
  esi_pct: 0.75,
  professional_tax: 200,
})

const structureColumns = [
  { key: 'name',           label: 'Name'           },
  { key: 'basic_pct',      label: 'Basic %'        },
  { key: 'hra_pct',        label: 'HRA %'          },
  { key: 'allowances_pct', label: 'Allowances %'   },
  { key: 'pf_pct',         label: 'PF %'           },
  { key: 'esi_pct',        label: 'ESI %'          },
]

async function loadStructures() {
  structuresLoading.value = true
  try {
    const res = await payrollService.getSalaryStructures()
    structures.value = res.data ?? res ?? []
  } catch {} finally { structuresLoading.value = false }
}

function openCreateStructure() {
  selectedStructure.value = null
  structureForm.value = { name: '', description: '', basic_pct: 50, hra_pct: 20, allowances_pct: 30, pf_pct: 12, esi_pct: 0.75, professional_tax: 200 }
  structureError.value = ''
  structureDrawerOpen.value = true
}

function openEditStructure(row: any) {
  selectedStructure.value = row
  structureForm.value = { ...row }
  structureError.value = ''
  structureDrawerOpen.value = true
}

async function saveStructure() {
  structureSaving.value = true; structureError.value = ''
  try {
    if (selectedStructure.value) {
      await payrollService.updateSalaryStructure(selectedStructure.value.id, structureForm.value)
    } else {
      await payrollService.createSalaryStructure(structureForm.value)
    }
    structureDrawerOpen.value = false
    loadStructures()
  } catch (e: any) { structureError.value = e.message } finally { structureSaving.value = false }
}

async function confirmDeleteStructure() {
  if (!deleteTarget.value) return
  deleting.value = true
  try { await payrollService.deleteSalaryStructure(deleteTarget.value.id); deleteTarget.value = null; loadStructures() }
  catch {} finally { deleting.value = false }
}

// ── Tax Profiles ─────────────────────────────────────────────────────────────

const selectedEmployee = ref('')
const selectedFinancialYear = ref(new Date().getFullYear())
const taxProfileLoaded = ref(false)
const taxProfileLoading = ref(false)
const taxProfileSaving = ref(false)
const taxProfileError = ref('')

const taxProfileForm = ref({
  tax_regime: 'new',
  investment_80c: 0,
  investment_80d: 0,
  hra_rent_paid: 0,
  is_metro_city: false,
  nps_voluntary: 0,
})

const fyOptions = [
  { value: 2024, label: 'FY 2024-25' },
  { value: 2025, label: 'FY 2025-26' },
  { value: 2026, label: 'FY 2026-27' },
]

const taxRegimeOptions = [
  { value: 'new', label: 'New Tax Regime (Default)' },
  { value: 'old', label: 'Old Tax Regime' },
]

async function loadTaxProfile() {
  if (!selectedEmployee.value) return
  taxProfileLoading.value = true; taxProfileLoaded.value = false
  try {
    const res = await payrollService.getTaxProfile(selectedEmployee.value, selectedFinancialYear.value)
    const data = res.data ?? res
    if (data) {
      taxProfileForm.value = { ...taxProfileForm.value, ...data }
      taxProfileLoaded.value = true
    }
  } catch {
    taxProfileLoaded.value = true
  } finally { taxProfileLoading.value = false }
}

async function saveTaxProfile() {
  taxProfileSaving.value = true; taxProfileError.value = ''
  try {
    await payrollService.updateTaxProfile(selectedEmployee.value, selectedFinancialYear.value, taxProfileForm.value)
  } catch (e: any) { taxProfileError.value = e.message } finally { taxProfileSaving.value = false }
}

onMounted(loadStructures)
</script>

<template>
  <div class="space-y-8 max-w-5xl">
    <Tabs defaultValue="salary-structures" class="w-full">
      <div class="flex items-center justify-between mb-8 overflow-x-auto pb-2">
        <TabsList class="bg-muted/50 p-1 rounded-2xl border border-white/10 h-12">
          <TabsTrigger value="salary-structures" class="rounded-xl px-6 data-[state=active]:bg-white data-[state=active]:shadow-sm">
            <Coins class="w-4 h-4 mr-2" /> Salary Structures
          </TabsTrigger>
          <TabsTrigger value="tax-profiles" class="rounded-xl px-6 data-[state=active]:bg-white data-[state=active]:shadow-sm">
            <ShieldCheck class="w-4 h-4 mr-2" /> Tax Profiles
          </TabsTrigger>
        </TabsList>
      </div>

      <!-- Salary Structures Tab -->
      <TabsContent value="salary-structures" class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-sm font-bold text-slate-900">Salary Structures</h3>
            <p class="text-xs text-slate-500 mt-0.5">Define CTC component percentages for payroll calculation</p>
          </div>
          <Button @click="openCreateStructure" class="rounded-xl bg-slate-900 text-white h-9 text-[11px] font-bold uppercase tracking-widest px-5">
            <Plus class="w-4 h-4 mr-2" /> New Structure
          </Button>
        </div>

        <DataTable :columns="structureColumns" :rows="structures" :loading="structuresLoading" empty-text="No salary structures yet. Create one to assign to employees.">
          <template #cell-basic_pct="{ value }"><span class="font-mono text-xs">{{ value }}%</span></template>
          <template #cell-hra_pct="{ value }"><span class="font-mono text-xs">{{ value }}%</span></template>
          <template #cell-allowances_pct="{ value }"><span class="font-mono text-xs">{{ value }}%</span></template>
          <template #cell-pf_pct="{ value }"><span class="font-mono text-xs">{{ value }}%</span></template>
          <template #cell-esi_pct="{ value }"><span class="font-mono text-xs">{{ value }}%</span></template>
          <template #actions="{ row }">
            <div class="flex items-center justify-end gap-1">
              <Button variant="ghost" size="icon" @click="openEditStructure(row)" class="h-8 w-8 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-900">
                <Pencil class="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="icon" @click="deleteTarget = row" class="h-8 w-8 rounded-lg hover:bg-rose-50 text-slate-400 hover:text-rose-600">
                <Trash2 class="w-4 h-4" />
              </Button>
            </div>
          </template>
        </DataTable>

        <!-- Create / Edit drawer -->
        <SlideDrawer :open="structureDrawerOpen" :title="selectedStructure ? 'Edit Salary Structure' : 'New Salary Structure'" width="w-full max-w-xl" @close="structureDrawerOpen = false">
          <div class="space-y-6 py-2">
            <FormInput v-model="structureForm.name" label="Structure Name" placeholder="e.g. Standard CTC, Senior Band" required />
            <FormInput v-model="structureForm.description" label="Description" placeholder="Internal notes…" />

            <div class="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-4">
              <p class="text-[10px] font-black uppercase tracking-widest text-slate-500">Component Percentages (of CTC)</p>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <FormInput v-model.number="structureForm.basic_pct" label="Basic %" type="number" />
                  <p class="text-[10px] text-slate-400 mt-1">Drives PF and HRA calculations</p>
                </div>
                <div>
                  <FormInput v-model.number="structureForm.hra_pct" label="HRA %" type="number" />
                  <p class="text-[10px] text-slate-400 mt-1">% of basic salary</p>
                </div>
                <FormInput v-model.number="structureForm.allowances_pct" label="Allowances %" type="number" />
                <FormInput v-model.number="structureForm.pf_pct" label="PF %" type="number" />
                <FormInput v-model.number="structureForm.esi_pct" label="ESI %" type="number" step="0.01" />
                <FormInput v-model.number="structureForm.professional_tax" label="Professional Tax (₹/mo)" type="number" />
              </div>

              <div class="flex items-center justify-between pt-2 border-t border-slate-200">
                <div class="flex items-center gap-2">
                  <Building2 class="w-4 h-4 text-slate-400" />
                  <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Defined</span>
                </div>
                <span :class="['text-lg font-black', (structureForm.basic_pct + structureForm.hra_pct + structureForm.allowances_pct) > 100 ? 'text-rose-600' : 'text-slate-900']">
                  {{ structureForm.basic_pct + structureForm.hra_pct + structureForm.allowances_pct }}%
                </span>
              </div>
            </div>
          </div>

          <template #footer>
            <div class="flex items-center justify-between w-full">
              <p v-if="structureError" class="text-xs text-destructive font-medium">{{ structureError }}</p>
              <div v-else />
              <div class="flex gap-3">
                <Button variant="outline" @click="structureDrawerOpen = false" class="rounded-full px-6">Cancel</Button>
                <Button @click="saveStructure" :disabled="structureSaving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
                  {{ structureSaving ? 'Saving…' : selectedStructure ? 'Update' : 'Create' }}
                </Button>
              </div>
            </div>
          </template>
        </SlideDrawer>

        <ConfirmDialog
          :open="!!deleteTarget"
          title="Delete Salary Structure?"
          :message="`Remove '${deleteTarget?.name}'? Employees assigned to this structure will need to be reassigned.`"
          :loading="deleting"
          @confirm="confirmDeleteStructure"
          @cancel="deleteTarget = null"
        />
      </TabsContent>

      <!-- Tax Profiles Tab -->
      <TabsContent value="tax-profiles" class="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
        <div class="bg-white/40 backdrop-blur-xl rounded-[28px] border border-white/20 p-8 shadow-sm">
          <div class="flex items-center gap-2 mb-6 text-slate-900">
            <Search class="w-4 h-4 text-muted-foreground" />
            <h3 class="text-xs font-bold uppercase tracking-widest">Select Employee</h3>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <FormInput
              v-model="selectedEmployee"
              label="Employee ID"
              placeholder="Paste employee UUID"
            />
            <FormSelect
              v-model="selectedFinancialYear"
              label="Financial Year"
              :options="fyOptions"
            />
            <Button @click="loadTaxProfile" :disabled="!selectedEmployee || taxProfileLoading" class="rounded-xl h-10 bg-slate-900 text-white text-xs font-bold uppercase tracking-widest">
              {{ taxProfileLoading ? 'Loading…' : 'Load Profile' }}
            </Button>
          </div>
        </div>

        <div v-if="taxProfileLoaded" class="bg-white/40 backdrop-blur-xl rounded-[28px] border border-white/20 p-10 shadow-sm animate-in zoom-in-95">
          <div class="flex items-center justify-between mb-8">
            <div class="flex items-center gap-3">
              <div class="h-10 w-10 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center">
                <FileText class="w-5 h-5 text-indigo-600" />
              </div>
              <h3 class="text-base font-bold text-slate-900">Tax Declaration</h3>
            </div>
            <Button @click="saveTaxProfile" :disabled="taxProfileSaving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
              <Save class="w-4 h-4 mr-2" /> {{ taxProfileSaving ? 'Saving…' : 'Save Profile' }}
            </Button>
          </div>

          <p v-if="taxProfileError" class="text-xs text-destructive font-medium mb-4">{{ taxProfileError }}</p>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-6">
            <div class="space-y-6">
              <FormSelect v-model="taxProfileForm.tax_regime" label="Tax Regime" :options="taxRegimeOptions" />
              <div class="flex items-center space-x-3 bg-muted/30 p-4 rounded-2xl border border-dashed">
                <Checkbox id="metro-city" :checked="taxProfileForm.is_metro_city" @update:checked="taxProfileForm.is_metro_city = $event" />
                <div>
                  <Label for="metro-city" class="text-[11px] font-bold uppercase tracking-wider text-slate-900 cursor-pointer">Metro City Residence</Label>
                  <p class="text-[10px] text-muted-foreground">Adjusts HRA exemption limit to 50% of basic.</p>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4 bg-slate-50/50 p-6 rounded-2xl border">
              <FormInput v-model.number="taxProfileForm.investment_80c" label="80C (Life Ins, PPF)" type="number" placeholder="₹ Amount" />
              <FormInput v-model.number="taxProfileForm.investment_80d" label="80D (Health Ins)" type="number" placeholder="₹ Amount" />
              <FormInput v-model.number="taxProfileForm.hra_rent_paid" label="Monthly Rent Paid" type="number" placeholder="₹ Amount" />
              <FormInput v-model.number="taxProfileForm.nps_voluntary" label="NPS (80CCC)" type="number" placeholder="₹ Amount" />
            </div>
          </div>
        </div>

        <div v-else class="flex flex-col items-center justify-center py-20 bg-white/40 backdrop-blur-xl border border-dashed border-white/20 rounded-[40px]">
          <div class="h-16 w-16 rounded-full bg-slate-50 flex items-center justify-center mb-4">
            <ShieldCheck class="w-8 h-8 text-slate-200" />
          </div>
          <p class="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground">Enter an employee ID and click Load Profile</p>
        </div>
      </TabsContent>
    </Tabs>
  </div>
</template>
