<script setup lang="ts">
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import type { Employee } from '../../services/employee.service'

const props = defineProps<{ modelValue: Partial<Employee> }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: Partial<Employee>): void }>()

function update(key: keyof Employee, val: string) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}

const genderOptions = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other / Prefer not to say' },
]
</script>

<template>
  <div class="space-y-5">
    <div class="grid grid-cols-2 gap-4">
      <FormInput label="First Name" :modelValue="modelValue.first_name" @update:modelValue="update('first_name', $event)" required autocomplete="given-name" />
      <FormInput label="Last Name" :modelValue="modelValue.last_name" @update:modelValue="update('last_name', $event)" required autocomplete="family-name" />
    </div>
    <FormSelect label="Gender" :modelValue="modelValue.gender" :options="genderOptions" placeholder="Select gender" @update:modelValue="update('gender', $event)" />
    <FormInput label="Date of Birth" type="date" :modelValue="modelValue.date_of_birth" @update:modelValue="update('date_of_birth', $event)" />
    <FormInput label="Company Email" type="email" :modelValue="modelValue.email" @update:modelValue="update('email', $event)" required autocomplete="email" />
    <FormInput label="Personal Email" type="email" :modelValue="modelValue.personal_email" @update:modelValue="update('personal_email', $event)" autocomplete="email" />
    <div class="grid grid-cols-2 gap-4">
      <FormInput label="Phone" type="tel" :modelValue="modelValue.phone" @update:modelValue="update('phone', $event)" autocomplete="tel" />
      <FormInput label="Phone 2" type="tel" :modelValue="modelValue.phone_2" @update:modelValue="update('phone_2', $event)" autocomplete="tel" />
    </div>
    <FormInput label="Project" :modelValue="modelValue.project" @update:modelValue="update('project', $event)" />
    <FormInput label="Referred By" :modelValue="modelValue.referred_by" @update:modelValue="update('referred_by', $event)" />
  </div>
</template>
