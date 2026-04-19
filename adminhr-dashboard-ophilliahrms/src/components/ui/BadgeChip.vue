<script setup lang="ts">
import { Badge } from './badge'

defineProps<{
  status: 'active' | 'inactive' | 'terminated' | string
}>()

const map: Record<string, { label: string; class: string }> = {
  active:     { label: 'Active',     class: 'bg-emerald-100 text-emerald-700 hover:bg-emerald-100/80 border-transparent' },
  inactive:   { label: 'Inactive',   class: 'bg-muted text-muted-foreground hover:bg-muted/80 border-transparent'        },
  terminated: { label: 'Terminated', class: 'bg-destructive/10 text-destructive hover:bg-destructive/20 border-transparent'   },
}

const get = (s: string) => map[s] ?? { label: s, class: 'bg-muted text-muted-foreground hover:bg-muted/80 border-transparent' }
</script>

<template>
  <Badge :class="['rounded-full px-2.5 py-0.5 font-semibold text-[10px] uppercase tracking-wider shadow-none', get(status).class]">
    {{ get(status).label }}
  </Badge>
</template>
