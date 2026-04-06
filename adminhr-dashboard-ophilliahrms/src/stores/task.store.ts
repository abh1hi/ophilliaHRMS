import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  listTasks,
  getTask,
  createTask,
  updateTask,
  updateTaskStatus,
  deleteTask,
  type CalendarTask,
  type TaskCreate,
  type TaskUpdate,
  type TaskListParams,
} from '@/services/calendar-tasks.service'

type KanbanColumns = Record<string, CalendarTask[]>

const COLUMNS = ['todo', 'in_progress', 'blocked', 'in_review', 'done', 'cancelled'] as const

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<CalendarTask[]>([])
  const activeTask = ref<CalendarTask | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const activeFilters = ref<TaskListParams>({})

  const kanban = computed<KanbanColumns>(() => {
    const cols: KanbanColumns = {}
    for (const col of COLUMNS) cols[col] = []
    for (const task of tasks.value) {
      if (cols[task.status]) cols[task.status].push(task)
    }
    return cols
  })

  async function fetchTasks(params: TaskListParams = {}) {
    loading.value = true
    error.value = null
    activeFilters.value = params
    try {
      tasks.value = (await listTasks(params)) ?? []
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load tasks'
    } finally {
      loading.value = false
    }
  }

  async function openTask(id: string) {
    loading.value = true
    try {
      activeTask.value = await getTask(id) ?? null
    } finally {
      loading.value = false
    }
  }

  async function create(payload: TaskCreate) {
    const task = await createTask(payload)
    if (task) tasks.value.unshift(task)
    return task
  }

  async function edit(id: string, payload: TaskUpdate) {
    const task = await updateTask(id, payload)
    if (task) _replace(task)
    return task
  }

  async function moveStatus(id: string, status: string) {
    const task = await updateTaskStatus(id, status)
    if (task) _replace(task)
    return task
  }

  async function remove(id: string) {
    await deleteTask(id)
    tasks.value = tasks.value.filter(t => t.id !== id)
    if (activeTask.value?.id === id) activeTask.value = null
  }

  function _replace(task: CalendarTask) {
    const idx = tasks.value.findIndex(t => t.id === task.id)
    if (idx !== -1) tasks.value[idx] = task
    if (activeTask.value?.id === task.id) activeTask.value = task
  }

  return {
    tasks,
    activeTask,
    kanban,
    loading,
    error,
    activeFilters,
    fetchTasks,
    openTask,
    create,
    edit,
    moveStatus,
    remove,
    COLUMNS,
  }
})
