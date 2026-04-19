<script setup lang="ts">
import { Button } from './button'

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
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
    <div>
      <h2 class="text-3xl font-bold tracking-tight text-foreground">{{ title }}</h2>
      <p v-if="subtitle" class="text-muted-foreground mt-1 text-sm font-medium">{{ subtitle }}</p>
    </div>
    <div class="flex items-center gap-3">
      <slot name="extra" />
      <Button
        v-if="actionLabel"
        @click="emit('action')"
        size="sm"
        class="rounded-full px-5"
      >
        {{ actionLabel }}
      </Button>
    </div>
  </div>
</template>
