<script setup lang="ts">
import FormInput from '../ui/FormInput.vue'
import type { Employee } from '../../services/employee.service'

const props = defineProps<{ modelValue: Partial<Employee> }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: Partial<Employee>): void }>()

function update(key: keyof Employee, val: string) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}
</script>

<template>
  <div class="space-y-5">
    <FormInput label="Highest Qualification" :modelValue="modelValue.highest_qualification" @update:modelValue="update('highest_qualification', $event)" placeholder="e.g. B.Tech, MBA" />
    <FormInput label="Institute / University" :modelValue="modelValue.institute_name" @update:modelValue="update('institute_name', $event)" />
    <FormInput label="Year of Passing" type="number" :modelValue="modelValue.year_of_passing" @update:modelValue="update('year_of_passing', $event)" placeholder="e.g. 2020" />
    <FormInput label="Percentage / Grade" :modelValue="modelValue.percentage" @update:modelValue="update('percentage', $event)" placeholder="e.g. 72.5% or A+" />
  </div>
</template>
