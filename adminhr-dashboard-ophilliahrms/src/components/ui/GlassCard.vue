<script setup lang="ts">
import { Card, CardContent } from './card'

defineProps<{
  class?: string
  noPadding?: boolean
}>()
</script>

<template>
  <Card :class="['overflow-hidden', $props.class]">
    <CardContent :class="[noPadding ? 'p-0' : 'p-6 sm:p-8']">
      <slot />
    </CardContent>
  </Card>
</template>
