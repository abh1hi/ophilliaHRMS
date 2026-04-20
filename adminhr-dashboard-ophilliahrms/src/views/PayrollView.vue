<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppTopNav from '../components/layout/AppTopNav.vue'
import PayrollRunsTab from '../components/payroll/PayrollRunsTab.vue'
import PayrollReportsTab from '../components/payroll/PayrollReportsTab.vue'
import PayrollSettingsTab from '../components/payroll/PayrollSettingsTab.vue'
import { getEmployeeProfile, logout, decodeToken } from '../services/auth.service'
import { getToken } from '../services/http'
import type { EmployeeProfile } from '../services/auth.service'

const router = useRouter()
const activeTab = ref('runs')
const showNewRun = ref(false)
const employeeProfile = ref<EmployeeProfile | null>(null)
const companyName = ref(localStorage.getItem('company_name') || 'Ophillia HRMS')

const claims = decodeToken(getToken())
const userRole = claims?.role ?? ''

const userName = computed(() => {
  if (!employeeProfile.value) return claims?.email ?? '—'
  const { first_name, last_name } = employeeProfile.value
  return `${first_name ?? ''} ${last_name ?? ''}`.trim() || claims?.email || '—'
})

onMounted(async () => {
  employeeProfile.value = await getEmployeeProfile()
})

function navigateTab(tab: string) {
  if (tab === 'payroll') {
    activeTab.value = 'runs'
  } else {
    router.push(`/dashboard?tab=${tab}`)
  }
}

function handleLogout() {
  logout()
  router.push('/')
}

function onRunCreated() {
  showNewRun.value = false
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-slate-50">
    <AppTopNav
      current-tab="payroll"
      :company-name="companyName"
      :user-role="userRole"
      :user-name="userName"
      @navigate="navigateTab"
      @logout="handleLogout"
    />

    <main class="flex-1 overflow-y-auto no-scrollbar">
      <!-- Page header -->
      <div class="px-6 pt-6 pb-4 bg-white border-b border-slate-200">
        <h1 class="text-xl font-semibold text-slate-900">Payroll</h1>
        <p class="text-sm text-slate-500 mt-0.5">Manage payroll runs, approve payments, and generate reports</p>
      </div>

      <div class="p-6">
        <!-- Sub-tabs -->
        <div class="flex gap-1 border-b border-slate-200 mb-6">
          <button
            @click="activeTab = 'runs'"
            :class="[
              'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px',
              activeTab === 'runs'
                ? 'border-indigo-600 text-indigo-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            ]"
          >
            Payroll Runs
          </button>
          <button
            @click="activeTab = 'reports'"
            :class="[
              'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px',
              activeTab === 'reports'
                ? 'border-indigo-600 text-indigo-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            ]"
          >
            Reports & Exports
          </button>
          <button
            @click="activeTab = 'settings'"
            :class="[
              'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px',
              activeTab === 'settings'
                ? 'border-indigo-600 text-indigo-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            ]"
          >
            Settings
          </button>
        </div>

        <!-- Tab content -->
        <div v-show="activeTab === 'runs'">
          <PayrollRunsTab :show-new-run="showNewRun" @run-created="onRunCreated" />
        </div>
        <div v-show="activeTab === 'reports'">
          <PayrollReportsTab />
        </div>
        <div v-show="activeTab === 'settings'">
          <PayrollSettingsTab />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
