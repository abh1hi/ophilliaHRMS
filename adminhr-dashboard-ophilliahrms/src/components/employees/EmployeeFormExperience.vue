<script setup lang="ts">
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import type { Employee } from '../../services/employee.service'

const props = defineProps<{ modelValue: Partial<Employee> }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: Partial<Employee>): void }>()

function update(key: keyof Employee, val: string) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}
</script>

<template>
  <div class="space-y-5">
    <FormInput label="Previous Company Name" :modelValue="modelValue.last_firm_name" @update:modelValue="update('last_firm_name', $event)" />
    <FormInput label="Last Designation" :modelValue="modelValue.last_designation" @update:modelValue="update('last_designation', $event)" />
    <FormInput label="Years of Experience" type="number" :modelValue="modelValue.years_of_experience" @update:modelValue="update('years_of_experience', $event)" placeholder="e.g. 3.5" />
    <FormInput label="Last Drawn Salary (₹)" type="number" :modelValue="modelValue.last_drawn_salary?.toString()" @update:modelValue="update('last_drawn_salary', $event)" />
    <FormTextarea label="Reason to Quit" :modelValue="modelValue.reason_to_quit" @update:modelValue="update('reason_to_quit', $event)" />
    <div class="pt-4 border-t border-slate-200/60">
      <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">Health Details</p>
      <div class="space-y-4">
        <FormTextarea label="Known Health Issues" :modelValue="modelValue.health_issues" @update:modelValue="update('health_issues', $event)" />
        <FormTextarea label="Allergies" :modelValue="modelValue.allergies" @update:modelValue="update('allergies', $event)" />
      </div>
    </div>
  </div>
</template>
