<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { XIcon, BuildingIcon, ShieldCheckIcon, UserIcon, CheckCircle2Icon } from 'lucide-vue-next'
import { createCompany, createUser, selectCompany } from '../../services/auth.service'
import { handleApiError } from '../../utils/handleApiError'
import type { Company } from '../../services/auth.service'

const emit = defineEmits<{ close: [] }>()
const router = useRouter()

const step = ref(1)
const saving = ref(false)
const errorMsg = ref('')

// Created data
const newCompany = ref<Company | null>(null)
const adminEmail = ref('')
const hrEmail = ref('')

// Step 1
const companyForm = reactive({ name: '', domain: '' })

// Step 2
const adminForm = reactive({ email: '', password: '' })

// Step 3
const hrForm = reactive({ email: '', password: '' })

const PASSWORD_HINT = 'Min 10 chars · Uppercase + lowercase + digit + special char'

async function createCompanyStep() {
  if (saving.value) return
  if (!companyForm.name.trim()) { errorMsg.value = 'Company name is required'; return }
  saving.value = true; errorMsg.value = ''
  try {
    newCompany.value = await createCompany(companyForm.name.trim(), companyForm.domain.trim() || undefined)
    step.value = 2
  } catch (e) {
    errorMsg.value = handleApiError(e)
  } finally {
    saving.value = false
  }
}

async function createAdminStep() {
  if (saving.value) return
  if (!adminForm.email.trim() || !adminForm.password) { errorMsg.value = 'Email and password are required'; return }
  saving.value = true; errorMsg.value = ''
  try {
    await createUser({
      email: adminForm.email.trim(),
      password: adminForm.password,
      role: 'admin',
      company_id: newCompany.value!.id,
    })
    adminEmail.value = adminForm.email.trim()
    step.value = 3
  } catch (e) {
    errorMsg.value = handleApiError(e)
  } finally {
    saving.value = false
  }
}

async function createHrStep() {
  if (saving.value) return
  if (!hrForm.email.trim() || !hrForm.password) { errorMsg.value = 'Email and password are required'; return }
  saving.value = true; errorMsg.value = ''
  try {
    await createUser({
      email: hrForm.email.trim(),
      password: hrForm.password,
      role: 'hr',
      company_id: newCompany.value!.id,
    })
    hrEmail.value = hrForm.email.trim()
    step.value = 4
  } catch (e) {
    errorMsg.value = handleApiError(e)
  } finally {
    saving.value = false
  }
}

function skipHr() {
  step.value = 4
}

async function enterWorkspace() {
  if (saving.value || !newCompany.value) return
  saving.value = true; errorMsg.value = ''
  try {
    // Get a fresh JWT scoped to the new company
    await selectCompany(newCompany.value.id)
    router.push('/onboarding')
  } catch (e) {
    errorMsg.value = handleApiError(e)
  } finally {
    saving.value = false
  }
}

const stepLabels = ['Company', 'Admin', 'HR User', 'Done']
</script>

