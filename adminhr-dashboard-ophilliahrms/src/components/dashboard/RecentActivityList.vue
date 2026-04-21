<script setup lang="ts">
import { Activity, Clock, ChevronRight } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

defineProps<{
  activities: any[]
  loading?: boolean
}>()

function initials(name: string): string {
  return name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || '??'
}

const avatarColors = [
  'bg-indigo-50 text-indigo-600 border-indigo-100',
  'bg-emerald-50 text-emerald-600 border-emerald-100',
  'bg-amber-50 text-amber-600 border-amber-100',
  'bg-rose-50 text-rose-600 border-rose-100',
  'bg-slate-50 text-slate-600 border-slate-100',
]
function colorFor(i: number) { return avatarColors[i % avatarColors.length] }
</script>

<template>
  <div class="space-y-3">
    <!-- Loading Skeleton -->
    <template v-if="loading">
      <div v-for="n in 5" :key="n" class="flex items-center justify-between p-4 rounded-xl bg-white border border-slate-100 animate-pulse">
        <div class="flex items-center gap-4">
          <div class="w-10 h-10 rounded-lg bg-slate-100"></div>
          <div class="space-y-2">
            <div class="h-3 bg-slate-100 rounded-full w-40"></div>
            <div class="h-2 bg-slate-50 rounded-full w-20"></div>
          </div>
        </div>
        <div class="w-16 h-8 rounded-lg bg-slate-50"></div>
      </div>
    </template>

    <!-- Empty State -->
    <div v-else-if="!activities.length" class="flex flex-col items-center justify-center py-16 text-center rounded-xl bg-slate-50/50 border border-dashed border-slate-200">
      <div class="w-12 h-12 rounded-xl bg-white border border-slate-100 shadow-sm flex items-center justify-center mb-4">
        <Activity class="w-6 h-6 text-slate-300" />
      </div>
      <div class="space-y-1">
        <p class="text-sm font-semibold text-slate-900">No recent activity</p>
        <p class="text-xs text-slate-500">Activity logs will appear here as they happen.</p>
      </div>
    </div>

    <!-- Activity List Items -->
    <template v-else>
      <div
        v-for="(item, idx) in activities"
        :key="item.id ?? idx"
        class="group flex items-center justify-between p-4 rounded-xl bg-white border border-slate-100 hover:border-indigo-100 hover:bg-slate-50/50 transition-all duration-200 shadow-sm hover:shadow-md"
      >
        <div class="flex items-center gap-4">
          <!-- Avatar -->
          <div :class="['w-10 h-10 rounded-lg border flex items-center justify-center text-xs font-bold transition-transform group-hover:scale-105', colorFor(idx)]">
            {{ initials(item.employee_name || item.user_name || '') }}
          </div>

          <div class="space-y-0.5">
            <p class="text-sm font-semibold text-slate-900">
              {{ item.employee_name || item.user_name }}
              <span class="text-slate-500 font-normal ml-1">• {{ item.action || item.description }}</span>
            </p>
            <div class="flex items-center gap-3">
               <span class="text-[10px] font-medium text-slate-400 uppercase tracking-tight">Event: {{ item.id?.slice(0, 8) ?? 'AUTO' }}</span>
               <span class="text-[10px] font-medium text-slate-400 flex items-center gap-1">
                 <Clock class="w-3 h-3" /> {{ item.time_ago || item.created_at || 'Just now' }}
               </span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <Badge v-if="item.status" variant="outline" class="hidden sm:inline-flex capitalize text-[10px] px-2 py-0 h-5">
            {{ item.status }}
          </Badge>
          <Button
            v-if="item.requires_action"
            size="sm"
            variant="outline"
            class="h-8 text-xs font-semibold"
          >
            Review
          </Button>
          <div v-else class="w-8 h-8 rounded-full flex items-center justify-center text-slate-300 group-hover:text-indigo-500 group-hover:bg-white transition-all cursor-pointer border border-transparent group-hover:border-slate-100">
            <ChevronRight class="w-4 h-4" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
