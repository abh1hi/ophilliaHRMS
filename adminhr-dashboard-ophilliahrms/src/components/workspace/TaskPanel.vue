<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Button } from '@/components/ui/button'
import { 
  X, 
  CheckCircle, 
  Calendar, 
  Clock, 
  User, 
  Tag, 
  AlertCircle, 
  Info,
  Layers,
  Zap,
  Target,
  BarChart3
} from 'lucide-vue-next'
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

const priorityOptions = [
  { value: 'low', label: 'Low Intensity' },
  { value: 'medium', label: 'Medium Priority' },
  { value: 'high', label: 'High Priority' },
  { value: 'urgent', label: 'Mission Critical' }
]

const statusOptions = [
  { value: 'todo', label: 'Initial Queue' },
  { value: 'in_progress', label: 'Active Execution' },
  { value: 'blocked', label: 'Synchronous Block' },
  { value: 'in_review', label: 'Validation Phase' },
  { value: 'done', label: 'Finalized' }
]
</script>

<template>
  <SlideDrawer 
    :open="open" 
    :title="isEdit ? 'Task Reprogramming' : 'Initialize Task Sequence'" 
    width="w-full max-w-lg" 
    @close="emit('close')"
  >
    <div class="space-y-8 py-4">
      <div class="bg-indigo-50/30 p-4 rounded-2xl flex items-start gap-3 border border-indigo-100/50 mb-2">
         <Info class="w-4 h-4 text-indigo-500 mt-0.5" />
         <p class="text-[11px] text-indigo-700 font-medium leading-relaxed">
           Tasks represent atomic units of work within the workspace engine. Configure priority and resource allotment to optimize the execution flow.
         </p>
      </div>

      <FormInput label="Sequence Title" v-model="form.title" required placeholder="Describe the objective..." />
      <FormTextarea label="Operational Brief" v-model="form.description" placeholder="Specify depth and constraints..." />

      <div class="grid grid-cols-2 gap-6">
        <FormSelect label="Intensity Protocol" v-model="form.priority" :options="priorityOptions" />
        <FormSelect label="Execution Status" v-model="form.status" :options="statusOptions" />
      </div>

      <div class="grid grid-cols-2 gap-6">
        <div class="space-y-2">
          <label class="block text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1">Temporal Deadline</label>
          <div class="relative group">
             <Calendar class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-slate-900 transition-colors pointer-events-none" />
             <input
               v-model="form.due_date"
               type="datetime-local"
               class="w-full pl-10 pr-4 py-3 bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-2xl outline-none focus:ring-4 focus:ring-slate-900/5 transition-all"
             />
          </div>
        </div>
        <div class="space-y-2">
          <label class="block text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1">Resource Hours (EST)</label>
          <div class="relative group">
             <Clock class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-slate-900 transition-colors pointer-events-none" />
             <input
               v-model.number="form.estimated_hours"
               type="number"
               min="0"
               step="0.5"
               placeholder="Hours..."
               class="w-full pl-10 pr-4 py-3 bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-2xl outline-none focus:ring-4 focus:ring-slate-900/5 transition-all"
             />
          </div>
        </div>
      </div>

      <div class="space-y-6">
         <div class="flex items-center gap-2 mb-2">
            <Zap class="w-4 h-4 text-slate-400" />
            <span class="text-[10px] font-black uppercase tracking-widest text-slate-900">Advanced Parameters</span>
         </div>
         
         <div class="p-6 bg-slate-50/50 rounded-[32px] border border-white/10 space-y-6 relative overflow-hidden">
            <Layers class="absolute -right-4 -top-4 w-16 h-16 text-slate-900/5 -rotate-12" />
            
            <div class="space-y-3">
               <div class="flex items-center gap-2">
                  <User class="w-3.5 h-3.5 text-slate-400" />
                  <label class="text-[10px] font-bold text-slate-600 uppercase tracking-tight">Resource Allotment</label>
               </div>
               <input
                 v-model="assigneesRaw"
                 type="text"
                 placeholder="e.g. EMP-001, EMP-088"
                 class="w-full bg-white border border-slate-200/60 text-slate-900 text-sm rounded-2xl px-4 py-3 outline-none focus:ring-4 focus:ring-slate-900/5 transition-all shadow-sm"
               />
            </div>

            <div class="space-y-3">
               <div class="flex items-center gap-2">
                  <Tag class="w-3.5 h-3.5 text-slate-400" />
                  <label class="text-[10px] font-bold text-slate-600 uppercase tracking-tight">Taxonomy Tags</label>
               </div>
               <input
                 v-model="tagsRaw"
                 type="text"
                 placeholder="e.g. backend, urgency-l1"
                 class="w-full bg-white border border-slate-200/60 text-slate-900 text-sm rounded-2xl px-4 py-3 outline-none focus:ring-4 focus:ring-slate-900/5 transition-all shadow-sm"
               />
            </div>
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
            :disabled="saving || !form.title.trim()" 
            class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 font-bold uppercase tracking-widest text-[11px]"
          >
            {{ saving ? 'Syncing...' : isEdit ? 'Deploy Update' : 'Initialize Sequence' }}
          </Button>
        </div>
      </div>
    </template>
  </SlideDrawer>
</template>
