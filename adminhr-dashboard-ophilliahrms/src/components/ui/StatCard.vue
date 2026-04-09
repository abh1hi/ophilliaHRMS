<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  sub?: string
  glowColor?: string  // tailwind bg class e.g. 'bg-emerald-100/50'
  badgeText?: string
  badgeColor?: string // tailwind text class e.g. 'text-emerald-600'
  badgeBg?: string    // tailwind bg class e.g. 'bg-emerald-100/80'
}>()
</script>

<template>
  <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)] rounded-[24px] p-8 relative overflow-hidden group hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.08)] transition-shadow duration-500">
    <!-- Glow orb -->
    <div :class="['absolute -top-6 -right-6 w-24 h-24 blur-[30px] rounded-full z-0 group-hover:scale-150 transition-transform duration-700', glowColor || 'bg-slate-100/50']"></div>
    <div class="relative z-10">
      <h3 class="text-slate-500 font-semibold mb-2 text-sm">{{ label }}</h3>
      <div class="text-4xl font-bold text-slate-900">{{ value }}</div>
      <div v-if="badgeText || sub" class="mt-4 flex items-center text-sm font-medium" :class="badgeColor || 'text-slate-500'">
        <span v-if="badgeText" :class="['px-2 py-0.5 rounded-md mr-2', badgeBg || 'bg-slate-100/80']">{{ badgeText }}</span>
        <span v-if="sub">{{ sub }}</span>
      </div>
    </div>
  </div>
</template>
