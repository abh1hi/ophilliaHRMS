<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { 
  X, 
  Pencil, 
  Clock, 
  Timer, 
  User, 
  Tag, 
  CheckCircle2, 
  Activity,
  AlertCircle,
  Monitor,
  Zap,
  CheckCircle,
  Layers,
  MessageSquare
} from 'lucide-vue-next'
import { useTaskStore } from '@/stores/task.store'
import { listSubtasks } from '@/services/calendar-tasks.service'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import SlideDrawer from '../ui/SlideDrawer.vue'
import CommentThread from './CommentThread.vue'
import type { CalendarTask } from '@/services/calendar-tasks.service'

interface Props {
  open: boolean
  task: CalendarTask | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit', task: CalendarTask): void
}>()

const store = useTaskStore()
const subtasks = ref<CalendarTask[]>([])

const statusOptions = [
  { value: 'todo', label: 'Activation Queue', icon: Clock, activeClass: 'bg-slate-900 text-white' },
  { value: 'in_progress', label: 'Active Processing', icon: Activity, activeClass: 'bg-blue-600 text-white shadow-lg shadow-blue-200' },
  { value: 'blocked', label: 'Node Latency', icon: AlertCircle, activeClass: 'bg-rose-600 text-white shadow-lg shadow-rose-200' },
  { value: 'in_review', label: 'Validation Layer', icon: Monitor, activeClass: 'bg-amber-500 text-white shadow-lg shadow-amber-200' },
  { value: 'done', label: 'Commit Complete', icon: CheckCircle2, activeClass: 'bg-emerald-600 text-white shadow-lg shadow-emerald-200' },
]

watch(() => props.task, async (t) => {
  if (t) subtasks.value = (await listSubtasks(t.id)) ?? []
  else subtasks.value = []
})

