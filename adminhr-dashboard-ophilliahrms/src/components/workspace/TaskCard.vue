<script setup lang="ts">
import { computed } from 'vue'
import { 
  ArrowDown, 
  ArrowRight, 
  ArrowUp, 
  Zap, 
  List, 
  Calendar,
  MoreVertical,
  Activity,
  CheckCircle2,
  Clock,
  AlertCircle
} from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui/tooltip'
import type { CalendarTask } from '@/services/calendar-tasks.service'

interface Props {
  task: CalendarTask
}

const props = defineProps<Props>()
const emit = defineEmits<{ (e: 'click', task: CalendarTask): void }>()

const priorityConfig = {
  low: {
    label: 'Low',
    icon: ArrowDown,
    color: 'bg-slate-100/80 text-slate-500 border-slate-200/50',
    iconColor: 'text-slate-400'
  },
  medium: {
    label: 'Medium',
    icon: ArrowRight,
    color: 'bg-blue-50/80 text-blue-600 border-blue-100/50',
    iconColor: 'text-blue-500'
  },
  high: {
    label: 'High',
    icon: ArrowUp,
    color: 'bg-amber-50/80 text-amber-600 border-amber-100/50',
    iconColor: 'text-amber-500'
  },
  urgent: {
    label: 'Urgent',
    icon: Zap,
    color: 'bg-rose-50/80 text-rose-600 border-rose-100/50',
    iconColor: 'text-rose-500'
  }
}

const pConfig = computed(() => priorityConfig[props.task.priority] || priorityConfig.low)

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

<template>
  <div
    class="relative group bg-white/60 backdrop-blur-md border border-white/20 rounded-[22px] p-4 shadow-[0_4px_12px_-3px_rgba(0,0,0,0.04)] hover:shadow-[0_12px_24px_-4px_rgba(0,0,0,0.08)] hover:bg-white/80 hover:-translate-y-1 transition-all duration-300 cursor-pointer overflow-hidden border-b-2"
    @click="emit('click', task)"
  >
    <!-- Card Decoration -->
    <div class="absolute -right-4 -top-4 w-12 h-12 rounded-full bg-slate-100/20 blur-xl group-hover:bg-slate-200/20 transition-colors" />

    <!-- Metadata Layer -->
    <div class="flex items-start justify-between gap-3 mb-4">
      <Badge 
        variant="secondary" 
        :class="['h-5 rounded-full px-2 text-[9px] font-black uppercase tracking-widest border transition-colors', pConfig.color]"
      >
        <component :is="pConfig.icon" class="w-2.5 h-2.5 mr-1" :class="pConfig.iconColor" />
        {{ pConfig.label }}
      </Badge>
      
      <div v-if="task.due_date" class="flex items-center gap-1.5 py-0.5 px-2 rounded-lg bg-slate-50/50 border border-slate-100/50">
        <Clock class="w-2.5 h-2.5" :class="isOverdue ? 'text-rose-500' : 'text-slate-400'" />
        <span class="text-[9px] font-bold uppercase tracking-tight" :class="isOverdue ? 'text-rose-600' : 'text-slate-500'">
          {{ formatDate(task.due_date) }}
        </span>
      </div>
    </div>

    <!-- Payload Identification -->
    <h5 class="text-[13px] font-bold text-slate-900 leading-snug mb-3 line-clamp-2 uppercase tracking-tight group-hover:text-black transition-colors">
      {{ task.title }}
    </h5>

    <!-- Taxonomy Tokens -->
    <div v-if="task.tags?.length" class="flex flex-wrap gap-1.5 mb-4">
      <Badge
        v-for="tag in task.tags.slice(0, 3)"
        :key="tag"
        variant="outline"
        class="h-5 rounded-md px-1.5 bg-white/50 text-slate-500 text-[8px] font-black uppercase tracking-widest border-slate-100/60"
      >
        {{ tag }}
      </Badge>
    </div>

    <!-- Resource Allocation & Metrics -->
    <div class="flex items-center justify-between mt-autp pt-3 border-t border-slate-100/30">
      <div class="flex -space-x-2">
        <TooltipProvider v-for="(a, i) in task.assignees?.slice(0, 4)" :key="a.employee_id">
          <Tooltip>
            <TooltipTrigger as-child>
              <div
                :style="{ zIndex: 10 - i }"
                class="w-7 h-7 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-[10px] font-black text-slate-900 shadow-sm transition-transform hover:scale-110 hover:-translate-y-0.5"
              >
                {{ a.employee_id.charAt(0).toUpperCase() }}
              </div>
            </TooltipTrigger>
            <TooltipContent class="bg-slate-900 text-white border-none py-1.5 px-3 rounded-lg">
              <p class="text-[10px] font-bold uppercase tracking-widest text-center">{{ a.employee_id }}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
        
        <div
          v-if="(task.assignees?.length ?? 0) > 4"
          class="w-7 h-7 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-center text-[9px] font-bold text-slate-400 shadow-sm"
        >
          +{{ task.assignees!.length - 4 }}
        </div>
      </div>

      <div v-if="task.subtask_count" class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50/50 border border-slate-100/50">
        <List class="w-3 h-3 text-slate-400" />
        <span class="text-[10px] font-black text-slate-500 tracking-widest">{{ task.subtask_count }}</span>
      </div>
    </div>
  </div>
</template>
