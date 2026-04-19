<script setup lang="ts">
import { ref } from 'vue'
import { createCompanyWithAdmin, type CreateCompanyPayload } from '../services/company.service'

const emit = defineEmits<{
  close: []
  created: []
}>()

const step = ref<1 | 2>(1)
const isLoading = ref(false)
const errorMsg = ref('')

const companyName = ref('')
const companyDomain = ref('')
const adminEmail = ref('')
const adminPassword = ref('')
const adminPasswordConfirm = ref('')

async function submit() {
  errorMsg.value = ''

  if (adminPassword.value !== adminPasswordConfirm.value) {
    errorMsg.value = 'Passwords do not match'
    return
  }

  isLoading.value = true
  try {
    const payload: CreateCompanyPayload = {
      name: companyName.value,
      ...(companyDomain.value ? { domain: companyDomain.value } : {}),
      admin: { email: adminEmail.value, password: adminPassword.value },
    }
    await createCompanyWithAdmin(payload)
    emit('created')
    emit('close')
  } catch (err: any) {
    errorMsg.value = err.message || 'Failed to create company'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md shadow-2xl">
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div>
          <h2 class="text-base font-semibold text-white">New Company</h2>
          <p class="text-xs text-slate-400 mt-0.5">Step {{ step }} of 2 — {{ step === 1 ? 'Company Info' : 'Admin Account' }}</p>
        </div>
        <button @click="emit('close')" class="text-slate-400 hover:text-white transition-colors">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="px-6 py-5 space-y-4">
        <!-- Step 1: Company Info -->
        <template v-if="step === 1">
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">Company Name <span class="text-red-400">*</span></label>
            <input
              v-model="companyName"
              type="text"
              placeholder="Acme Corp"
              class="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">Domain <span class="text-slate-500">(optional)</span></label>
            <input
              v-model="companyDomain"
              type="text"
              placeholder="acme.com"
              class="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>
        </template>

        <!-- Step 2: Admin Account -->
        <template v-else>
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">Admin Email <span class="text-red-400">*</span></label>
            <input
              v-model="adminEmail"
              type="email"
              placeholder="admin@acme.com"
              class="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">Password <span class="text-red-400">*</span></label>
            <input
              v-model="adminPassword"
              type="password"
              placeholder="Min 10 chars, upper+lower+digit+special"
              class="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">Confirm Password <span class="text-red-400">*</span></label>
            <input
              v-model="adminPasswordConfirm"
              type="password"
              placeholder="Repeat password"
              class="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>
        </template>

        <div v-if="errorMsg" class="bg-red-950/50 border border-red-800 rounded-lg px-3.5 py-2.5 text-red-300 text-sm">
          {{ errorMsg }}
        </div>
      </div>

      <div class="flex items-center justify-between px-6 py-4 border-t border-slate-800">
        <button
          v-if="step === 2"
          @click="step = 1"
          class="text-sm text-slate-400 hover:text-white transition-colors"
        >
          Back
        </button>
        <div v-else />
        <div class="flex gap-2">
          <button
            @click="emit('close')"
            class="text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-4 py-2 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            v-if="step === 1"
            @click="() => { if (companyName.trim()) step = 2; else errorMsg = 'Company name is required' }"
            class="text-sm bg-violet-600 hover:bg-violet-500 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Next
          </button>
          <button
            v-else
            @click="submit"
            :disabled="isLoading"
            class="text-sm bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {{ isLoading ? 'Creating...' : 'Create Company' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
