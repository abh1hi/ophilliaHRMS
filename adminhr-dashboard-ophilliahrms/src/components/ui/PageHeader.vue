<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
  actionLabel?: string
}>()

const emit = defineEmits<{
  (e: 'action'): void
}>()
</script>

<template>
  <div class="flex items-center justify-between mb-8">
    <div>
      <h2 class="text-2xl font-bold tracking-tight text-slate-900">{{ title }}</h2>
      <p v-if="subtitle" class="text-slate-500 font-medium mt-1 text-sm">{{ subtitle }}</p>
    </div>
    <button
      v-if="actionLabel"
      @click="emit('action')"
      class="bg-slate-900 text-white rounded-full px-5 py-2.5 text-sm font-medium hover:bg-slate-800 transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 flex items-center space-x-2"
    >
      <span>{{ actionLabel }}</span>
    </button>
  </div>
</template>
