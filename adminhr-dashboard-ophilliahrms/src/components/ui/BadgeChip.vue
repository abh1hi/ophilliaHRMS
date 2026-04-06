<script setup lang="ts">
defineProps<{
  status: 'active' | 'inactive' | 'terminated' | string
}>()

const map: Record<string, { label: string; classes: string }> = {
  active:     { label: 'Active',     classes: 'bg-emerald-100 text-emerald-700' },
  inactive:   { label: 'Inactive',   classes: 'bg-slate-100 text-slate-600'    },
  terminated: { label: 'Terminated', classes: 'bg-rose-100 text-rose-700'      },
}

const get = (s: string) => map[s] ?? { label: s, classes: 'bg-slate-100 text-slate-600' }
</script>

<template>
  <span :class="['inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold', get(status).classes]">
    {{ get(status).label }}
  </span>
</template>
