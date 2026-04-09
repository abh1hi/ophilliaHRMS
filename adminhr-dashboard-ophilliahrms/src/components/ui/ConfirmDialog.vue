<script setup lang="ts">
import { AlertTriangleIcon } from 'lucide-vue-next'

defineProps<{
  open: boolean
  title?: string
  message?: string
  confirmLabel?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="open" class="fixed inset-0 bg-slate-900/30 backdrop-blur-sm z-50 flex items-center justify-center p-6">
        <div class="bg-white/90 backdrop-blur-xl border border-slate-200/60 rounded-[24px] shadow-[0_20px_60px_-10px_rgba(0,0,0,0.15)] p-8 max-w-sm w-full">
          <div class="w-12 h-12 bg-rose-100 rounded-[14px] flex items-center justify-center mb-6">
            <AlertTriangleIcon class="w-6 h-6 text-rose-600" />
          </div>
          <h3 class="text-lg font-bold text-slate-900 mb-2">{{ title || 'Are you sure?' }}</h3>
          <p class="text-slate-500 text-sm mb-8">{{ message || 'This action cannot be undone.' }}</p>
          <div class="flex items-center space-x-3">
            <button
              @click="emit('cancel')"
              class="flex-1 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full py-2.5 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              @click="emit('confirm')"
              :disabled="loading"
              class="flex-1 bg-rose-600 hover:bg-rose-700 text-white rounded-full py-2.5 font-medium transition-colors disabled:opacity-60"
            >
              {{ loading ? 'Deleting...' : (confirmLabel || 'Delete') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
