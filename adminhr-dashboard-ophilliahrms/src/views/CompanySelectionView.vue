<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { BuildingIcon, ArrowRightIcon, PlusIcon, LogOutIcon } from 'lucide-vue-next'
import { companyApi } from '../services/api'
import { clearTokens } from '../services/http'

const router = useRouter()
const companies = ref<any[]>([])
const isLoading = ref(true)

onMounted(async () => {
  try {
    const result = await companyApi.getCompanies()
    companies.value = result.data.companies.map((c: any) => ({
      ...c,
      glow: 'bg-emerald-200/30' // Visual enhancement from guideline
    }))
  } catch (err) {
    console.error('Failed to fetch companies', err)
  } finally {
    isLoading.value = false
  }
})

const selectCompany = (company: any) => {
  localStorage.setItem('selected_company_id', company.id)
  router.push('/dashboard')
}

const logout = () => {
  clearTokens()
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen p-6 sm:p-12 relative flex flex-col">
    
    <!-- Header -->
    <div class="w-full max-w-6xl mx-auto flex justify-between items-center mb-16 relative z-10">
      <div class="flex items-center space-x-4">
        <div class="w-12 h-12 bg-slate-900 rounded-[16px] flex items-center justify-center shadow-md">
           <span class="text-white text-xl font-bold font-serif leading-none italic">O</span>
        </div>
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-slate-900">Select Entity</h1>
          <p class="text-slate-500 font-medium text-sm">Choose a company workspace to manage</p>
        </div>
      </div>
      
      <button @click="logout" class="p-3 bg-white/50 hover:bg-white/80 border border-slate-200/50 backdrop-blur text-slate-600 hover:text-slate-900 rounded-xl transition-all duration-300 shadow-sm hover:shadow active:scale-95" title="Logout">
        <LogOutIcon class="w-5 h-5" />
      </button>
    </div>

    <!-- Grid -->
    <div class="w-full max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 relative z-10">
      
      <!-- Company Card -->
      <button 
        v-for="company in companies" 
        :key="company.id"
        @click="selectCompany(company)"
        class="group text-left relative bg-white/60 backdrop-blur-md border border-slate-200/60 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.1)] rounded-[24px] p-8 transition-all duration-500 hover:-translate-y-1 overflow-hidden"
      >
        <!-- Internal Glow on hover -->
        <div :class="['absolute -top-10 -right-10 w-32 h-32 blur-[40px] rounded-full transition-all duration-700 opacity-0 group-hover:opacity-100', company.glow]"></div>

        <div class="flex items-start justify-between mb-8 relative z-10">
          <div class="w-14 h-14 rounded-[16px] bg-white flex items-center justify-center border border-slate-100 shadow-sm group-hover:scale-105 transition-transform duration-300">
            <BuildingIcon class="w-6 h-6 text-slate-700" />
          </div>
          <div class="bg-white/80 backdrop-blur border border-slate-100 text-slate-600 text-xs font-semibold px-3 py-1 rounded-full shadow-sm">
            {{ company.role }}
          </div>
        </div>

        <div class="space-y-1 relative z-10">
          <h2 class="text-xl font-bold text-slate-900">{{ company.name }}</h2>
          <p class="text-slate-500 font-medium text-sm">{{ company.employees }} Employees</p>
        </div>

        <div class="mt-8 flex items-center text-sm font-semibold text-slate-900 opacity-0 group-hover:opacity-100 -translate-x-4 group-hover:translate-x-0 transition-all duration-300 relative z-10">
          <span>Enter Workspace</span>
          <ArrowRightIcon class="w-4 h-4 ml-2" />
        </div>
      </button>

      <!-- Add New Entity Card -->
      <button class="min-h-[260px] border-2 border-dashed border-slate-300/70 hover:border-slate-400 bg-white/20 hover:bg-white/40 backdrop-blur-sm rounded-[24px] p-8 flex flex-col items-center justify-center text-slate-500 hover:text-slate-800 transition-all duration-300 group">
        <div class="w-14 h-14 rounded-full bg-slate-200/60 group-hover:bg-slate-200 flex items-center justify-center mb-4 transition-colors duration-300">
          <PlusIcon class="w-6 h-6" />
        </div>
        <span class="font-semibold">Add New Entity</span>
      </button>

    </div>
  </div>
</template>
