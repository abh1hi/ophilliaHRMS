<script setup lang="ts">
import { Card, CardContent } from './card'
import { Badge } from './badge'
import { Activity, TrendingUp } from 'lucide-vue-next'

defineProps<{
  label: string
  value: string | number
  sub?: string
  glowColor?: string  // Kept for prop compatibility but will be used subtly
  badgeText?: string
}>()
</script>

<template>
  <Card class="overflow-hidden border-slate-200 shadow-sm hover:shadow-md transition-all duration-300">
    <CardContent class="p-6">
      <div class="flex items-center justify-between mb-4">
        <div class="space-y-1">
          <p class="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{{ label }}</p>
          <div class="w-6 h-0.5 rounded-full" :style="{ backgroundColor: glowColor || '#6366f1' }" />
        </div>
        <div class="w-9 h-9 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center">
          <Activity class="w-4 h-4 text-slate-400" />
        </div>
      </div>

      <div class="space-y-1">
        <div class="text-4xl font-bold text-slate-900 tracking-tight">{{ value }}</div>
        <p v-if="sub" class="text-xs text-slate-500 font-medium">{{ sub }}</p>
      </div>

      <div class="mt-6 flex items-center justify-between">
        <Badge v-if="badgeText" variant="secondary" class="text-[10px] px-2 py-0 h-5 font-semibold">
          {{ badgeText }}
        </Badge>
        <div v-else class="flex items-center gap-1.5 text-emerald-600">
           <TrendingUp class="w-3.5 h-3.5" />
           <span class="text-xs font-semibold">+12.5%</span>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
