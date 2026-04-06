<script setup lang="ts">
defineProps<{
  activities: any[]
  loading?: boolean
}>()

function initials(name: string): string {
  return name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || '??'
}

const colors = ['bg-rose-100 text-rose-700', 'bg-blue-100 text-blue-700', 'bg-emerald-100 text-emerald-700', 'bg-purple-100 text-purple-700']
function colorFor(i: number) { return colors[i % colors.length] }
</script>

<template>
  <div class="space-y-3">
    <!-- Loading skeleton -->
    <template v-if="loading">
      <div v-for="n in 3" :key="n" class="flex items-center space-x-4 p-4 rounded-[16px] bg-slate-50 animate-pulse">
        <div class="w-10 h-10 rounded-[12px] bg-slate-200 shrink-0"></div>
        <div class="flex-1 space-y-2">
          <div class="h-3 bg-slate-200 rounded-full w-3/4"></div>
          <div class="h-2 bg-slate-200 rounded-full w-1/4"></div>
        </div>
      </div>
    </template>

    <!-- Empty state -->
    <div v-else-if="!activities.length" class="text-center py-10 text-slate-400 text-sm">
      No recent activity to display.
    </div>

    <!-- Activity items -->
    <template v-else>
      <div
        v-for="(item, idx) in activities"
        :key="item.id ?? idx"
        class="flex items-center justify-between p-4 rounded-[16px] bg-white/40 hover:bg-white/80 transition-colors border border-transparent hover:border-slate-100 shadow-sm hover:shadow"
      >
      <div class="flex items-center space-x-4">
        <div :class="['w-10 h-10 rounded-[12px] flex items-center justify-center font-bold shrink-0 text-sm', colorFor(idx)]">
          {{ initials(item.employee_name || item.user_name || '') }}
        </div>
        <div>
          <p class="font-semibold text-slate-900 text-sm">
            {{ item.employee_name || item.user_name }}
            <span class="font-normal text-slate-500">{{ item.action || item.description }}</span>
          </p>
          <p class="text-xs text-slate-400">{{ item.time_ago || item.created_at }}</p>
        </div>
      </div>
        <button
          v-if="item.requires_action"
          class="px-4 py-1.5 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-colors shadow-sm text-xs font-medium"
        >
          Review
        </button>
      </div>
    </template>
  </div>
</template>
