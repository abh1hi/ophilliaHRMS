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
    <FormInput label="Contact Name" :modelValue="modelValue.emergency_contact_name" @update:modelValue="update('emergency_contact_name', $event)" autocomplete="name" />
    <FormInput label="Contact Number" type="tel" :modelValue="modelValue.emergency_contact_number" @update:modelValue="update('emergency_contact_number', $event)" autocomplete="tel" />
    <FormInput label="Relationship" :modelValue="modelValue.emergency_contact_relation" @update:modelValue="update('emergency_contact_relation', $event)" placeholder="e.g. Spouse, Parent, Sibling" />
  </div>
</template>
