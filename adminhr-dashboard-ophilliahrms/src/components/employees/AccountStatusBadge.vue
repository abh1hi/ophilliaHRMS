<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '../ui/badge'

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
    return { label: 'Invite Expired', class: 'bg-amber-100 text-amber-700 hover:bg-amber-100/80 border-transparent shadow-none' }
  }
  const map: Record<string, { label: string; class: string }> = {
    not_registered: { label: 'Not Registered', class: 'bg-muted text-muted-foreground hover:bg-muted/80 border-transparent shadow-none' },
    invited:        { label: 'Invite Sent',     class: 'bg-amber-100 text-amber-700 hover:bg-amber-100/80 border-transparent shadow-none' },
    active:         { label: 'Active',           class: 'bg-emerald-100 text-emerald-700 hover:bg-emerald-100/80 border-transparent shadow-none' },
    suspended:      { label: 'Suspended',        class: 'bg-destructive/10 text-destructive hover:bg-destructive/20 border-transparent shadow-none' },
  }
  return map[props.status ?? ''] ?? { label: props.status ?? '—', class: 'bg-muted text-muted-foreground border-transparent shadow-none' }
})
</script>

<template>
  <Badge :class="['rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider', badge.class]">
    {{ badge.label }}
  </Badge>
</template>
