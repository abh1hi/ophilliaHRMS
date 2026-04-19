<script setup lang="ts">
import { Card, CardContent } from './card'
import { Badge } from './badge'
import { Activity, ArrowUpRight, TrendingUp } from 'lucide-vue-next'

defineProps<{
  label: string
  value: string | number
  sub?: string
  glowColor?: string  // e.g. '#6366f1'
  badgeText?: string
  badgeColor?: string 
  badgeBg?: string
}>()
</script>

<template>
  <div class="relative group hover:-translate-y-2 transition-all duration-500">
    <!-- Macro Physical Container -->
    <div class="absolute inset-0 bg-slate-100 rounded-[36px] translate-y-2 opacity-20 group-hover:translate-y-4 group-hover:opacity-40 blur-xl transition-all" />
    
    <Card class="relative h-full overflow-hidden bg-white/40 backdrop-blur-2xl border-white/60 rounded-[36px] shadow-[0_32px_64px_-16px_rgba(0,0,0,0.05)] border-t border-l border-white/80">
      <!-- High-Fidelity Ambient Glow -->
      <div 
        class="absolute -top-10 -right-10 w-40 h-40 blur-[80px] rounded-full z-0 group-hover:scale-150 transition-transform duration-1000 opacity-20 group-hover:opacity-40"
        :style="{ backgroundColor: glowColor || '#6366f1' }"
      />
      
      <CardContent class="p-10 relative z-10 flex flex-col justify-between h-full">
        <div class="space-y-6">
          <div class="flex items-center justify-between">
            <div class="space-y-1">
              <p class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 leading-none">{{ label }}</p>
              <div class="w-8 h-0.5 bg-slate-900 rounded-full" />
            </div>
            <div class="w-8 h-8 rounded-xl bg-white border border-slate-100 flex items-center justify-center shadow-sm">
              <component :is="Activity" class="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-900 transition-colors" />
            </div>
          </div>

          <div class="space-y-1">
            <div class="text-6xl font-black text-slate-900 tracking-tighter uppercase leading-none">{{ value }}</div>
            <p v-if="sub" class="text-[10px] font-bold text-slate-400 uppercase tracking-widest pl-1">{{ sub }}</p>
          </div>
        </div>
        
        <div class="mt-10 flex items-center justify-between">
          <Badge v-if="badgeText" variant="outline" class="h-6 px-2.5 bg-white/30 border-white/20 backdrop-blur-md text-[9px] font-black uppercase tracking-widest shadow-sm">
            {{ badgeText }}
          </Badge>
          <div class="flex items-center gap-1.5 text-emerald-500 group-hover:translate-x-1 transition-transform">
             <TrendingUp class="w-3.5 h-3.5" />
             <span class="text-[10px] font-black uppercase tracking-widest">+12.5%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
