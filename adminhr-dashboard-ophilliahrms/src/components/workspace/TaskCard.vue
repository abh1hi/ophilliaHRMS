<template>
  <div
    class="bg-white rounded-xl border border-slate-200 p-3 shadow-sm hover:shadow-md hover:border-slate-300 transition-all cursor-pointer group"
    @click="emit('click', task)"
  >
    <!-- Priority indicator -->
    <div class="flex items-start justify-between gap-2 mb-2">
      <span :class="['inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium', priorityClass]">
        <component :is="priorityIcon" class="w-3 h-3" />
        {{ task.priority }}
      </span>
      <span v-if="task.due_date" :class="['text-xs font-medium', isOverdue ? 'text-red-500' : 'text-slate-400']">
        {{ formatDate(task.due_date) }}
      </span>
    </div>

    <!-- Title -->
    <p class="text-sm font-medium text-slate-800 leading-snug mb-2 line-clamp-2">{{ task.title }}</p>

    <!-- Tags -->
    <div v-if="task.tags?.length" class="flex flex-wrap gap-1 mb-2">
      <span
        v-for="tag in task.tags.slice(0, 3)"
        :key="tag"
        class="px-1.5 py-0.5 bg-slate-100 text-slate-600 text-xs rounded"
      >
        {{ tag }}
      </span>
    </div>

    <!-- Footer: assignees + comments count -->
    <div class="flex items-center justify-between mt-2">
      <div class="flex -space-x-1">
        <div
          v-for="(a, i) in task.assignees?.slice(0, 4)"
          :key="a.employee_id"
          :style="{ zIndex: 4 - i }"
          class="w-6 h-6 rounded-full bg-slate-300 border-2 border-white flex items-center justify-center text-xs font-medium text-slate-600"
          :title="a.employee_id"
        >
          {{ a.employee_id.charAt(0).toUpperCase() }}
        </div>
        <div
          v-if="(task.assignees?.length ?? 0) > 4"
          class="w-6 h-6 rounded-full bg-slate-200 border-2 border-white flex items-center justify-center text-xs text-slate-500"
        >
          +{{ task.assignees!.length - 4 }}
        </div>
      </div>
      <div v-if="task.subtask_count" class="flex items-center gap-1 text-xs text-slate-400">
        <ListIcon class="w-3 h-3" />
        {{ task.subtask_count }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowDownIcon, ArrowRightIcon, ArrowUpIcon, ZapIcon, ListIcon } from 'lucide-vue-next'
import type { CalendarTask } from '@/services/calendar-tasks.service'

interface Props {
  task: CalendarTask
}

const props = defineProps<Props>()
const emit = defineEmits<{ (e: 'click', task: CalendarTask): void }>()

const priorityMap: Record<string, { class: string; icon: unknown }> = {
  low:    { class: 'bg-slate-100 text-slate-500', icon: ArrowDownIcon },
  medium: { class: 'bg-blue-100 text-blue-600',   icon: ArrowRightIcon },
  high:   { class: 'bg-orange-100 text-orange-600', icon: ArrowUpIcon },
  urgent: { class: 'bg-red-100 text-red-600',      icon: ZapIcon },
}

const priorityClass = computed(() => priorityMap[props.task.priority]?.class ?? 'bg-slate-100 text-slate-500')
const priorityIcon = computed(() => priorityMap[props.task.priority]?.icon ?? ArrowRightIcon)

const isOverdue = computed(() => {
  if (!props.task.due_date) return false
  return new Date(props.task.due_date) < new Date() && props.task.status !== 'done'
})

function formatDate(iso: string) {
  const d = new Date(iso)
  const now = new Date()
  const diff = Math.round((d.getTime() - now.getTime()) / 86400000)
  if (diff === 0) return 'Today'
  if (diff === 1) return 'Tomorrow'
  if (diff === -1) return 'Yesterday'
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
</script>
