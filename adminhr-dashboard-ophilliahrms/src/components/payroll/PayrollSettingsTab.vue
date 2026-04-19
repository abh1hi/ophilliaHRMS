<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import FormInput from '@/components/ui/FormInput.vue'
import FormSelect from '@/components/ui/FormSelect.vue'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { 
  FileText, 
  Calculator, 
  Settings2, 
  Coins, 
  Save, 
  Plus, 
  Search, 
  ShieldCheck, 
  Building2,
  PieChart
} from 'lucide-vue-next'

const activeTab = ref('tax-profiles')

const selectedEmployee = ref('')
const selectedFinancialYear = ref(new Date().getFullYear())

const taxProfileForm = ref({
  tax_regime: 'new',
  investment_80c: 0,
  investment_80d: 0,
  hra_rent_paid: 0,
  is_metro_city: false,
  nps_voluntary: 0,
})

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

const saveTaxProfile = async () => {
  console.log('Saving tax profile:', taxProfileForm.value)
}

const saveStructure = async () => {
  console.log('Saving structure:', structureForm.value)
}

const fyOptions = [
  { value: 2024, label: 'FY 2024-25' },
  { value: 2025, label: 'FY 2025-26' },
  { value: 2026, label: 'FY 2026-27' },
]

const taxRegimeOptions = [
  { value: 'new', label: 'New Tax Regime (Default)' },
  { value: 'old', label: 'Old Tax Regime' },
]
</script>

