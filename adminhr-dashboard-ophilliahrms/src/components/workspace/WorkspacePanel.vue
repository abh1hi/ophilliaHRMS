<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { Button } from '@/components/ui/button'
import { 
  X, 
  Users, 
  Folder, 
  User, 
  Palette, 
  Info, 
  Layout, 
  Component, 
  Compass,
  Zap,
  Check
} from 'lucide-vue-next'
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
  { value: 'team' as const, label: 'Collective', icon: Users },
  { value: 'project' as const, label: 'Initiative', icon: Folder },
  { value: 'personal' as const, label: 'Individual', icon: User },
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
</script>

<template>
  <SlideDrawer 
    :open="open" 
    :title="isEdit ? 'Modify Environment' : 'Initialize Workspace'" 
    width="w-full max-w-md" 
    @close="emit('close')"
  >
    <div class="space-y-8 py-4">
      <div class="bg-indigo-50/30 p-4 rounded-2xl flex items-start gap-3 border border-indigo-100/50 mb-2">
         <Info class="w-4 h-4 text-indigo-500 mt-0.5" />
         <p class="text-[11px] text-indigo-700 font-medium leading-relaxed">
           Workspaces represent synchronized environments for task orchestration. Calibration of type and aesthetic focus optimizes data visualization.
         </p>
      </div>

      <FormInput label="Environmental Identity" v-model="form.name" required maxlength="200" placeholder="e.g. Core Engineering Hub" />
      <FormTextarea label="Operational Brief" v-model="form.description" placeholder="Specify the mission parameters..." />

      <div class="space-y-4">
        <div class="flex items-center gap-2 mb-2">
           <Layout class="w-4 h-4 text-slate-400" />
           <span class="text-[10px] font-black uppercase tracking-widest text-slate-900">Type Calibration</span>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <Button
            v-for="t in types"
            :key="t.value"
            type="button"
            variant="ghost"
            @click="form.workspace_type = t.value"
            :class="[
              'h-auto flex-col gap-2 p-4 rounded-[22px] border transition-all duration-300',
              form.workspace_type === t.value
                ? 'bg-slate-900 text-white border-slate-900 shadow-xl shadow-slate-200 scale-105'
                : 'bg-slate-50/50 text-slate-500 border-white/10 hover:bg-slate-100/50 hover:border-slate-200 hover:text-slate-900',
            ]"
          >
            <component :is="t.icon" :class="['w-5 h-5', form.workspace_type === t.value ? 'text-white' : 'text-slate-400']" />
            <span class="text-[10px] font-bold uppercase tracking-widest">{{ t.label }}</span>
          </Button>
        </div>
      </div>

      <div class="space-y-4">
        <div class="flex items-center gap-2 mb-2">
           <Palette class="w-4 h-4 text-slate-400" />
           <span class="text-[10px] font-black uppercase tracking-widest text-slate-900">Aesthetic Focus</span>
        </div>
        <div class="p-6 bg-slate-50/50 rounded-[32px] border border-white/10 flex flex-wrap gap-3">
          <button
            v-for="c in colors"
            :key="c"
            type="button"
            @click="form.color = c"
            :style="{ backgroundColor: c }"
            class="w-8 h-8 rounded-full border-2 transition-all duration-300 relative group"
            :class="[
              form.color === c ? 'border-slate-900 scale-125' : 'border-white/40 hover:scale-110 shadow-sm',
            ]"
          >
             <Check v-if="form.color === c" class="absolute inset-0 m-auto w-3 h-3 text-white" />
          </button>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between gap-4">
        <div class="flex-1">
           <p v-if="error" class="text-[10px] font-bold text-destructive uppercase tracking-tight animate-in fade-in">{{ error }}</p>
        </div>
        <div class="flex gap-3">
          <Button variant="outline" @click="emit('close')" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[11px]">Cancel</Button>
          <Button 
            @click="submit" 
            :disabled="saving || !form.name.trim()" 
            class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 font-bold uppercase tracking-widest text-[11px]"
          >
            {{ saving ? 'Syncing...' : isEdit ? 'Update Environment' : 'Initialize Hub' }}
          </Button>
        </div>
      </div>
    </template>
  </SlideDrawer>
</template>

