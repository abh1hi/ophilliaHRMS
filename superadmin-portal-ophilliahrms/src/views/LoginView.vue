<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.store'
import { login, decodeToken } from '../services/auth.service'

const router = useRouter()
const auth = useAuthStore()
const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  isLoading.value = true
  errorMsg.value = ''
  try {
    const data = await login(email.value, password.value)
    const claims = decodeToken(data.access_token)

    if (!claims || claims.role !== 'super_admin') {
      errorMsg.value = 'Access denied. This portal is for super admin accounts only. Use the HR Dashboard instead.'
      return
    }

    auth.setTokens(data.access_token, data.refresh_token)
    router.push('/dashboard')
  } catch (err: any) {
    errorMsg.value = err.message || 'Authentication failed'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-950 flex items-center justify-center p-6">
    <div class="w-full max-w-[420px]">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <div class="text-center mb-8">
          <div class="w-12 h-12 mx-auto bg-violet-600 rounded-xl flex items-center justify-center mb-4">
            <span class="text-white text-xl font-bold italic">O</span>
          </div>
          <h1 class="text-xl font-semibold text-white">Super Admin Portal</h1>
          <p class="text-slate-400 text-sm mt-1">Ophillia HRMS Platform Management</p>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
            <input
              v-model="email"
              type="email"
              required
              autocomplete="username"
              placeholder="superadmin@example.com"
              class="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent placeholder-slate-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
            <input
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
              placeholder="••••••••••"
              class="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent placeholder-slate-500"
            />
          </div>

          <div v-if="errorMsg" class="bg-red-950/50 border border-red-800 rounded-lg px-3.5 py-2.5 text-red-300 text-sm">
            {{ errorMsg }}
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg px-4 py-2.5 text-sm transition-colors mt-2"
          >
            {{ isLoading ? 'Signing in...' : 'Sign in' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