<template>
  <div class="space-y-8 max-w-5xl">
    <Tabs defaultValue="tax-profiles" class="w-full" @update:modelValue="activeTab = $event">
      <div class="flex items-center justify-between mb-8 overflow-x-auto pb-2">
        <TabsList class="bg-muted/50 p-1 rounded-2xl border border-white/10 h-12">
          <TabsTrigger value="tax-profiles" class="rounded-xl px-6 data-[state=active]:bg-white data-[state=active]:shadow-sm">
            <ShieldCheck class="w-4 h-4 mr-2" /> Tax Profiles
          </TabsTrigger>
          <TabsTrigger value="salary-structures" class="rounded-xl px-6 data-[state=active]:bg-white data-[state=active]:shadow-sm">
            <Coins class="w-4 h-4 mr-2" /> Salary Structures
          </TabsTrigger>
        </TabsList>

        <div v-if="activeTab === 'salary-structures'">
          <Button @click="structureForm = { name: '', description: '', basic_pct: 50, hra_pct: 20, allowances_pct: 30, pf_pct: 12, esi_pct: 0.75, professional_tax: 200 }" size="sm" class="rounded-full bg-slate-900 text-white">
            <Plus class="w-4 h-4 mr-2" /> Create Structure
          </Button>
        </div>
      </div>

      <!-- Tax Profiles Tab -->
      <TabsContent value="tax-profiles" class="space-y-10 animate-in fade-in slide-in-from-bottom-2 duration-500">
        <div class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-8 shadow-sm">
          <div class="flex items-center gap-2 mb-6 text-slate-900 dark:text-slate-50">
            <Search class="w-4 h-4 text-muted-foreground" />
            <h3 class="text-xs font-bold uppercase tracking-widest">Employee Selection</h3>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <FormSelect 
              v-model="selectedEmployee" 
              label="Select Employee Profile" 
              :options="[{ value: '', label: 'Search employee...' }]" 
            />
            <FormSelect 
              v-model="selectedFinancialYear" 
              label="Financial Year Assessment" 
              :options="fyOptions" 
            />
          </div>
        </div>

        <div v-if="selectedEmployee" class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-10 shadow-sm animate-in zoom-in-95">
          <div class="flex items-center justify-between mb-10">
            <div class="flex items-center gap-3">
              <div class="h-10 w-10 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center">
                 <FileText class="w-5 h-5 text-indigo-600" />
              </div>
              <h3 class="text-lg font-black text-slate-900 tracking-tight">Tax Declaration Details</h3>
            </div>
            <Button @click="saveTaxProfile" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800 shadow-lg shadow-slate-200">
               <Save class="w-4 h-4 mr-2" /> Sync Profile
            </Button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-8">
            <div class="space-y-6">
               <FormSelect 
                v-model="taxProfileForm.tax_regime" 
                label="Selected Regime" 
                :options="taxRegimeOptions"
              />

              <div class="flex items-center space-x-2 bg-muted/30 p-5 rounded-3xl border border-dashed">
                <Checkbox id="metro-city" :checked="taxProfileForm.is_metro_city" @update:checked="taxProfileForm.is_metro_city = $event" />
                <div class="grid gap-1.5 leading-none">
                  <Label for="metro-city" class="text-[11px] font-bold uppercase tracking-wider text-slate-900 cursor-pointer">Metro City Residence</Label>
                  <p class="text-[10px] text-muted-foreground">Adjusts HRA exemption limit to 50% of basic.</p>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 bg-slate-50/50 p-8 rounded-[32px] border border-white/10">
               <FormInput v-model.number="taxProfileForm.investment_80c" label="80C (Life Ins, PPF)" type="number" placeholder="₹ Amount" />
               <FormInput v-model.number="taxProfileForm.investment_80d" label="80D (Health Ins)" type="number" placeholder="₹ Amount" />
               <FormInput v-model.number="taxProfileForm.hra_rent_paid" label="Monthly Rent Paid" type="number" placeholder="₹ Amount" />
               <FormInput v-model.number="taxProfileForm.nps_voluntary" label="NPS (80CCC)" type="number" placeholder="₹ Amount" />
            </div>
          </div>
        </div>

        <div v-else class="flex flex-col items-center justify-center py-20 bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl border border-dashed border-white/20 rounded-[40px]">
          <div class="h-20 w-20 rounded-full bg-slate-50 flex items-center justify-center mb-6">
            <ShieldCheck class="w-10 h-10 text-slate-200" />
          </div>
          <p class="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground italic">Identify employee record to begin taxation assessment</p>
        </div>
      </TabsContent>

      <!-- Salary Structures Tab -->
      <TabsContent value="salary-structures" class="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
        <div class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-10 shadow-sm">
          <div class="flex items-center justify-between mb-10">
            <div class="flex items-center gap-3">
              <div class="h-10 w-10 rounded-2xl bg-amber-50 border border-amber-100 flex items-center justify-center">
                 <Settings2 class="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <h3 class="text-lg font-black text-slate-900 tracking-tight">Configuration Engine</h3>
                <p class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Define percentage breakdown of total CTC</p>
              </div>
            </div>
            <Button @click="saveStructure" class="rounded-full px-10 bg-slate-900 text-white hover:bg-slate-800 shadow-lg shadow-slate-200">
               <Save class="w-4 h-4 mr-2" /> Save Architecture
            </Button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
            <div class="space-y-8">
              <div class="grid grid-cols-1 gap-6">
                <FormInput v-model="structureForm.name" label="Component ID" placeholder="e.g. Standard Corporate v2" />
                <FormInput v-model="structureForm.description" label="System Description" placeholder="Internal remarks..." />
              </div>

              <div class="p-6 rounded-3xl bg-indigo-50/30 border border-indigo-100/50 space-y-4">
                 <div class="flex items-center gap-2">
                    <PieChart class="w-3.5 h-3.5 text-indigo-600" />
                    <span class="text-[10px] font-black text-indigo-600 uppercase tracking-widest">Taxation Pillars</span>
                 </div>
                 <div class="grid grid-cols-2 gap-4">
                    <FormInput v-model.number="structureForm.professional_tax" label="Professional Tax (₹)" type="number" />
                    <FormInput v-model.number="structureForm.basic_pct" label="Basic Pay (%)" type="number" />
                 </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-6 p-8 rounded-[40px] bg-slate-50/50 border border-white/10 h-fit">
              <FormInput v-model.number="structureForm.hra_pct" label="HRA (%)" type="number" />
              <FormInput v-model.number="structureForm.allowances_pct" label="Special Allw. (%)" type="number" />
              <FormInput v-model.number="structureForm.pf_pct" label="Provident Fund (%)" type="number" />
              <FormInput v-model.number="structureForm.esi_pct" label="ESI (%)" type="number" step="0.01" />
              
              <div class="col-span-2 mt-4 p-4 bg-white/60 rounded-2xl border border-dashed flex items-center justify-between">
                <div class="flex items-center gap-2">
                   <Building2 class="w-4 h-4 text-slate-400" />
                   <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Defined</span>
                </div>
                <span class="text-lg font-black text-slate-900">{{ structureForm.basic_pct + structureForm.hra_pct + structureForm.allowances_pct }}%</span>
              </div>
            </div>
          </div>
        </div>
      </TabsContent>
    </Tabs>
  </div>
</template>
