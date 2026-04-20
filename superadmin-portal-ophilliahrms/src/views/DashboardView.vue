<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.store'
import { listCompanies, reactivateCompany, type Company } from '../services/company.service'
import CompanyTable from '../components/CompanyTable.vue'
import CreateCompanyModal from '../components/CreateCompanyModal.vue'
import DeactivateCompanyDialog from '../components/DeactivateCompanyDialog.vue'

const router = useRouter()
const auth = useAuthStore()

const companies = ref<Company[]>([])
const total = ref(0)
const isLoading = ref(false)
const errorMsg = ref('')

const showCreateModal = ref(false)
const deactivateTarget = ref<Company | null>(null)

async function loadCompanies() {
  isLoading.value = true
  errorMsg.value = ''
  try {
    const res = await listCompanies()
    companies.value = res.companies
    total.value = res.total
  } catch (err: any) {
    errorMsg.value = err.message || 'Failed to load companies'
  } finally {
    isLoading.value = false
  }
}

async function handleReactivate(company: Company) {
  try {
    await reactivateCompany(company.id)
    await loadCompanies()
  } catch (err: any) {
    errorMsg.value = err.message || 'Failed to reactivate company'
  }
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(loadCompanies)
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-white">
    <!-- Header -->
    <header class="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 bg-violet-600 rounded-lg flex items-center justify-center">
          <span class="text-white text-sm font-bold italic">O</span>
        </div>
        <div>
          <span class="text-white font-semibold text-sm">Ophillia HRMS</span>
          <span class="ml-2 text-xs text-violet-400 bg-violet-500/15 border border-violet-500/30 px-1.5 py-0.5 rounded-full">Super Admin</span>
        </div>
      </div>
      <button
        @click="handleLogout"
        class="text-sm text-slate-400 hover:text-white transition-colors flex items-center gap-1.5"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
        Sign out
      </button>
    </header>

    <!-- Main -->
    <main class="max-w-6xl mx-auto px-6 py-8">
      <!-- Page title + actions -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-xl font-semibold text-white">Companies</h1>
          <p class="text-sm text-slate-400 mt-0.5">{{ total }} tenant{{ total !== 1 ? 's' : '' }} provisioned</p>
        </div>
        <button
          @click="showCreateModal = true"
          class="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          New Company
        </button>
      </div>

      <!-- Error -->
      <div v-if="errorMsg" class="bg-red-950/50 border border-red-800 rounded-lg px-4 py-3 text-red-300 text-sm mb-4">
        {{ errorMsg }}
      </div>

      <!-- Table -->
      <CompanyTable
        :companies="companies"
        :loading="isLoading"
        @deactivate="c => deactivateTarget = c"
        @reactivate="handleReactivate"
      />
    </main>

    <!-- Modals -->
    <CreateCompanyModal
      v-if="showCreateModal"
      @close="showCreateModal = false"
      @created="loadCompanies"
    />
    <DeactivateCompanyDialog
      v-if="deactivateTarget"
      :company="deactivateTarget"
      @close="deactivateTarget = null"
      @deactivated="loadCompanies"
    />
  </div>
</template>
