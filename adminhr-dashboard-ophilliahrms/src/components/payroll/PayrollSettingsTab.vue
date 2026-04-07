<script setup lang="ts">
import { ref } from 'vue'

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
</script>

<template>
  <div class="space-y-6">
    <!-- Tab Navigation -->
    <div class="flex gap-4 border-b border-slate-200">
      <button
        @click="activeTab = 'tax-profiles'"
        :class="[
          'px-4 py-3 font-medium transition-colors',
          activeTab === 'tax-profiles'
            ? 'border-b-2 border-slate-900 text-slate-900'
            : 'text-slate-500 hover:text-slate-700'
        ]"
      >
        Tax Profiles
      </button>
      <button
        @click="activeTab = 'salary-structures'"
        :class="[
          'px-4 py-3 font-medium transition-colors',
          activeTab === 'salary-structures'
            ? 'border-b-2 border-slate-900 text-slate-900'
            : 'text-slate-500 hover:text-slate-700'
        ]"
      >
        Salary Structures
      </button>
    </div>

    <!-- Tax Profiles Tab -->
    <div v-if="activeTab === 'tax-profiles'" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">Select Employee</label>
          <select
            v-model="selectedEmployee"
            class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
          >
            <option value="">Choose employee...</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">Financial Year</label>
          <select
            v-model.number="selectedFinancialYear"
            class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
          >
            <option v-for="year in [2024, 2025, 2026, 2027]" :key="year" :value="year">{{ year }}</option>
          </select>
        </div>
      </div>

      <div v-if="selectedEmployee" class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-2xl p-6">
        <h3 class="text-lg font-bold text-slate-900 mb-6">Tax Profile Details</h3>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Tax Regime</label>
            <select
              v-model="taxProfileForm.tax_regime"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            >
              <option value="old">Old Regime</option>
              <option value="new">New Regime</option>
            </select>
          </div>

          <div class="flex items-end">
            <label class="flex items-center">
              <input
                v-model="taxProfileForm.is_metro_city"
                type="checkbox"
                class="w-4 h-4 rounded border-slate-300"
              />
              <span class="ml-2 text-sm text-slate-700">Metro City (for HRA exemption)</span>
            </label>
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">80C Investments (₹)</label>
            <input
              v-model.number="taxProfileForm.investment_80c"
              type="number"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">80D Health Insurance (₹)</label>
            <input
              v-model.number="taxProfileForm.investment_80d"
              type="number"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">HRA Rent Paid (₹)</label>
            <input
              v-model.number="taxProfileForm.hra_rent_paid"
              type="number"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">NPS (80CCC) (₹)</label>
            <input
              v-model.number="taxProfileForm.nps_voluntary"
              type="number"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>
        </div>

        <div class="flex gap-3">
          <button
            @click="saveTaxProfile"
            class="px-6 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 font-medium transition-colors"
          >
            Save Changes
          </button>
        </div>
      </div>

      <div v-else class="text-center py-12 text-slate-500">
        Select an employee to view and edit tax profile
      </div>
    </div>

    <!-- Salary Structures Tab -->
    <div v-if="activeTab === 'salary-structures'" class="space-y-6">
      <div class="flex justify-between items-center">
        <h3 class="text-lg font-bold text-slate-900">Salary Structures</h3>
        <button
          @click="structureForm = { name: '', description: '', basic_pct: 50, hra_pct: 20, allowances_pct: 30, pf_pct: 12, esi_pct: 0.75, professional_tax: 200 }"
          class="px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 font-medium transition-colors text-sm"
        >
          + New Structure
        </button>
      </div>

      <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 rounded-2xl p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Structure Name</label>
            <input
              v-model="structureForm.name"
              type="text"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Description</label>
            <input
              v-model="structureForm.description"
              type="text"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Basic (%)</label>
            <input
              v-model.number="structureForm.basic_pct"
              type="number"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">HRA (%)</label>
            <input
              v-model.number="structureForm.hra_pct"
              type="number"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Allowances (%)</label>
            <input
              v-model.number="structureForm.allowances_pct"
              type="number"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">PF (%)</label>
            <input
              v-model.number="structureForm.pf_pct"
              type="number"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">ESI (%)</label>
            <input
              v-model.number="structureForm.esi_pct"
              type="number"
              step="0.01"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Professional Tax (₹)</label>
            <input
              v-model.number="structureForm.professional_tax"
              type="number"
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>
        </div>

        <button
          @click="saveStructure"
          class="px-6 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 font-medium transition-colors"
        >
          Save Structure
        </button>
      </div>
    </div>
  </div>
</template>
