<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open && task" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/40" @click="emit('close')" />
        <div class="relative w-full max-w-xl bg-white h-full shadow-xl flex flex-col">
          <!-- Header -->
          <div class="flex items-start justify-between px-6 py-4 border-b border-slate-200">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span :class="['px-2 py-0.5 rounded text-xs font-medium capitalize', statusClass(task.status)]">
                  {{ task.status.replace('_', ' ') }}
                </span>
                <span :class="['px-2 py-0.5 rounded text-xs font-medium capitalize', priorityClass(task.priority)]">
                  {{ task.priority }}
                </span>
              </div>
              <h2 class="text-lg font-semibold text-slate-800 truncate">{{ task.title }}</h2>
            </div>
            <div class="flex items-center gap-1 ml-3 flex-shrink-0">
              <button @click="emit('edit', task)" class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500">
                <PencilIcon class="w-4 h-4" />
              </button>
              <button @click="emit('close')" class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500">
                <XIcon class="w-5 h-5" />
              </button>
            </div>
          </div>

          <!-- Status selector -->
          <div class="px-6 py-3 border-b border-slate-100 flex gap-1.5 overflow-x-auto">
            <button
              v-for="s in statusOptions"
              :key="s.value"
              @click="changeStatus(s.value)"
              :class="[
                'px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors',
                task.status === s.value ? s.activeClass : 'bg-slate-100 text-slate-500 hover:bg-slate-200',
              ]"
            >
              {{ s.label }}
            </button>
          </div>

          <!-- Body -->
          <div class="flex-1 overflow-y-auto">
            <!-- Description -->
            <div class="px-6 py-4 border-b border-slate-100">
              <p v-if="task.description" class="text-sm text-slate-600 leading-relaxed">{{ task.description }}</p>
              <p v-else class="text-sm text-slate-400 italic">No description.</p>
            </div>

            <!-- Meta -->
            <div class="px-6 py-4 border-b border-slate-100 grid grid-cols-2 gap-3 text-sm">
              <div v-if="task.due_date">
                <p class="text-xs text-slate-400 mb-0.5">Due</p>
                <p :class="['font-medium', isOverdue ? 'text-red-500' : 'text-slate-700']">
                  {{ formatDate(task.due_date) }}
                </p>
              </div>
              <div v-if="task.estimated_hours">
                <p class="text-xs text-slate-400 mb-0.5">Estimated</p>
                <p class="font-medium text-slate-700">{{ task.estimated_hours }}h</p>
              </div>
              <div v-if="task.actual_hours">
                <p class="text-xs text-slate-400 mb-0.5">Logged</p>
                <p class="font-medium text-slate-700">{{ task.actual_hours }}h</p>
              </div>
            </div>

            <!-- Assignees -->
            <div class="px-6 py-4 border-b border-slate-100">
              <p class="text-xs font-medium text-slate-500 mb-2">Assignees</p>
              <div class="flex flex-wrap gap-2">
                <div
                  v-for="a in task.assignees"
                  :key="a.employee_id"
                  class="flex items-center gap-1.5 px-2 py-1 bg-slate-100 rounded-full text-xs text-slate-700"
                >
                  <div class="w-4 h-4 rounded-full bg-slate-400 flex items-center justify-center text-white text-xs">
                    {{ a.employee_id.charAt(0).toUpperCase() }}
                  </div>
                  {{ a.employee_id }}
                </div>
                <span v-if="!task.assignees?.length" class="text-xs text-slate-400">Unassigned</span>
              </div>
            </div>

            <!-- Tags -->
            <div v-if="task.tags?.length" class="px-6 py-4 border-b border-slate-100">
              <p class="text-xs font-medium text-slate-500 mb-2">Tags</p>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="tag in task.tags" :key="tag" class="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                  {{ tag }}
                </span>
              </div>
            </div>

            <!-- Subtasks -->
            <div v-if="subtasks.length" class="px-6 py-4 border-b border-slate-100">
              <p class="text-xs font-medium text-slate-500 mb-2">Subtasks ({{ subtasks.length }})</p>
              <div class="space-y-1.5">
                <div
                  v-for="st in subtasks"
                  :key="st.id"
                  class="flex items-center gap-2 text-sm"
                >
                  <div :class="['w-3 h-3 rounded-full flex-shrink-0', st.status === 'done' ? 'bg-green-400' : 'bg-slate-200']" />
                  <span :class="[st.status === 'done' ? 'line-through text-slate-400' : 'text-slate-700']">{{ st.title }}</span>
                </div>
              </div>
            </div>

            <!-- Comments -->
            <div class="px-6 py-4">
              <p class="text-xs font-medium text-slate-500 mb-3">Comments</p>
              <CommentThread :task-id="task.id" />
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { XIcon, PencilIcon } from 'lucide-vue-next'
import { useTaskStore } from '@/stores/task.store'
import { listSubtasks } from '@/services/calendar-tasks.service'
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
  { value: 'todo', label: 'To Do', activeClass: 'bg-slate-700 text-white' },
  { value: 'in_progress', label: 'In Progress', activeClass: 'bg-blue-600 text-white' },
  { value: 'blocked', label: 'Blocked', activeClass: 'bg-red-500 text-white' },
  { value: 'in_review', label: 'In Review', activeClass: 'bg-yellow-500 text-white' },
  { value: 'done', label: 'Done', activeClass: 'bg-green-600 text-white' },
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
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function statusClass(s: string) {
  const map: Record<string, string> = {
    todo: 'bg-slate-100 text-slate-600',
    in_progress: 'bg-blue-100 text-blue-700',
    blocked: 'bg-red-100 text-red-700',
    in_review: 'bg-yellow-100 text-yellow-700',
    done: 'bg-green-100 text-green-700',
    cancelled: 'bg-slate-200 text-slate-500',
  }
  return map[s] ?? 'bg-slate-100 text-slate-600'
}

function priorityClass(p: string) {
  const map: Record<string, string> = {
    low: 'bg-slate-100 text-slate-500',
    medium: 'bg-blue-100 text-blue-600',
    high: 'bg-orange-100 text-orange-600',
    urgent: 'bg-red-100 text-red-600',
  }
  return map[p] ?? 'bg-slate-100 text-slate-500'
}

async function changeStatus(status: string) {
  if (!props.task) return
  await store.moveStatus(props.task.id, status)
}
</script>

<style scoped>
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.25s; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
</style>
