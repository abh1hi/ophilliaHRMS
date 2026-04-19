<script setup lang="ts">
import { ref } from 'vue'
import { UserCircle, LogOut, User, ChevronDown, ChevronRight } from 'lucide-vue-next'

defineProps<{
  title?: string
  subtitle?: string
  userName?: string
  userRole?: string
}>()

const emit = defineEmits<{
  (e: 'profile-click'): void
  (e: 'logout'): void
}>()

const menuOpen = ref(false)

function onProfile() {
  menuOpen.value = false
  emit('profile-click')
}

function onLogout() {
  menuOpen.value = false
  emit('logout')
}
</script>

<template>
  <div class="relative z-30 mb-6">
    <header class="flex justify-between items-start">
      <div class="space-y-0.5">
        <h1 class="text-xl font-semibold text-slate-900">{{ title }}</h1>
        <p v-if="subtitle" class="text-sm text-slate-500">{{ subtitle }}</p>
      </div>

      <div class="relative flex items-center gap-3">
        <div class="hidden sm:block text-right">
          <p class="text-sm font-medium text-slate-800">{{ userName || '—' }}</p>
          <p class="text-xs text-slate-400 capitalize">{{ userRole?.replace('_', ' ') }}</p>
        </div>

        <button
          @click="menuOpen = !menuOpen"
          class="flex items-center gap-1.5 h-9 px-2.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-all"
        >
          <UserCircle class="w-5 h-5" />
          <ChevronDown :class="['w-3.5 h-3.5 transition-transform', menuOpen ? 'rotate-180' : '']" />
        </button>

        <Transition name="drop">
          <div
            v-if="menuOpen"
            class="absolute top-11 right-0 w-48 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden z-50 py-1"
          >
            <div class="px-3 py-2 border-b border-slate-100">
              <p class="text-xs text-slate-400 mb-0.5">Account</p>
              <p class="text-sm font-medium text-slate-800 truncate">{{ userName || '—' }}</p>
            </div>
            <button
              @click="onProfile"
              class="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <User class="w-4 h-4 text-slate-400" />
              My Profile
              <ChevronRight class="w-3.5 h-3.5 text-slate-300 ml-auto" />
            </button>
            <div class="border-t border-slate-100" />
            <button
              @click="onLogout"
              class="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-rose-600 hover:bg-rose-50 transition-colors"
            >
              <LogOut class="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </Transition>
      </div>
    </header>

    <div
      v-if="menuOpen"
      class="fixed inset-0 z-40"
      @click="menuOpen = false"
    />
  </div>
</template>

<style scoped>
.drop-enter-active, .drop-leave-active { transition: all 0.15s ease; }
.drop-enter-from, .drop-leave-to { opacity: 0; transform: translateY(-4px); }
.drop-enter-to, .drop-leave-from { opacity: 1; transform: translateY(0); }
</style>
