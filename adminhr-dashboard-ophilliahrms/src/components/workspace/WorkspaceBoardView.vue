<template>
  <div class="flex flex-col h-[calc(100vh-12rem)]">
    <!-- Board toolbar -->
    <div class="flex items-center justify-between mb-4 flex-shrink-0">
      <div class="flex items-center gap-3">
        <select
          v-model="activeWorkspaceId"
          @change="loadTasks"
          class="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
        >
          <option value="">All Workspaces</option>
          <option v-for="ws in workspaceStore.workspaces" :key="ws.id" :value="ws.id">
            {{ ws.name }}
          </option>
        </select>
        <div class="flex items-center gap-1.5">
          <select v-model="filterStatus" class="px-2 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none">
            <option value="">All Status</option>
            <option v-for="col in store.COLUMNS" :key="col" :value="col" class="capitalize">{{ col.replace('_', ' ') }}</option>
          </select>
          <select v-model="filterPriority" class="px-2 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none">
            <option value="">All Priority</option>
            <option value="urgent">Urgent</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>
      <button
        @click="showCreate = true"
        class="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 text-white text-sm rounded-lg hover:bg-slate-700"
      >
        <PlusIcon class="w-4 h-4" />
        New Task
      </button>
    </div>

    <!-- Kanban board -->
    <div class="flex-1 overflow-x-auto">
      <div class="flex gap-4 h-full min-w-max">
        <div
          v-for="col in displayColumns"
          :key="col.key"
          class="w-72 flex flex-col flex-shrink-0"
        >
          <!-- Column header -->
          <div :class="['flex items-center justify-between px-3 py-2 rounded-xl mb-2', col.headerClass]">
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold capitalize">{{ col.label }}</span>
              <span class="text-xs bg-white/50 px-1.5 py-0.5 rounded-full font-medium">
                {{ filteredKanban[col.key]?.length ?? 0 }}
              </span>
            </div>
            <button
              @click="openCreate(col.key)"
              class="p-1 rounded hover:bg-white/50 transition-colors"
            >
              <PlusIcon class="w-3.5 h-3.5" />
            </button>
          </div>

          <!-- Task cards -->
          <div
            class="flex-1 overflow-y-auto space-y-2 min-h-16 rounded-xl p-1"
            @dragover.prevent
            @drop="onDrop($event, col.key)"
          >
            <div
              v-for="task in filteredKanban[col.key]"
              :key="task.id"
              draggable="true"
              @dragstart="onDragStart($event, task.id)"
            >
              <TaskCard :task="task" @click="openDetail(task.id)" />
            </div>
            <div
              v-if="!filteredKanban[col.key]?.length"
              class="flex items-center justify-center h-16 text-xs text-slate-300 rounded-xl border-2 border-dashed border-slate-100"
            >
              Drop here
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create / Edit task -->
    <TaskPanel
      :open="showCreate || showEdit"
      :task="editTask"
      :workspace-id="activeWorkspaceId || undefined"
      @close="showCreate = false; showEdit = false; editTask = null"
      @saved="loadTasks"
    />

    <!-- Task detail drawer -->
    <TaskDetailDrawer
      :open="showDetail"
      :task="store.activeTask"
      @close="showDetail = false"
      @edit="onEditFromDetail"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { PlusIcon } from 'lucide-vue-next'
import { useWorkspaceStore } from '@/stores/workspace.store'
import { useTaskStore } from '@/stores/task.store'
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
  { key: 'todo',       label: 'To Do',      headerClass: 'bg-slate-100 text-slate-600' },
  { key: 'in_progress', label: 'In Progress', headerClass: 'bg-blue-100 text-blue-700'  },
  { key: 'blocked',    label: 'Blocked',    headerClass: 'bg-red-100 text-red-700'    },
  { key: 'in_review',  label: 'In Review',  headerClass: 'bg-yellow-100 text-yellow-700' },
  { key: 'done',       label: 'Done',       headerClass: 'bg-green-100 text-green-700' },
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
</script>