<template>
  <!-- Overlay -->
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" @click="emit('close')"></div>

    <div class="relative z-10 bg-white rounded-[24px] shadow-2xl w-full max-w-lg overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-slate-100">
        <div>
          <h2 class="text-lg font-bold text-slate-900">Create New Company</h2>
          <p class="text-sm text-slate-400 font-medium mt-0.5">Set up a new workspace in Ophillia HRMS</p>
        </div>
        <button @click="emit('close')" class="p-2 hover:bg-slate-100 rounded-[10px] text-slate-400 hover:text-slate-700 transition-colors">
          <XIcon class="w-5 h-5" />
        </button>
      </div>

      <!-- Step indicators -->
      <div class="flex items-center px-6 pt-5 pb-1 space-x-0">
        <div v-for="(label, i) in stepLabels" :key="i" class="flex items-center flex-1">
          <div class="flex flex-col items-center">
            <div :class="[
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all',
              step > i + 1 ? 'bg-emerald-500 text-white' :
              step === i + 1 ? 'bg-slate-900 text-white' :
              'bg-slate-100 text-slate-400',
            ]">
              <CheckCircle2Icon v-if="step > i + 1" class="w-4 h-4" />
              <span v-else>{{ i + 1 }}</span>
            </div>
            <span :class="['text-xs font-semibold mt-1', step === i + 1 ? 'text-slate-900' : 'text-slate-400']">{{ label }}</span>
          </div>
          <div v-if="i < stepLabels.length - 1" :class="['flex-1 h-0.5 mb-4 mx-1', step > i + 1 ? 'bg-emerald-400' : 'bg-slate-100']"></div>
        </div>
      </div>

      <!-- Step content -->
      <div class="p-6 pt-4 space-y-5 min-h-[240px]">

        <!-- Step 1: Company Details -->
        <div v-if="step === 1">
          <div class="flex items-center space-x-2 mb-5">
            <BuildingIcon class="w-5 h-5 text-slate-400" />
            <h3 class="text-sm font-semibold text-slate-700">Company Details</h3>
          </div>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">Company Name <span class="text-rose-500">*</span></label>
              <input v-model="companyForm.name" type="text" placeholder="Acme Corporation"
                class="w-full bg-slate-50 border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">Domain <span class="text-slate-400 font-normal">(optional)</span></label>
              <input v-model="companyForm.domain" type="text" placeholder="acme.com"
                class="w-full bg-slate-50 border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all" />
            </div>
          </div>
        </div>

        <!-- Step 2: Admin -->
        <div v-else-if="step === 2">
          <div class="flex items-center space-x-2 mb-5">
            <ShieldCheckIcon class="w-5 h-5 text-slate-400" />
            <h3 class="text-sm font-semibold text-slate-700">Create Admin Account for <span class="text-slate-900">{{ newCompany?.name }}</span></h3>
          </div>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">Admin Email <span class="text-rose-500">*</span></label>
              <input v-model="adminForm.email" type="email" placeholder="admin@company.com"
                class="w-full bg-slate-50 border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">Password <span class="text-rose-500">*</span></label>
              <input v-model="adminForm.password" type="password" placeholder="Strong password"
                class="w-full bg-slate-50 border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all" />
              <p class="text-xs text-slate-400 mt-1.5">{{ PASSWORD_HINT }}</p>
            </div>
          </div>
        </div>

        <!-- Step 3: HR -->
        <div v-else-if="step === 3">
          <div class="flex items-center space-x-2 mb-5">
            <UserIcon class="w-5 h-5 text-slate-400" />
            <h3 class="text-sm font-semibold text-slate-700">Add HR User <span class="text-slate-400 font-normal">(optional)</span></h3>
          </div>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">HR Email</label>
              <input v-model="hrForm.email" type="email" placeholder="hr@company.com"
                class="w-full bg-slate-50 border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1.5">Password</label>
              <input v-model="hrForm.password" type="password" placeholder="Strong password"
                class="w-full bg-slate-50 border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all" />
              <p class="text-xs text-slate-400 mt-1.5">{{ PASSWORD_HINT }}</p>
            </div>
          </div>
        </div>

        <!-- Step 4: Done -->
        <div v-else-if="step === 4">
          <div class="text-center py-4 space-y-4">
            <div class="w-14 h-14 mx-auto bg-emerald-100 rounded-full flex items-center justify-center">
              <CheckCircle2Icon class="w-7 h-7 text-emerald-600" />
            </div>
            <div>
              <h3 class="text-lg font-bold text-slate-900">Company created!</h3>
              <p class="text-slate-500 text-sm mt-1">Your workspace is ready to set up.</p>
            </div>
            <div class="text-left bg-slate-50 border border-slate-100 rounded-[14px] p-4 space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-slate-400 font-medium">Company</span>
                <span class="font-semibold text-slate-800">{{ newCompany?.name }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400 font-medium">Admin</span>
                <span class="font-semibold text-slate-800">{{ adminEmail }}</span>
              </div>
              <div v-if="hrEmail" class="flex justify-between">
                <span class="text-slate-400 font-medium">HR User</span>
                <span class="font-semibold text-slate-800">{{ hrEmail }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Error -->
        <p v-if="errorMsg" class="text-sm text-rose-600 font-medium">{{ errorMsg }}</p>
      </div>

      <!-- Footer actions -->
      <div class="px-6 pb-6 flex items-center gap-3">
        <!-- Step 1 -->
        <template v-if="step === 1">
          <button @click="createCompanyStep" :disabled="saving"
            class="flex-1 px-5 py-3 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-all disabled:opacity-60 flex items-center justify-center space-x-2">
            <div v-if="saving" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <span>{{ saving ? 'Creating...' : 'Create Company' }}</span>
          </button>
        </template>

        <!-- Step 2 -->
        <template v-else-if="step === 2">
          <button @click="createAdminStep" :disabled="saving"
            class="flex-1 px-5 py-3 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-all disabled:opacity-60 flex items-center justify-center space-x-2">
            <div v-if="saving" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <span>{{ saving ? 'Creating...' : 'Create Admin Account' }}</span>
          </button>
        </template>

        <!-- Step 3 -->
        <template v-else-if="step === 3">
          <button @click="createHrStep" :disabled="saving"
            class="flex-1 px-5 py-3 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-all disabled:opacity-60 flex items-center justify-center space-x-2">
            <div v-if="saving" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <span>{{ saving ? 'Adding...' : 'Add HR User' }}</span>
          </button>
          <button @click="skipHr" :disabled="saving"
            class="px-5 py-3 border border-slate-200 text-slate-500 hover:bg-slate-50 rounded-full text-sm font-semibold transition-colors disabled:opacity-60">
            Skip
          </button>
        </template>

        <!-- Step 4 -->
        <template v-else-if="step === 4">
          <button @click="enterWorkspace" :disabled="saving"
            class="flex-1 px-5 py-3 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-all disabled:opacity-60 flex items-center justify-center space-x-2">
            <div v-if="saving" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <span>{{ saving ? 'Entering...' : 'Enter Workspace →' }}</span>
          </button>
          <button @click="emit('close')" :disabled="saving"
            class="px-5 py-3 border border-slate-200 text-slate-500 hover:bg-slate-50 rounded-full text-sm font-semibold transition-colors disabled:opacity-60">
            Back to Companies
          </button>
        </template>
      </div>
    </div>
  </div>
</template>
