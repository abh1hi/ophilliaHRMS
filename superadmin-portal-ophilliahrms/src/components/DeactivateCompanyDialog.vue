<script setup lang="ts">
import { ref } from 'vue'
import type { Company } from '../services/company.service'
import { deactivateCompany } from '../services/company.service'

const props = defineProps<{ company: Company }>()
const emit = defineEmits<{ close: []; deactivated: [] }>()

const confirmName = ref('')
const isLoading = ref(false)
const errorMsg = ref('')

const isConfirmed = () => confirmName.value.trim() === props.company.name.trim()

async function confirm() {
  if (!isConfirmed()) {
    errorMsg.value = 'Company name does not match'
    return
  }
  isLoading.value = true
  errorMsg.value = ''
  try {
    await deactivateCompany(props.company.id)
    emit('deactivated')
    emit('close')
  } catch (err: any) {
    errorMsg.value = err.message || 'Failed to deactivate company'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-slate-900 border border-red-900/50 rounded-2xl w-full max-w-sm shadow-2xl">
      <div class="px-6 py-5">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-full bg-red-500/15 flex items-center justify-center">
            <svg class="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <h2 class="text-base font-semibold text-white">Deactivate Company</h2>
            <p class="text-xs text-slate-400 mt-0.5">This will block all logins for this company</p>
          </div>
        </div>

        <p class="text-sm text-slate-300 mb-4">
          Type <span class="font-mono text-white bg-slate-800 px-1.5 py-0.5 rounded text-xs">{{ company.name }}</span> to confirm.
        </p>

        <input
          v-model="confirmName"
          type="text"
          :placeholder="company.name"
          class="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 mb-3"
        />

        <div v-if="errorMsg" class="bg-red-950/50 border border-red-800 rounded-lg px-3 py-2 text-red-300 text-xs mb-3">
          {{ errorMsg }}
        </div>

        <div class="flex gap-2">
          <button
            @click="emit('close')"
            class="flex-1 text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-4 py-2 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            @click="confirm"
            :disabled="isLoading || !isConfirmed()"
            class="flex-1 text-sm bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg transition-colors"
          >
            {{ isLoading ? 'Deactivating...' : 'Deactivate' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
