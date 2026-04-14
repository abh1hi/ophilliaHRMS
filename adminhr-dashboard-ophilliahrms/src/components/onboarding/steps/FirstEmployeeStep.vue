<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { UserPlusIcon } from 'lucide-vue-next'
import { createEmployee } from '../../../services/employee.service'
import { listDepartments } from '../../../services/department.service'
import type { Department } from '../../../services/department.service'
import { handleApiError } from '../../../utils/handleApiError'

const DRAFT_KEY = 'onboarding_draft_first_employee'

const emit = defineEmits<{ completed: []; skipped: [] }>()
defineProps<{ readonly?: boolean }>()

const saving = ref(false)
const errorMsg = ref('')
const departments = ref<Department[]>([])
const form = reactive({
  first_name: '',
  last_name: '',
  email: '',
  date_joined: new Date().toISOString().split('T')[0],
  department_id: '',
  designation: '',
})

onMounted(async () => {
  const saved = localStorage.getItem(DRAFT_KEY)
  if (saved) {
    try { Object.assign(form, JSON.parse(saved)) } catch {}
  }
  try {
    departments.value = await listDepartments()
  } catch {}
})

watch(form, val => {
  localStorage.setItem(DRAFT_KEY, JSON.stringify(val))
}, { deep: true })

async function submit() {
  if (saving.value) return
  if (!form.first_name.trim() || !form.last_name.trim()) { errorMsg.value = 'First and last name are required'; return }
  if (!form.email.trim()) { errorMsg.value = 'Email is required'; return }
  if (!form.date_joined) { errorMsg.value = 'Date joined is required'; return }

  saving.value = true
  errorMsg.value = ''
  try {
    await createEmployee({
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      email: form.email.trim(),
      date_joined: form.date_joined,
      department_id: form.department_id || undefined,
      designation: form.designation.trim() || undefined,
      employment_status: 'active',
    } as any)
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
        <UserPlusIcon class="w-5 h-5 text-slate-600" />
      </div>
      <div>
        <h2 class="text-xl font-bold text-slate-900 leading-tight">Add first employee</h2>
        <p class="text-sm text-slate-400 font-medium mt-0.5">Add the first member of your team</p>
      </div>
    </div>

    <div class="space-y-5">
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1.5">First Name <span class="text-rose-500">*</span></label>
          <input
            v-model="form.first_name"
            type="text"
            placeholder="John"
            class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all"
          />
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1.5">Last Name <span class="text-rose-500">*</span></label>
          <input
            v-model="form.last_name"
            type="text"
            placeholder="Doe"
            class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all"
          />
        </div>
      </div>

      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-1.5">Work Email <span class="text-rose-500">*</span></label>
        <input
          v-model="form.email"
          type="email"
          placeholder="john.doe@company.com"
          class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all"
        />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1.5">Date Joined <span class="text-rose-500">*</span></label>
          <input
            v-model="form.date_joined"
            type="date"
            class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all"
          />
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1.5">Department</label>
          <select
            v-model="form.department_id"
            class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all"
          >
            <option value="">— None —</option>
            <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
          </select>
        </div>
      </div>

      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-1.5">Designation <span class="text-slate-400 font-normal">(optional)</span></label>
        <input
          v-model="form.designation"
          type="text"
          placeholder="e.g. Software Engineer, Manager"
          class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all"
        />
      </div>

      <p v-if="errorMsg" class="text-sm text-rose-600 font-medium">{{ errorMsg }}</p>

      <div class="flex items-center space-x-3 pt-2">
        <button
          @click="submit"
          :disabled="saving"
          class="px-7 py-3 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          <div v-if="saving" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span>{{ saving ? 'Adding...' : 'Add Employee' }}</span>
        </button>
        <button @click="skip" :disabled="saving" class="px-5 py-3 text-slate-400 hover:text-slate-600 text-sm font-medium transition-colors">
          Skip for now
        </button>
      </div>
    </div>
  </div>
</template>
