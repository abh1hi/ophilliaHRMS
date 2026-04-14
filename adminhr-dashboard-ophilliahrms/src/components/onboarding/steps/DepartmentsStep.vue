<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { BuildingIcon } from 'lucide-vue-next'
import { createDepartment } from '../../../services/department.service'
import { handleApiError } from '../../../utils/handleApiError'

const DRAFT_KEY = 'onboarding_draft_departments'

const emit = defineEmits<{ completed: []; skipped: [] }>()

defineProps<{ readonly?: boolean }>()

const saving = ref(false)
const errorMsg = ref('')
const form = reactive({ name: '', description: '' })

// Draft persistence
watch(form, val => {
  localStorage.setItem(DRAFT_KEY, JSON.stringify(val))
}, { deep: true })

onMounted(() => {
  const saved = localStorage.getItem(DRAFT_KEY)
  if (saved) {
    try { Object.assign(form, JSON.parse(saved)) } catch {}
  }
})

async function submit() {
  if (saving.value) return
  if (!form.name.trim()) { errorMsg.value = 'Department name is required'; return }

  saving.value = true
  errorMsg.value = ''
  try {
    await createDepartment({ name: form.name.trim(), description: form.description || undefined })
    localStorage.removeItem(DRAFT_KEY)
    emit('completed')
  } catch (e) {
    errorMsg.value = handleApiError(e)
  } finally {
    saving.value = false
  }
}

function skip() {
  localStorage.removeItem(DRAFT_KEY)
  emit('skipped')
}
</script>

<template>
  <div class="max-w-lg">
    <!-- Step header -->
    <div class="flex items-center space-x-3 mb-8">
      <div class="w-11 h-11 bg-slate-100 rounded-[14px] flex items-center justify-center">
        <BuildingIcon class="w-5 h-5 text-slate-600" />
      </div>
      <div>
        <h2 class="text-xl font-bold text-slate-900 leading-tight">Set up departments</h2>
        <p class="text-sm text-slate-400 font-medium mt-0.5">Create your first department to organise employees</p>
      </div>
    </div>

    <!-- Read-only notice for HR -->
    <div v-if="readonly" class="p-4 bg-slate-50 border border-slate-200 rounded-[14px] text-sm text-slate-500 font-medium mb-6">
      You can view this step but cannot make changes. Contact an admin.
    </div>

    <div v-else class="space-y-5">
      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-1.5">Department Name <span class="text-rose-500">*</span></label>
        <input
          v-model="form.name"
          type="text"
          placeholder="e.g. Engineering, Sales, HR"
          class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all"
        />
      </div>

      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-1.5">Description <span class="text-slate-400 font-normal">(optional)</span></label>
        <textarea
          v-model="form.description"
          rows="3"
          placeholder="Brief description of this department's function"
          class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all resize-none"
        ></textarea>
      </div>

      <p v-if="errorMsg" class="text-sm text-rose-600 font-medium">{{ errorMsg }}</p>

      <div class="flex items-center space-x-3 pt-2">
        <button
          @click="submit"
          :disabled="saving"
          class="px-7 py-3 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          <div v-if="saving" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span>{{ saving ? 'Creating...' : 'Create Department' }}</span>
        </button>
        <button
          @click="skip"
          :disabled="saving"
          class="px-5 py-3 text-slate-400 hover:text-slate-600 text-sm font-medium transition-colors"
        >
          Skip for now
        </button>
      </div>
    </div>
  </div>
</template>