const isOverdue = computed(() => {
  if (!props.task?.due_date) return false
  return new Date(props.task.due_date) < new Date() && props.task.status !== 'done'
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

function getStatusConfig(s: string) {
  const map: Record<string, any> = {
    todo: { color: 'bg-slate-100 text-slate-600 border-slate-200', label: 'Queue' },
    in_progress: { color: 'bg-blue-100 text-blue-700 border-blue-200', label: 'Processing' },
    blocked: { color: 'bg-rose-100 text-rose-700 border-rose-200', label: 'Latency' },
    in_review: { color: 'bg-amber-100 text-amber-700 border-amber-200', label: 'Validation' },
    done: { color: 'bg-emerald-100 text-emerald-700 border-emerald-200', label: 'Committed' },
  }
  return map[s] ?? { color: 'bg-slate-100 text-slate-600', label: s }
}

function getPriorityConfig(p: string) {
  const map: Record<string, any> = {
    low: { color: 'bg-slate-100 text-slate-500 border-slate-200', label: 'L3: Auxiliary' },
    medium: { color: 'bg-blue-50 text-blue-600 border-blue-100', label: 'L2: Standard' },
    high: { color: 'bg-amber-50 text-amber-600 border-amber-100', label: 'L1: High' },
    urgent: { color: 'bg-rose-50 text-rose-600 border-rose-100', label: 'L0: Critical' },
  }
  return map[p] ?? { color: 'bg-slate-100 text-slate-500', label: p }
}

async function changeStatus(status: string) {
  if (!props.task) return
  await store.moveStatus(props.task.id, status)
}
</script>

<template>
  <SlideDrawer
    :open="open"
    title="Process Lifecycle Matrix"
    description="Extended orchestration data for the selected process node."
    side="right"
    width="max-w-xl"
    @close="emit('close')"
  >
    <template #actions>
      <Button variant="ghost" size="icon" @click="emit('edit', task!)" class="h-9 w-9 rounded-xl hover:bg-slate-100">
        <Pencil class="w-4 h-4 text-slate-500" />
      </Button>
    </template>

    <div v-if="task" class="space-y-8 py-4">
      <!-- Status & Priority Synchronization -->
      <div class="space-y-4">
        <div class="flex items-center gap-3">
          <Badge variant="outline" :class="['h-6 px-3 rounded-full text-[10px] font-black uppercase tracking-widest border transition-all', getStatusConfig(task.status).color]">
            {{ getStatusConfig(task.status).label }}
          </Badge>
          <Badge variant="outline" :class="['h-6 px-3 rounded-full text-[10px] font-black uppercase tracking-widest border transition-all', getPriorityConfig(task.priority).color]">
            {{ getPriorityConfig(task.priority).label }}
          </Badge>
        </div>
        <h2 class="text-2xl font-black text-slate-900 uppercase tracking-tight leading-tight">{{ task.title }}</h2>
      </div>

      <!-- Lifecycle Stage Modulation -->
      <div class="flex gap-2 overflow-x-auto no-scrollbar pb-2">
        <button
          v-for="s in statusOptions"
          :key="s.value"
          @click="changeStatus(s.value)"
          :class="[
            'flex items-center gap-2 px-4 py-2 rounded-full text-[10px] font-black uppercase tracking-widest transition-all whitespace-nowrap border',
            task.status === s.value 
              ? s.activeClass + ' border-transparent scale-105' 
              : 'bg-white/50 text-slate-400 border-slate-100 hover:bg-white hover:text-slate-600 hover:border-slate-200 shadow-sm'
          ]"
        >
          <component :is="s.icon" class="w-3.5 h-3.5" />
          {{ s.label }}
        </button>
      </div>

      <!-- Technical Description -->
      <div class="p-6 bg-slate-50/50 rounded-[24px] border border-slate-100 relative overflow-hidden group">
        <div class="absolute -right-8 -top-8 w-24 h-24 bg-white/40 rounded-full blur-2xl group-hover:bg-white/60 transition-colors" />
        <p class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
          <Layers class="w-3 h-3" />
          Payload Specification
        </p>
        <p v-if="task.description" class="text-sm text-slate-600 leading-relaxed font-medium">{{ task.description }}</p>
        <p v-else class="text-xs text-slate-400 italic font-medium">No descriptive metadata provided.</p>
      </div>

      <!-- Metadata Matrix -->
      <div class="grid grid-cols-3 gap-4">
        <div v-if="task.due_date" class="p-4 bg-white/40 border border-slate-100 rounded-[20px] shadow-sm">
          <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1 flex items-center gap-1.5">
            <Clock class="w-3 h-3" />
            Termination
          </p>
          <p :class="['text-[11px] font-bold uppercase tracking-tight', isOverdue ? 'text-rose-600 underline decoration-rose-200' : 'text-slate-900']">
            {{ formatDate(task.due_date) }}
          </p>
        </div>
        <div v-if="task.estimated_hours" class="p-4 bg-white/40 border border-slate-100 rounded-[20px] shadow-sm">
          <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1 flex items-center gap-1.5">
            <Timer class="w-3 h-3" />
            Allocation
          </p>
          <p class="text-[11px] font-bold text-slate-900 uppercase tracking-tight">{{ task.estimated_hours }}h Capacity</p>
        </div>
        <div v-if="task.actual_hours" class="p-4 bg-white/40 border border-slate-100 rounded-[20px] shadow-sm">
          <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1 flex items-center gap-1.5">
            <Zap class="w-3 h-3" />
            Utilization
          </p>
          <p class="text-[11px] font-bold text-slate-900 uppercase tracking-tight">{{ task.actual_hours }}h Deployed</p>
        </div>
      </div>

      <!-- Resource Assignment Matrix -->
      <div class="space-y-4">
        <p class="text-[11px] font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
          <User class="w-4 h-4 text-slate-400" />
          Resource Allocation
        </p>
        <div class="flex flex-wrap gap-3">
          <div
            v-for="a in task.assignees"
            :key="a.employee_id"
            class="flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-shadow"
          >
            <div class="w-6 h-6 rounded-lg bg-slate-900 flex items-center justify-center text-white text-[10px] font-black uppercase shadow-sm">
              {{ a.employee_id.charAt(0).toUpperCase() }}
            </div>
            <span class="text-[11px] font-bold text-slate-700 uppercase tracking-tight">{{ a.employee_id }}</span>
          </div>
          <p v-if="!task.assignees?.length" class="text-[11px] font-bold text-slate-300 uppercase italic">Awaiting Resource Enrollment</p>
        </div>
      </div>

      <!-- Taxonomy & Sub-Nodes -->
      <div v-if="task.tags?.length || subtasks.length" class="grid grid-cols-2 gap-8 pt-4 border-t border-slate-100">
        <div v-if="task.tags?.length">
          <p class="text-[11px] font-black text-slate-900 uppercase tracking-widest mb-4 flex items-center gap-2">
            <Tag class="w-4 h-4 text-slate-400" />
            Taxonomy
          </p>
          <div class="flex flex-wrap gap-2">
            <Badge v-for="tag in task.tags" :key="tag" variant="secondary" class="h-6 rounded-lg px-2 bg-indigo-50 text-indigo-700 border-indigo-100 text-[9px] font-black uppercase tracking-widest">
              {{ tag }}
            </Badge>
          </div>
        </div>
        
        <div v-if="subtasks.length">
          <p class="text-[11px] font-black text-slate-900 uppercase tracking-widest mb-4 flex items-center gap-2">
            <Layers class="w-4 h-4 text-slate-400" />
            Sub-Nodes ({{ subtasks.length }})
          </p>
          <div class="space-y-3">
            <div
              v-for="st in subtasks"
              :key="st.id"
              class="flex items-center gap-3 p-2 rounded-xl bg-slate-50/50 border border-slate-100 hover:border-slate-200 transition-colors group"
            >
              <div :class="['w-2.5 h-2.5 rounded-full flex-shrink-0 shadow-sm transition-transform group-hover:scale-125', st.status === 'done' ? 'bg-emerald-500' : 'bg-slate-200']" />
              <span :class="['text-[11px] font-bold uppercase tracking-tight', st.status === 'done' ? 'line-through text-slate-300' : 'text-slate-600']">{{ st.title }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Communication Thread -->
      <div class="pt-8 border-t border-slate-100 space-y-6">
        <p class="text-[11px] font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
          <MessageSquare class="w-4 h-4 text-slate-400" />
          Synchronized Communication
        </p>
        <div class="rounded-[28px] overflow-hidden border border-slate-100 bg-white/30 backdrop-blur-sm p-4">
           <CommentThread :task-id="task.id" />
        </div>
      </div>
    </div>
  </SlideDrawer>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>

<style scoped>
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.25s; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
</style>
