<script setup lang="ts">
import { ref } from 'vue'
import { UserCircleIcon, LogOutIcon, UserIcon, ChevronDownIcon } from 'lucide-vue-next'

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
  <!-- Single root keeps Vue's fragment patch algorithm happy -->
  <div>
    <header class="flex justify-between items-center mb-10">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-slate-900">{{ title || 'Overview' }}</h1>
        <p v-if="subtitle" class="text-slate-500 font-medium mt-1">{{ subtitle }}</p>
      </div>

      <div class="relative flex items-center space-x-3">
        <div class="text-right hidden sm:block">
          <p class="text-sm font-bold text-slate-900">{{ userName || '—' }}</p>
          <p class="text-xs font-medium text-slate-500 capitalize">{{ userRole?.replace('_', ' ') || 'Admin' }}</p>
        </div>

        <button
          @click="menuOpen = !menuOpen"
          class="w-12 h-12 rounded-[16px] bg-white border border-slate-200 flex items-center justify-center hover:shadow-md transition-shadow relative"
        >
          <UserCircleIcon class="w-6 h-6 text-slate-600" />
          <ChevronDownIcon
            :class="['w-3 h-3 text-slate-400 absolute bottom-1.5 right-1.5 transition-transform duration-200', menuOpen ? 'rotate-180' : '']"
          />
        </button>

        <Transition name="drop">
          <div
            v-if="menuOpen"
            class="absolute top-14 right-0 w-48 bg-white border border-slate-200/70 rounded-[16px] shadow-lg overflow-hidden z-50"
          >
            <button
              @click="onProfile"
              class="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <UserIcon class="w-4 h-4 text-slate-400" />
              My Profile
            </button>
            <div class="border-t border-slate-100" />
            <button
              @click="onLogout"
              class="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-rose-600 hover:bg-rose-50 transition-colors"
            >
              <LogOutIcon class="w-4 h-4" />
              Sign out
            </button>
          </div>
        </Transition>
      </div>
    </header>

    <!-- Click-outside: inside single root, no fragment issue -->
    <div
      v-if="menuOpen"
      class="fixed inset-0 z-40"
      @click="menuOpen = false"
    />
  </div>
</template>

<style scoped>
.drop-enter-active, .drop-leave-active { transition: all 0.15s ease; }
.drop-enter-from, .drop-leave-to { opacity: 0; transform: translateY(-6px); }
.drop-enter-to, .drop-leave-from { opacity: 1; transform: translateY(0); }
</style>
