<script setup lang="ts">
defineProps<{
  class?: string
  noPadding?: boolean
}>()
</script>

<template>
  <div
    :class="[
      'bg-white/70 backdrop-blur-md border border-slate-200/60 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)] rounded-[24px] relative overflow-hidden',
      noPadding ? '' : 'p-8',
      $props.class
    ]"
  >
    <slot />
  </div>
</template>
