<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useCommandPaletteStore } from './stores/commandPalette.store'
import CommandPalette from './components/ui/CommandPalette.vue'
import { useRouter } from 'vue-router'

const palette = useCommandPaletteStore()
const router = useRouter()

function onKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    palette.toggle()
  }
}

function handleNavigate(tab: string) {
  if (tab === 'payroll') {
    router.push('/payroll')
  } else {
    router.push({ path: '/dashboard', query: { tab } })
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="min-h-screen bg-slate-50 relative overflow-hidden text-slate-900 font-sans selection:bg-rose-200/50">
    <CommandPalette @navigate="handleNavigate" />
    <!-- Ambient glowing orbs -->
    <div class="fixed -top-20 -left-20 w-[40%] h-[40%] bg-rose-100/40 blur-[120px] rounded-full pointer-events-none z-0"></div>
    <div class="fixed top-1/2 -right-20 w-[30%] h-[30%] bg-blue-100/40 blur-[100px] rounded-full pointer-events-none z-0"></div>
    <div class="fixed -bottom-20 left-1/4 w-[35%] h-[40%] bg-purple-100/30 blur-[120px] rounded-full pointer-events-none z-0"></div>
    
    <!-- Main Content App Context -->
    <div class="relative z-10 w-full min-h-screen">
      <router-view />
    </div>
  </div>
</template>
