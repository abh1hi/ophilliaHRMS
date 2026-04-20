<script setup lang="ts">
import { type Component } from 'vue'
import { Button } from '@/components/ui/button'

defineProps<{
  icon?: Component
  title: string
  description?: string
  actionLabel?: string
}>()

const emit = defineEmits<{ (e: 'action'): void }>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 px-4 text-center">
    <div class="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
      <component v-if="icon" :is="icon" class="w-7 h-7 text-slate-400" />
      <span v-else class="text-2xl">📭</span>
    </div>
    <h3 class="text-sm font-semibold text-slate-800 mb-1">{{ title }}</h3>
    <p v-if="description" class="text-xs text-slate-500 max-w-xs leading-relaxed mb-5">{{ description }}</p>
    <Button
      v-if="actionLabel"
      @click="emit('action')"
      class="rounded-xl bg-slate-900 text-white hover:bg-slate-800 h-9 text-[11px] font-bold uppercase tracking-widest px-5"
    >
      {{ actionLabel }}
    </Button>
  </div>
</template>
