<template>
  <span :class="[statusColor, sizeClasses, 'rounded-full font-semibold inline-block']">
    {{ statusLabel }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
  size?: 'small' | 'medium' | 'large'
}>()

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    DRAFT: 'Draft',
    REVIEW: 'Under Review',
    APPROVED: 'Approved',
    PROCESSING: 'Processing',
    COMPLETED: 'Completed',
    PAID: 'Paid',
    LOCKED: 'Locked',
    FAILED: 'Failed',
  }
  return labels[props.status] || props.status
})

const statusColor = computed(() => {
  const colors: Record<string, string> = {
    DRAFT: 'bg-slate-100 text-slate-900',
    REVIEW: 'bg-blue-100 text-blue-900',
    APPROVED: 'bg-green-100 text-green-900',
    PROCESSING: 'bg-yellow-100 text-yellow-900',
    COMPLETED: 'bg-green-100 text-green-900',
    PAID: 'bg-green-100 text-green-900',
    LOCKED: 'bg-slate-900 text-white',
    FAILED: 'bg-red-100 text-red-900',
  }
  return colors[props.status] || 'bg-slate-100 text-slate-900'
})

const sizeClasses = computed(() => {
  const sizes: Record<string, string> = {
    small: 'px-2 py-1 text-xs',
    medium: 'px-3 py-1 text-sm',
    large: 'px-4 py-2 text-base',
  }
  return sizes[props.size || 'medium']
})
</script>
