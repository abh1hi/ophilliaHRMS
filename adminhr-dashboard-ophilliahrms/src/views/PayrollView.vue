<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppSidebar from '../components/layout/AppSidebar.vue'
import AppHeader from '../components/layout/AppHeader.vue'
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

// Decode role directly from the stored JWT
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
    // Already on payroll page
    activeTab.value = 'runs'
  } else {
    // Navigate to other pages via dashboard
    router.push(`/dashboard?tab=${tab}`)
  }
}

function navigateToProfile() {
  router.push('/dashboard?tab=profile')
}

function switchEntity() {
  router.push('/select-company')
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
  <div class="min-h-screen flex relative">
    <!-- Sidebar -->
    <AppSidebar
      :current-tab="'payroll'"
      :company-name="companyName"
      :user-role="userRole"
      @navigate="navigateTab"
      @switch-entity="switchEntity"
      @logout="handleLogout"
    />

    <!-- Main Content -->
    <main class="flex-1 p-8 sm:p-12 h-screen overflow-y-auto relative z-10">
      <AppHeader
        title="Payroll Management"
        subtitle="Manage payroll runs, approve/process payments, and generate compliance reports"
        :user-name="userName"
        :user-role="userRole"
        @profile-click="navigateToProfile"
        @logout="handleLogout"
      />

      <!-- Tabs -->
      <div class="flex gap-4 border-b border-slate-200 mb-8">
        <button
          @click="activeTab = 'runs'"
          :class="[
            'px-4 py-3 font-medium transition-colors',
            activeTab === 'runs'
              ? 'border-b-2 border-slate-900 text-slate-900'
              : 'text-slate-500 hover:text-slate-700'
          ]"
        >
          Payroll Runs
        </button>
        <button
          @click="activeTab = 'reports'"
          :class="[
            'px-4 py-3 font-medium transition-colors',
            activeTab === 'reports'
              ? 'border-b-2 border-slate-900 text-slate-900'
              : 'text-slate-500 hover:text-slate-700'
          ]"
        >
          Reports & Exports
        </button>
        <button
          @click="activeTab = 'settings'"
          :class="[
            'px-4 py-3 font-medium transition-colors',
            activeTab === 'settings'
              ? 'border-b-2 border-slate-900 text-slate-900'
              : 'text-slate-500 hover:text-slate-700'
          ]"
        >
          Settings
        </button>
      </div>

      <!-- Tab Content -->
      <div v-show="activeTab === 'runs'">
        <PayrollRunsTab :show-new-run="showNewRun" @run-created="onRunCreated" />
      </div>

      <div v-show="activeTab === 'reports'">
        <PayrollReportsTab />
      </div>

      <div v-show="activeTab === 'settings'">
        <PayrollSettingsTab />
      </div>
    </main>
  </div>
</template>

<style scoped>
.payroll-container {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
