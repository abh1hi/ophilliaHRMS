<template>
  <!-- Slide drawer overlay -->
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/40" @click="emit('close')" />
        <div class="relative w-full max-w-md bg-white h-full shadow-xl flex flex-col">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
            <h2 class="text-lg font-semibold text-slate-800">
              {{ isEdit ? 'Edit Workspace' : 'New Workspace' }}
            </h2>
            <button @click="emit('close')" class="p-1.5 rounded-lg hover:bg-slate-100 transition-colors">
              <XIcon class="w-5 h-5 text-slate-500" />
            </button>
          </div>

          <!-- Form -->
          <form @submit.prevent="submit" class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
            <!-- Name -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Name <span class="text-red-500">*</span></label>
              <input
                v-model="form.name"
                type="text"
                required
                maxlength="200"
                placeholder="Team workspace name"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
            </div>

            <!-- Description -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Description</label>
              <textarea
                v-model="form.description"
                rows="3"
                placeholder="What is this workspace for?"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 resize-none"
              />
            </div>

            <!-- Type -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Type</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="t in types"
                  :key="t.value"
                  type="button"
                  @click="form.workspace_type = t.value"
                  :class="[
                    'px-3 py-2 rounded-lg border text-sm font-medium transition-colors flex flex-col items-center gap-1',
                    form.workspace_type === t.value
                      ? 'bg-slate-900 text-white border-slate-900'
                      : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50',
                  ]"
                >
                  <component :is="t.icon" class="w-4 h-4" />
                  {{ t.label }}
                </button>
              </div>
            </div>

            <!-- Color -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Color</label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="c in colors"
                  :key="c"
                  type="button"
                  @click="form.color = c"
                  :style="{ backgroundColor: c }"
                  :class="[
                    'w-8 h-8 rounded-full border-2 transition-all',
                    form.color === c ? 'border-slate-900 scale-110' : 'border-transparent',
                  ]"
                />
              </div>
            </div>

            <!-- Error -->
            <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
          </form>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-slate-200 flex justify-end gap-3">
            <button
              type="button"
              @click="emit('close')"
              class="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              @click="submit"
              :disabled="saving || !form.name.trim()"
              class="px-4 py-2 text-sm font-medium text-white bg-slate-900 rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50"
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
import { ref, watch } from 'vue'
import { XIcon, UsersIcon, FolderIcon, UserIcon } from 'lucide-vue-next'
import { useWorkspaceStore } from '@/stores/workspace.store'
import type { Workspace } from '@/services/calendar-workspace.service'

interface Props {
  open: boolean
  workspace?: Workspace | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved', workspace: Workspace): void
}>()

const store = useWorkspaceStore()
const saving = ref(false)
const error = ref<string | null>(null)

const isEdit = computed(() => !!props.workspace)

const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#64748b']

const types = [
  { value: 'team' as const, label: 'Team', icon: UsersIcon },
  { value: 'project' as const, label: 'Project', icon: FolderIcon },
  { value: 'personal' as const, label: 'Personal', icon: UserIcon },
]

const form = ref({
  name: '',
  description: '',
  workspace_type: 'team' as 'team' | 'project' | 'personal',
  color: '#3b82f6',
})

watch(() => props.open, (val) => {
  if (val) {
    error.value = null
    if (props.workspace) {
      form.value = {
        name: props.workspace.name,
        description: props.workspace.description ?? '',
        workspace_type: props.workspace.workspace_type,
        color: props.workspace.color ?? '#3b82f6',
      }
    } else {
      form.value = { name: '', description: '', workspace_type: 'team', color: '#3b82f6' }
    }
  }
})

async function submit() {
  if (!form.value.name.trim()) return
  saving.value = true
  error.value = null
  try {
    let ws: Workspace | undefined | null
    if (props.workspace) {
      ws = await store.update(props.workspace.id, {
        name: form.value.name,
        description: form.value.description || undefined,
        color: form.value.color,
      })
    } else {
      ws = await store.create({
        name: form.value.name,
        description: form.value.description || undefined,
        workspace_type: form.value.workspace_type,
        color: form.value.color,
      })
    }
    if (ws) emit('saved', ws)
    emit('close')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to save workspace'
  } finally {
    saving.value = false
  }
}

import { computed } from 'vue'
</script>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.25s;
}
.drawer-enter-active .relative,
.drawer-leave-active .relative {
  transition: transform 0.25s;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from .relative {
  transform: translateX(100%);
}
</style>
