<script setup lang="ts">
import { ref, onMounted } from 'vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import type { Employee } from '../../services/employee.service'
import { listDepartments } from '../../services/department.service'
import { listDesignations } from '../../services/designation.service'
import { listBranches } from '../../services/branch.service'
import { listEmployeeGrades } from '../../services/employee-grade.service'

const props = defineProps<{ modelValue: Partial<Employee> }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: Partial<Employee>): void }>()

function update(key: keyof Employee, val: string) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}

const deptOptions = ref<{ value: string; label: string }[]>([])
const desigOptions = ref<{ value: string; label: string }[]>([])
const branchOptions = ref<{ value: string; label: string }[]>([])
const gradeOptions = ref<{ value: string; label: string }[]>([])

onMounted(async () => {
  const [depts, desigs, branches, grades] = await Promise.allSettled([
    listDepartments(), listDesignations(), listBranches(), listEmployeeGrades()
  ])
  if (depts.status === 'fulfilled') deptOptions.value = depts.value.map(d => ({ value: d.id, label: d.name }))
  if (desigs.status === 'fulfilled') desigOptions.value = desigs.value.map(d => ({ value: d.id, label: d.name }))
  if (branches.status === 'fulfilled') branchOptions.value = branches.value.map(b => ({ value: b.id, label: b.name }))
  if (grades.status === 'fulfilled') gradeOptions.value = grades.value.map(g => ({ value: g.id, label: g.name }))
})
</script>

<template>
  <div class="space-y-5">
    <FormSelect label="Department" :modelValue="modelValue.department_id" :options="deptOptions" placeholder="Select department" @update:modelValue="update('department_id', $event)" />
    <FormSelect label="Designation" :modelValue="modelValue.designation" :options="desigOptions" placeholder="Select designation" @update:modelValue="update('designation', $event)" />
    <FormSelect label="Grade" :modelValue="modelValue.grade" :options="gradeOptions" placeholder="Select grade" @update:modelValue="update('grade', $event)" />
    <FormSelect label="Branch" :modelValue="modelValue.branch" :options="branchOptions" placeholder="Select branch" @update:modelValue="update('branch', $event)" />
    <FormInput label="Reports To (Employee ID)" :modelValue="modelValue.reports_to" @update:modelValue="update('reports_to', $event)" />
  </div>
</template>
