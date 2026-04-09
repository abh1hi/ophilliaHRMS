<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status?: string | null
  expiresAt?: string | null
}>()

const isExpired = computed(() => {
  if (props.status !== 'invited' || !props.expiresAt) return false
  return new Date(props.expiresAt) < new Date()
})

const badge = computed(() => {
  if (props.status === 'invited' && isExpired.value) {
    return { label: 'Invite Expired', classes: 'bg-amber-50 text-amber-700 border border-amber-300' }
  }
  const map: Record<string, { label: string; classes: string }> = {
    not_registered: { label: 'Not Registered', classes: 'bg-slate-100 text-slate-500' },
    invited:        { label: 'Invite Sent',     classes: 'bg-amber-100 text-amber-700' },
    active:         { label: 'Active',           classes: 'bg-emerald-100 text-emerald-700' },
    suspended:      { label: 'Suspended',        classes: 'bg-rose-100 text-rose-700' },
  }
  return map[props.status ?? ''] ?? { label: props.status ?? '—', classes: 'bg-slate-100 text-slate-500' }
})
</script>

<template>
  <span :class="['inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold', badge.classes]">
    {{ badge.label }}
  </span>
</template>
