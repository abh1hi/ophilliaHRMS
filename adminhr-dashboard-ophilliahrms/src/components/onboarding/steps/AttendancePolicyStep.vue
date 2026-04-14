<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { ClockIcon } from 'lucide-vue-next'
import { apiFetchData } from '../../../services/http'
import { handleApiError } from '../../../utils/handleApiError'

const DRAFT_KEY = 'onboarding_draft_attendance_policy'

const emit = defineEmits<{ completed: []; skipped: [] }>()
const props = defineProps<{ readonly?: boolean }>()

const saving = ref(false)
const errorMsg = ref('')
const form = reactive({
  name: 'Default Attendance Policy',
  work_hours_per_day: 8,
  method: 'manual',
})

const methodOptions = [
  { value: 'manual', label: 'Manual Entry' },
  { value: 'biometric', label: 'Biometric Device' },
  { value: 'gps', label: 'GPS / Mobile' },
  { value: 'both', label: 'Biometric + GPS' },
]

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
  if (!form.name.trim()) { errorMsg.value = 'Policy name is required'; return }
  if (!form.work_hours_per_day || form.work_hours_per_day < 1 || form.work_hours_per_day > 24) {
    errorMsg.value = 'Work hours must be between 1 and 24'
    return
  }

  saving.value = true
  errorMsg.value = ''
  try {
    await apiFetchData('/attendance/policies', {
      method: 'POST',
      body: JSON.stringify({
        name: form.name.trim(),
        work_hours_per_day: form.work_hours_per_day,
        method: form.method,
      }),
    })
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
    <div class="flex items-center space-x-3 mb-8">
      <div class="w-11 h-11 bg-slate-100 rounded-[14px] flex items-center justify-center">
        <ClockIcon class="w-5 h-5 text-slate-600" />
      </div>
      <div>
        <h2 class="text-xl font-bold text-slate-900 leading-tight">Set attendance policy</h2>
        <p class="text-sm text-slate-400 font-medium mt-0.5">Define work hours and how attendance is tracked</p>
      </div>
    </div>

    <!-- Read-only for HR -->
    <div v-if="props.readonly" class="p-4 bg-slate-50 border border-slate-200 rounded-[14px] text-sm text-slate-500 font-medium mb-6">
      Attendance policy can only be configured by an admin.
    </div>

    <div v-else class="space-y-5">
      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-1.5">Policy Name <span class="text-rose-500">*</span></label>
        <input
          v-model="form.name"
          type="text"
          placeholder="e.g. Standard Attendance Policy"
          class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all"
        />
      </div>

      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-1.5">Work Hours per Day <span class="text-rose-500">*</span></label>
        <input
          v-model.number="form.work_hours_per_day"
          type="number"
          min="1"
          max="24"
          class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all"
        />
      </div>

      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-1.5">Attendance Method</label>
        <div class="grid grid-cols-2 gap-2">
          <button
            v-for="opt in methodOptions"
            :key="opt.value"
            @click="form.method = opt.value"
            :class="[
              'px-4 py-3 rounded-[12px] border text-sm font-medium text-left transition-all',
              form.method === opt.value
                ? 'border-slate-900 bg-slate-900 text-white'
                : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
            ]"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <p v-if="errorMsg" class="text-sm text-rose-600 font-medium">{{ errorMsg }}</p>

      <div class="flex items-center space-x-3 pt-2">
        <button
          @click="submit"
          :disabled="saving"
          class="px-7 py-3 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          <div v-if="saving" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span>{{ saving ? 'Saving...' : 'Save Policy' }}</span>
        </button>
        <button @click="skip" :disabled="saving" class="px-5 py-3 text-slate-400 hover:text-slate-600 text-sm font-medium transition-colors">
          Skip for now
        </button>
      </div>
    </div>
  </div>
</template>
