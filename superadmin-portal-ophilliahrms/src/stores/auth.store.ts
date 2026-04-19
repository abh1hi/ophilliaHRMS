import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { decodeToken } from '../services/auth.service'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('sa_access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('sa_refresh_token'))

  const claims = computed(() => (accessToken.value ? decodeToken(accessToken.value) : null))
  const role = computed(() => claims.value?.role ?? null)
  const isAuthenticated = computed(
    () => !!accessToken.value && !!claims.value && claims.value.exp * 1000 > Date.now()
  )

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('sa_access_token', access)
    localStorage.setItem('sa_refresh_token', refresh)
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('sa_access_token')
    localStorage.removeItem('sa_refresh_token')
  }

  return { accessToken, refreshToken, claims, role, isAuthenticated, setTokens, logout }
})
