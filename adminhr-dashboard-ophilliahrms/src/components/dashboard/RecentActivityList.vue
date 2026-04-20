<script setup lang="ts">
import { Activity, Clock, ChevronRight, Zap } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

defineProps<{
  activities: any[]
  loading?: boolean
}>()

function initials(name: string): string {
  return name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || '??'
}

const colors = [
  'bg-slate-50 text-slate-400 border-slate-100',
  'bg-slate-50 text-slate-400 border-slate-100'
]
function colorFor(i: number) { return colors[i % colors.length] }
</script>

<template>
  <div class="space-y-4">
    <!-- Terminal Latency: Loading Skeleton -->
    <template v-if="loading">
      <div v-for="n in 5" :key="n" class="flex items-center justify-between p-6 rounded-[28px] bg-white/20 border border-white/40 animate-pulse">
        <div class="flex items-center gap-6">
          <div class="w-14 h-14 rounded-[20px] bg-slate-100"></div>
          <div class="space-y-3">
            <div class="h-3 bg-slate-100 rounded-full w-48"></div>
            <div class="h-2 bg-slate-50 rounded-full w-24"></div>
          </div>
        </div>
        <div class="w-20 h-8 rounded-full bg-slate-50"></div>
      </div>
    </template>

    <!-- Ingestion Void: Empty State -->
    <div v-else-if="!activities.length" class="flex flex-col items-center justify-center py-24 text-center rounded-[40px] bg-slate-50/30 border border-dashed border-slate-200 group">
      <div class="relative mb-6">
         <div class="absolute inset-0 bg-slate-100 rounded-full blur-2xl opacity-40 group-hover:opacity-60 transition-opacity" />
         <div class="relative w-16 h-16 rounded-3xl bg-white border border-slate-100 shadow-sm flex items-center justify-center group-hover:scale-110 transition-transform">
            <Activity class="w-8 h-8 text-slate-200" />
         </div>
      </div>
      <div class="space-y-1">
        <p class="text-[12px] font-black text-slate-300 uppercase tracking-[0.2em]">No recent activity</p>
        <p class="text-[10px] text-slate-400 font-medium uppercase tracking-widest">No activity items to display</p>
      </div>
    </div>

    <!-- Active Stream: Item Logic -->
    <template v-else>
      <div
        v-for="(item, idx) in activities"
        :key="item.id ?? idx"
        class="group relative flex items-center justify-between p-5 rounded-[28px] bg-white/40 backdrop-blur-xl border border-white/40 hover:bg-white/60 hover:border-white/80 transition-all duration-500 hover:shadow-[0_20px_40px_-12px_rgba(0,0,0,0.03)] hover:-translate-y-1"
      >
        <div class="flex items-center gap-6">
          <!-- Physical Avatar Node -->
          <div class="relative">
            <div class="absolute inset-0 bg-slate-900 rounded-[22px] blur-lg opacity-0 group-hover:opacity-10 transition-opacity" />
            <div :class="['relative w-14 h-14 rounded-[22px] border flex items-center justify-center text-[12px] font-black transition-all group-hover:scale-105 group-hover:bg-white', colorFor(idx)]">
              {{ initials(item.employee_name || item.user_name || '') }}
            </div>
            <div class="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-white border border-slate-50 shadow-sm flex items-center justify-center">
              <Zap class="w-3 h-3 text-indigo-400" />
            </div>
          </div>

          <div class="space-y-1">
            <p class="text-[12px] font-black text-slate-900 uppercase tracking-tight">
              {{ item.employee_name || item.user_name }}
              <span class="text-slate-400 font-bold ml-1 opacity-60">/ {{ item.action || item.description }}</span>
            </p>
            <div class="flex items-center gap-2">
               <Badge variant="outline" class="h-4 px-1.5 bg-white/40 border-black/5 text-[7px] font-black uppercase tracking-tighter">Event ID: {{ item.id?.slice(0, 8) ?? 'AUTO' }}</Badge>
               <span class="text-[9px] font-bold text-slate-300 uppercase tracking-widest flex items-center gap-1">
                 <Clock class="w-2.5 h-2.5" /> {{ item.time_ago || item.created_at || 'Just now' }}
               </span>
            </div>
          </div>
        </div>

        <Button
          v-if="item.requires_action"
          class="h-10 rounded-full px-6 bg-slate-900 text-white hover:bg-black shadow-lg shadow-slate-200/50 text-[10px] font-black uppercase tracking-widest transition-all"
        >
          View
        </Button>
        <div v-else class="pr-2 opacity-0 group-hover:opacity-100 transition-opacity">
           <div class="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center hover:bg-white border border-transparent hover:border-slate-100 transition-all cursor-pointer">
              <ChevronRight class="w-4 h-4 text-slate-400" />
           </div>
        </div>
      </div>
    </template>
  </div>
</template>
