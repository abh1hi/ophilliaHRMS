<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { UserIcon, LockIcon, ArrowRightIcon } from 'lucide-vue-next'
import { login, logout, postLoginContext } from '../services/auth.service'

const router = useRouter()
const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMsg = ref('')

const handleLogin = async () => {
  isLoading.value = true
  errorMsg.value = ''
  try {
    const result = await login(email.value, password.value)

    // Super admin must use the Super Admin Portal, not this dashboard
    if (result.claims.role === 'super_admin') {
      logout()
      errorMsg.value = 'Super admin accounts must use the Super Admin Portal (port 3001).'
      return
    }

    // Try backend-driven routing; fall back to JWT role if endpoint unavailable
    try {
      const ctx = await postLoginContext()
      if (ctx.next_action === 'COMPLETE_ONBOARDING') {
        router.push('/onboarding')
      } else {
        router.push('/dashboard')
      }
    } catch {
      router.push('/dashboard')
    }
  } catch (err: any) {
    errorMsg.value = err.message || 'Authentication failed'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center p-6">
    <div class="relative w-full max-w-[480px]">
      <!-- Localized glowing tint behind the card -->
      <div class="absolute -top-10 -right-10 w-48 h-48 bg-rose-200/40 blur-[80px] rounded-full pointer-events-none z-0"></div>

      <!-- Glass Card -->
      <div class="relative z-10 bg-white/70 backdrop-blur-md border border-slate-200/60 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)] rounded-[24px] p-8 sm:p-12 overflow-hidden">
        
        <div class="mb-10 text-center space-y-2">
          <div class="w-14 h-14 mx-auto bg-slate-900 rounded-[18px] flex items-center justify-center mb-6 shadow-md">
            <span class="text-white text-2xl font-bold font-serif leading-none italic">O</span>
          </div>
          <h1 class="text-3xl font-bold tracking-tight text-slate-900">Sign in</h1>
          <p class="text-slate-500 font-medium">Continue to Ophillia HRMS Admin</p>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-6">
          <div class="space-y-4">
            <!-- Email Input -->
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
                <UserIcon class="w-5 h-5" />
              </div>
              <input
                v-model="email"
                type="email"
                required
                autocomplete="username"
                placeholder="Admin Email"
                class="w-full bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-[16px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 block pl-12 p-3.5 transition-all outline-none"
              >
            </div>
            
            <!-- Password Input -->
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
                <LockIcon class="w-5 h-5" />
              </div>
              <input
                v-model="password"
                type="password"
                required
                autocomplete="current-password"
                placeholder="Password"
                class="w-full bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-[16px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 block pl-12 p-3.5 transition-all outline-none"
              >
            </div>
          </div>

          <div class="flex items-center justify-between text-sm py-2">
            <label class="flex items-center space-x-2 cursor-pointer group">
              <input type="checkbox" class="rounded text-slate-900 focus:ring-slate-900/20 w-4 h-4 border-slate-300 transition-colors">
              <span class="text-slate-500 group-hover:text-slate-700 transition-colors">Remember me</span>
            </label>
            <a href="#" class="text-slate-900 font-medium hover:underline">Forgot password?</a>
          </div>

          <button
            type="submit"
            class="w-full bg-slate-900 text-white rounded-full px-5 py-3.5 font-medium hover:bg-slate-800 transition-all duration-300 flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0"
            :disabled="isLoading"
          >
            <span>{{ isLoading ? 'Signing in...' : 'Sign in' }}</span>
            <ArrowRightIcon v-if="!isLoading" class="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
