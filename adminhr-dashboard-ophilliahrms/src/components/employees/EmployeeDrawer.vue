<script setup lang="ts">
import { ref, watch } from 'vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import EmployeeFormPersonal from './EmployeeFormPersonal.vue'
import EmployeeFormJoining from './EmployeeFormJoining.vue'
import EmployeeFormDeptGrade from './EmployeeFormDeptGrade.vue'
import EmployeeFormSalary from './EmployeeFormSalary.vue'
import EmployeeFormContact from './EmployeeFormContact.vue'
import EmployeeFormEmergency from './EmployeeFormEmergency.vue'
import EmployeeFormEducation from './EmployeeFormEducation.vue'
import EmployeeFormExperience from './EmployeeFormExperience.vue'
import EmployeeFormExit from './EmployeeFormExit.vue'
import { createEmployee, updateEmployee } from '../../services/employee.service'
import type { Employee } from '../../services/employee.service'

const props = defineProps<{
  open: boolean
  employee?: Employee | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved', emp: Employee): void
}>()

const tabs = [
  { key: 'personal',    label: 'Personal'     },
  { key: 'joining',     label: 'Joining'      },
  { key: 'dept',        label: 'Dept & Grade' },
  { key: 'salary',      label: 'Salary'       },
  { key: 'contact',     label: 'Contact'      },
  { key: 'emergency',   label: 'Emergency'    },
  { key: 'education',   label: 'Education'    },
  { key: 'experience',  label: 'Experience'   },
  { key: 'exit',        label: 'Exit'         },
]

const activeTab = ref('personal')
const form = ref<Partial<Employee>>({})
const saving = ref(false)
const errorMsg = ref('')

// Populate form when editing an existing employee
watch(() => props.employee, (emp) => {
  form.value = emp ? { ...emp } : {}
  activeTab.value = 'personal'
  errorMsg.value = ''
}, { immediate: true })

const isEdit = () => !!props.employee?.id

async function save() {
  saving.value = true
  errorMsg.value = ''
  try {
    const result = isEdit()
      ? await updateEmployee(props.employee!.id, form.value)
      : await createEmployee(form.value)
    emit('saved', result)
    emit('close')
  } catch (err: any) {
    errorMsg.value = err.message || 'Failed to save employee.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SlideDrawer
    :open="open"
    :title="isEdit() ? `Edit — ${employee?.first_name} ${employee?.last_name}` : 'New Employee'"
    subtitle="Fill in the details across the sections below"
    width="w-full max-w-3xl"
    @close="emit('close')"
  >
    <!-- Tab Pills -->
    <div class="flex flex-wrap gap-2 mb-8 -mt-2">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        :class="[
          'px-4 py-1.5 rounded-full text-xs font-semibold transition-all duration-200',
          activeTab === tab.key
            ? 'bg-slate-900 text-white shadow-sm'
            : 'bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-800'
        ]"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <EmployeeFormPersonal  v-if="activeTab === 'personal'"   v-model="form" />
    <EmployeeFormJoining   v-if="activeTab === 'joining'"    v-model="form" />
    <EmployeeFormDeptGrade v-if="activeTab === 'dept'"       v-model="form" />
    <EmployeeFormSalary    v-if="activeTab === 'salary'"     v-model="form" />
    <EmployeeFormContact   v-if="activeTab === 'contact'"    v-model="form" />
    <EmployeeFormEmergency v-if="activeTab === 'emergency'"  v-model="form" />
    <EmployeeFormEducation v-if="activeTab === 'education'"  v-model="form" />
    <EmployeeFormExperience v-if="activeTab === 'experience'" v-model="form" />
    <EmployeeFormExit      v-if="activeTab === 'exit'"       v-model="form" />

    <!-- Footer -->
    <template #footer>
      <div class="flex items-center justify-between">
        <p v-if="errorMsg" class="text-sm text-rose-600 font-medium">{{ errorMsg }}</p>
        <div v-else></div>
        <div class="flex items-center space-x-3">
          <button
            @click="emit('close')"
            class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors"
          >
            Cancel
          </button>
          <button
            @click="save"
            :disabled="saving"
            class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60 hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0"
          >
            {{ saving ? 'Saving...' : (isEdit() ? 'Update Employee' : 'Create Employee') }}
          </button>
        </div>
      </div>
    </template>
  </SlideDrawer>
</template>
