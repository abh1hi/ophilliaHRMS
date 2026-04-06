<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/40" @click="emit('close')" />
        <div class="relative w-full max-w-md bg-white h-full shadow-xl flex flex-col">
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
            <h2 class="text-lg font-semibold text-slate-800">
              {{ isEdit ? 'Edit Calendar' : 'New Calendar' }}
            </h2>
            <button @click="emit('close')" class="p-1.5 rounded-lg hover:bg-slate-100">
              <XIcon class="w-5 h-5 text-slate-500" />
            </button>
          </div>

          <form @submit.prevent="submit" class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Name <span class="text-red-500">*</span></label>
              <input
                v-model="form.name"
                type="text"
                required
                maxlength="200"
                placeholder="Calendar name"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Description</label>
              <textarea
                v-model="form.description"
                rows="2"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 resize-none"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">Type</label>
              <select
                v-model="form.calendar_type"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none"
              >
                <option value="personal">Personal</option>
                <option value="team">Team</option>
                <option value="company">Company-wide</option>
              </select>
            </div>

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

            <div class="flex items-center gap-3">
              <input
                v-model="form.is_public"
                type="checkbox"
                id="cal-public"
                class="rounded border-slate-300"
              />
              <label for="cal-public" class="text-sm text-slate-700">Make this calendar publicly viewable (via share link)</label>
            </div>

            <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
          </form>

          <div class="px-6 py-4 border-t border-slate-200 flex justify-end gap-3">
            <button type="button" @click="emit('close')" class="px-4 py-2 text-sm text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50">
              Cancel
            </button>
            <button
              @click="submit"
              :disabled="saving || !form.name.trim()"
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
import { useCalendarStore } from '@/stores/calendar.store'
import type { CalendarItem } from '@/services/calendar-events.service'

interface Props {
  open: boolean
  calendar?: CalendarItem | null
  workspaceId?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved', calendar: CalendarItem): void
}>()

const store = useCalendarStore()
const saving = ref(false)
const error = ref<string | null>(null)
const isEdit = computed(() => !!props.calendar)
const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#64748b']

const form = ref({
  name: '',
  description: '',
  calendar_type: 'team' as 'personal' | 'team' | 'company',
  color: '#3b82f6',
  is_public: false,
})

watch(() => props.open, (val) => {
  if (val) {
    error.value = null
    if (props.calendar) {
      form.value = {
        name: props.calendar.name,
        description: props.calendar.description ?? '',
        calendar_type: (props.calendar.calendar_type as 'personal' | 'team' | 'company') ?? 'team',
        color: props.calendar.color ?? '#3b82f6',
        is_public: props.calendar.is_public,
      }
    } else {
      form.value = { name: '', description: '', calendar_type: 'team', color: '#3b82f6', is_public: false }
    }
  }
})

async function submit() {
  if (!form.value.name.trim()) return
  saving.value = true
  error.value = null
  try {
    let cal: CalendarItem | undefined | null
    if (props.calendar) {
      cal = await store.editCalendar(props.calendar.id, {
        name: form.value.name,
        description: form.value.description || undefined,
        color: form.value.color,
        is_public: form.value.is_public,
      })
    } else {
      cal = await store.addCalendar({
        workspace_id: props.workspaceId,
        name: form.value.name,
        description: form.value.description || undefined,
        calendar_type: form.value.calendar_type,
        color: form.value.color,
        is_public: form.value.is_public,
      })
    }
    if (cal) emit('saved', cal)
    emit('close')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to save calendar'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.25s; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
</style>
