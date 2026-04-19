<script setup lang="ts">
import { ref, watch } from 'vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import { Button } from '../ui/button'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../ui/tabs'
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
    width="w-full max-w-4xl"
    @close="emit('close')"
  >
    <Tabs v-model="activeTab" class="w-full">
      <div class="sticky top-0 bg-background/95 backdrop-blur z-20 -mx-6 px-6 pb-2 border-b">
        <TabsList class="flex w-full justify-start h-auto p-1 bg-muted/50 rounded-lg overflow-x-auto no-scrollbar">
          <TabsTrigger
            v-for="tab in tabs"
            :key="tab.key"
            :value="tab.key"
            class="px-4 py-2 text-xs font-semibold rounded-md data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
          >
            {{ tab.label }}
          </TabsTrigger>
        </TabsList>
      </div>

      <div class="mt-8">
        <TabsContent value="personal"> <EmployeeFormPersonal v-model="form" /> </TabsContent>
        <TabsContent value="joining"> <EmployeeFormJoining v-model="form" /> </TabsContent>
        <TabsContent value="dept"> <EmployeeFormDeptGrade v-model="form" /> </TabsContent>
        <TabsContent value="salary"> <EmployeeFormSalary v-model="form" /> </TabsContent>
        <TabsContent value="contact"> <EmployeeFormContact v-model="form" /> </TabsContent>
        <TabsContent value="emergency"> <EmployeeFormEmergency v-model="form" /> </TabsContent>
        <TabsContent value="education"> <EmployeeFormEducation v-model="form" /> </TabsContent>
        <TabsContent value="experience"> <EmployeeFormExperience v-model="form" /> </TabsContent>
        <TabsContent value="exit"> <EmployeeFormExit v-model="form" /> </TabsContent>
      </div>
    </Tabs>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-center justify-between">
        <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
        <div v-else></div>
        <div class="flex items-center space-x-3">
          <Button variant="outline" @click="emit('close')" class="rounded-full px-6">
            Cancel
          </Button>
          <Button @click="save" :disabled="saving" class="rounded-full px-8 shadow-md">
            {{ saving ? 'Saving...' : (isEdit() ? 'Update Employee' : 'Create Employee') }}
          </Button>
        </div>
      </div>
    </template>
  </SlideDrawer>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
