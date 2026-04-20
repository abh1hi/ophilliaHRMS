<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { 
  Plus, 
  Layers, 
  Activity, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  MoreVertical,
  Kanban,
  Zap,
  Box,
  Monitor
} from 'lucide-vue-next'
import { useWorkspaceStore } from '@/stores/workspace.store'
import { useTaskStore } from '@/stores/task.store'
import { Button } from '@/components/ui/button'
import FormSelect from '../ui/FormSelect.vue'
import TaskCard from './TaskCard.vue'
import TaskPanel from './TaskPanel.vue'
import TaskDetailDrawer from './TaskDetailDrawer.vue'
import type { CalendarTask } from '@/services/calendar-tasks.service'

const workspaceStore = useWorkspaceStore()
const store = useTaskStore()

const activeWorkspaceId = ref('')
const filterStatus = ref('')
const filterPriority = ref('')
const showCreate = ref(false)
const showEdit = ref(false)
const showDetail = ref(false)
const editTask = ref<CalendarTask | null>(null)
const draggedTaskId = ref<string | null>(null)

const displayColumns = [
  { key: 'todo',        label: 'To Do',       icon: Clock,        accent: 'bg-slate-400' },
  { key: 'in_progress', label: 'In Progress', icon: Activity,     accent: 'bg-blue-500' },
  { key: 'in_review',   label: 'In Review',   icon: Monitor,      accent: 'bg-yellow-500' },
  { key: 'blocked',     label: 'Blocked',     icon: AlertCircle,  accent: 'bg-rose-500' },
  { key: 'done',        label: 'Done',        icon: CheckCircle2, accent: 'bg-emerald-500' },
]

const filteredKanban = computed(() => {
  const result: Record<string, CalendarTask[]> = {}
  for (const col of displayColumns) {
    let tasks = store.kanban[col.key] ?? []
    if (filterPriority.value) tasks = tasks.filter(t => t.priority === filterPriority.value)
    result[col.key] = tasks
  }
  return result
})

onMounted(async () => {
  await workspaceStore.fetchWorkspaces()
  await loadTasks()
})

async function loadTasks() {
  await store.fetchTasks({
    workspace_id: activeWorkspaceId.value || undefined,
    status: filterStatus.value || undefined,
    priority: filterPriority.value || undefined,
  })
}

watch([filterStatus, filterPriority], loadTasks)

const presetStatus = ref('')

function openCreate(status: string) {
  editTask.value = null
  presetStatus.value = status
  showCreate.value = true
}

async function openDetail(id: string) {
  await store.openTask(id)
  showDetail.value = true
}

function onEditFromDetail(task: CalendarTask) {
  editTask.value = task
  showDetail.value = false
  showEdit.value = true
}

function onDragStart(e: DragEvent, taskId: string) {
  draggedTaskId.value = taskId
  e.dataTransfer?.setData('text/plain', taskId)
}

async function onDrop(e: DragEvent, targetStatus: string) {
  const id = e.dataTransfer?.getData('text/plain') ?? draggedTaskId.value
  if (!id) return
  await store.moveStatus(id, targetStatus)
}

const workspaceOptions = computed(() => [
  { value: '', label: 'All Workspaces' },
  ...workspaceStore.workspaces.map(ws => ({ value: ws.id, label: ws.name }))
])

const statusOptions = computed(() => [
  { value: '', label: 'All Statuses' },
  ...displayColumns.map(col => ({ value: col.key, label: col.label }))
])

const priorityOptions = [
  { value: '', label: 'All Priorities' },
  { value: 'urgent', label: 'Urgent' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' }
]
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-10rem)] space-y-8 animate-in fade-in duration-700">
    <!-- Matrix Orchestration Toolbar -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-6 px-1">
      <div class="flex flex-col sm:flex-row items-end gap-4 flex-1">
        <div class="w-full sm:w-64">
           <FormSelect label="Workspace" v-model="activeWorkspaceId" :options="workspaceOptions" @update:model-value="loadTasks" />
        </div>
        <div class="w-full sm:w-48">
           <FormSelect label="Status Filter" v-model="filterStatus" :options="statusOptions" />
        </div>
        <div class="w-full sm:w-48">
           <FormSelect label="Priority" v-model="filterPriority" :options="priorityOptions" />
        </div>
      </div>
      <Button
        @click="showCreate = true"
        class="h-11 rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 font-bold uppercase tracking-widest text-[11px]"
      >
        <Plus class="w-4 h-4 mr-2" />
        New Task
      </Button>
    </div>

    <!-- Orchestration Matrix -->
    <div class="flex-1 overflow-x-auto no-scrollbar pb-6">
      <div class="flex gap-6 h-full min-w-max pb-2">
        <div
          v-for="col in displayColumns"
          :key="col.key"
          class="w-80 flex flex-col flex-shrink-0 relative"
          @dragover.prevent
          @drop="onDrop($event, col.key)"
        >
          <!-- Column Calibration -->
          <div class="flex items-center justify-between mb-4 group/header">
             <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-xl bg-white border border-slate-200 shadow-sm flex items-center justify-center group-hover/header:scale-110 transition-transform">
                   <component :is="col.icon" class="w-4 h-4 text-slate-400 group-hover/header:text-slate-900 transition-colors" />
                </div>
                <div>
                  <h4 class="text-[11px] font-black text-slate-900 uppercase tracking-widest leading-none">{{ col.label }}</h4>
                  <p class="text-[9px] text-slate-400 font-bold mt-1 uppercase tracking-tight">{{ filteredKanban[col.key]?.length ?? 0 }} tasks</p>
                </div>
             </div>
             <Button variant="ghost" size="icon" @click="openCreate(col.key)" class="h-8 w-8 rounded-xl hover:bg-white border border-transparent hover:border-slate-200 transition-all">
                <Plus class="w-3.5 h-3.5" />
             </Button>
             
             <!-- Accent Strip -->
             <div class="absolute -top-1 left-0 right-0 h-0.5 rounded-full" :class="col.accent" />
          </div>

          <!-- Processing Lane -->
          <div
            class="flex-1 overflow-y-auto space-y-4 p-2 rounded-[32px] bg-slate-50/30 backdrop-blur-sm border border-slate-100 transition-all hover:bg-slate-50/50"
          >
            <div
              v-for="task in filteredKanban[col.key]"
              :key="task.id"
              draggable="true"
              @dragstart="onDragStart($event, task.id)"
              class="animate-in fade-in slide-in-from-bottom-2 duration-300"
            >
              <TaskCard :task="task" @click="openDetail(task.id)" />
            </div>
            
            <div
              v-if="!filteredKanban[col.key]?.length"
              class="flex flex-col items-center justify-center py-12 px-6 rounded-[24px] border border-dashed border-slate-200/60 transition-all group/empty"
            >
               <Zap class="w-6 h-6 text-slate-200 mb-2 group-hover/empty:scale-110 transition-transform" />
               <p class="text-[9px] font-bold text-slate-300 uppercase tracking-widest text-center">Awaiting Node Allocation</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Interface Modulation Layers -->
    <TaskPanel
      :open="showCreate || showEdit"
      :task="editTask"
      :workspace-id="activeWorkspaceId || undefined"
      @close="showCreate = false; showEdit = false; editTask = null"
      @saved="loadTasks"
    />

    <TaskDetailDrawer
      :open="showDetail"
      :task="store.activeTask"
      @close="showDetail = false"
      @edit="onEditFromDetail"
    />
  </div>
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
