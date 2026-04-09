<script setup lang="ts">
import { watch } from 'vue'
import { XIcon } from 'lucide-vue-next'

const props = defineProps<{
  open: boolean
  title: string
  subtitle?: string
  width?: string // e.g. 'max-w-xl'
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

// Lock body scroll when open
watch(() => props.open, (val) => {
  document.body.style.overflow = val ? 'hidden' : ''
})
</script>

<template>
  <Teleport to="body">
    <!-- Overlay -->
    <Transition name="fade">
      <div
        v-if="open"
        class="fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-40"
        @click="emit('close')"
      />
    </Transition>

    <!-- Drawer Panel -->
    <Transition name="slide-right">
      <div
        v-if="open"
        :class="['fixed top-0 right-0 h-full z-50 flex flex-col bg-white/90 backdrop-blur-xl border-l border-slate-200/60 shadow-[−8px_0_40px_-4px_rgba(0,0,0,0.1)]', width || 'w-full max-w-2xl']"
      >
        <!-- Header -->
        <div class="flex items-center justify-between p-8 border-b border-slate-200/60 shrink-0">
          <div>
            <h2 class="text-xl font-bold text-slate-900">{{ title }}</h2>
            <p v-if="subtitle" class="text-sm text-slate-500 mt-0.5">{{ subtitle }}</p>
          </div>
          <button
            @click="emit('close')"
            class="p-2.5 rounded-[12px] border border-slate-200 hover:bg-slate-50 transition-colors active:scale-95"
          >
            <XIcon class="w-5 h-5 text-slate-600" />
          </button>
        </div>

        <!-- Scrollable Content -->
        <div class="flex-1 overflow-y-auto p-8">
          <slot />
        </div>

        <!-- Footer -->
        <div v-if="$slots.footer" class="shrink-0 border-t border-slate-200/60 p-6">
          <slot name="footer" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-right-enter-active, .slide-right-leave-active { transition: transform 0.35s cubic-bezier(0.4,0,0.2,1); }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(100%); }
</style>
