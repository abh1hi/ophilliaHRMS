<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/40" @click="emit('close')" />
        <div class="relative w-full max-w-lg bg-white h-full shadow-xl flex flex-col">
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
            <h2 class="text-lg font-semibold text-slate-800">{{ isEdit ? 'Edit Task' : 'New Task' }}</h2>
            <button @click="emit('close')" class="p-1.5 rounded-lg hover:bg-slate-100">
              <XIcon class="w-5 h-5 text-slate-500" />
            </button>
          </div>

          <form class="flex-1 overflow-y-auto px-6 py-5 space-y-4">
            <!-- Title -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Title <span class="text-red-500">*</span></label>
              <input
                v-model="form.title"
                type="text"
                required
                placeholder="Task title"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
            </div>

            <!-- Description -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Description</label>
              <textarea
                v-model="form.description"
                rows="3"
                placeholder="Describe the task…"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none resize-none"
              />
            </div>

            <!-- Priority + Status -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1.5">Priority</label>
                <select v-model="form.priority" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none">
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1.5">Status</label>
                <select v-model="form.status" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none">
                  <option value="todo">To Do</option>
                  <option value="in_progress">In Progress</option>
                  <option value="blocked">Blocked</option>
                  <option value="in_review">In Review</option>
                  <option value="done">Done</option>
                </select>
              </div>
            </div>

            <!-- Due date -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Due Date</label>
              <input
                v-model="form.due_date"
                type="datetime-local"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
              />
            </div>

            <!-- Estimated hours -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Estimated Hours</label>
              <input
                v-model.number="form.estimated_hours"
                type="number"
                min="0"
                step="0.5"
                placeholder="e.g. 2.5"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
              />
            </div>

            <!-- Assignees -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Assignees (Employee IDs, comma separated)</label>
              <input
                v-model="assigneesRaw"
                type="text"
                placeholder="emp-001, emp-002"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
              />
            </div>

            <!-- Tags -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Tags (comma separated)</label>
              <input
                v-model="tagsRaw"
                type="text"
                placeholder="frontend, bug, sprint-1"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
              />
            </div>

            <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
          </form>

          <div class="px-6 py-4 border-t border-slate-200 flex justify-end gap-3">
            <button type="button" @click="emit('close')" class="px-4 py-2 text-sm text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50">
              Cancel
            </button>
            <button
              @click="submit"
              :disabled="saving || !form.title.trim()"
              class="px-4 py-2 text-sm font-medium text-white bg-slate-900 rounded-lg hover:bg-slate-700 disabled:opacity-50"
            >
              {{ saving ? 'Saving…' : isEdit ? 'Update' : 'Create' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { XIcon } from 'lucide-vue-next'
import { useTaskStore } from '@/stores/task.store'
import type { CalendarTask } from '@/services/calendar-tasks.service'

interface Props {
  open: boolean
  task?: CalendarTask | null
  workspaceId?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved'): void
}>()

const store = useTaskStore()
const saving = ref(false)
const error = ref<string | null>(null)
const isEdit = computed(() => !!props.task)
const assigneesRaw = ref('')
const tagsRaw = ref('')

const form = ref({
  title: '',
  description: '',
  priority: 'medium',
  status: 'todo',
  due_date: '',
  estimated_hours: undefined as number | undefined,
})

watch(() => props.open, (val) => {
  if (val) {
    error.value = null
    if (props.task) {
      form.value = {
        title: props.task.title,
        description: props.task.description ?? '',
        priority: props.task.priority,
        status: props.task.status,
        due_date: props.task.due_date ? props.task.due_date.slice(0, 16) : '',
        estimated_hours: props.task.estimated_hours,
      }
      assigneesRaw.value = props.task.assignees?.map(a => a.employee_id).join(', ') ?? ''
      tagsRaw.value = props.task.tags?.join(', ') ?? ''
    } else {
      form.value = { title: '', description: '', priority: 'medium', status: 'todo', due_date: '', estimated_hours: undefined }
      assigneesRaw.value = ''
      tagsRaw.value = ''
    }
  }
})

async function submit() {
  if (!form.value.title.trim()) return
  saving.value = true
  error.value = null
  try {
    const assignees = assigneesRaw.value
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)

    const tags = tagsRaw.value
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)

    if (props.task) {
      await store.edit(props.task.id, {
        title: form.value.title,
        description: form.value.description || undefined,
        priority: form.value.priority,
        due_date: form.value.due_date ? form.value.due_date + ':00Z' : undefined,
        estimated_hours: form.value.estimated_hours,
        tags,
      })
    } else {
      await store.create({
        workspace_id: props.workspaceId,
        title: form.value.title,
        description: form.value.description || undefined,
        priority: form.value.priority,
        status: form.value.status,
        due_date: form.value.due_date ? form.value.due_date + ':00Z' : undefined,
        estimated_hours: form.value.estimated_hours,
        tags,
        assignees,
      })
    }
    emit('saved')
    emit('close')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to save task'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.25s; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
</style>
