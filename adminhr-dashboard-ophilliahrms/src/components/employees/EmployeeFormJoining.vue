<script setup lang="ts">
import { ref, onMounted } from 'vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import type { Employee } from '../../services/employee.service'
import { listEmploymentTypes } from '../../services/employment-type.service'

const props = defineProps<{ modelValue: Partial<Employee> }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: Partial<Employee>): void }>()

function update(key: keyof Employee, val: string) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}

const statusOptions = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'terminated', label: 'Terminated' },
]

const empTypeOptions = ref<{ value: string; label: string }[]>([])
onMounted(async () => {
  try {
    const types = await listEmploymentTypes()
    empTypeOptions.value = types.map(t => ({ value: t.id, label: t.name }))
  } catch {}
})
</script>

<template>
  <div class="space-y-5">
    <FormInput label="Employee Code" :modelValue="modelValue.employee_code" @update:modelValue="update('employee_code', $event)" placeholder="e.g. EMP-001, REG-U-90" />
    <FormInput label="Date of Joining" type="date" :modelValue="modelValue.date_joined" @update:modelValue="update('date_joined', $event)" required />
    <FormInput label="Offer Date" type="date" :modelValue="modelValue.offer_date" @update:modelValue="update('offer_date', $event)" />
    <FormInput label="Confirmation Date" type="date" :modelValue="modelValue.confirmation_date" @update:modelValue="update('confirmation_date', $event)" />
    <FormInput label="Contract End Date" type="date" :modelValue="modelValue.contract_end_date" @update:modelValue="update('contract_end_date', $event)" />
    <FormInput label="Notice Period (Days)" type="number" :modelValue="modelValue.notice_days?.toString()" @update:modelValue="update('notice_days', $event)" />
    <FormInput label="Date of Retirement" type="date" :modelValue="modelValue.date_of_retirement" @update:modelValue="update('date_of_retirement', $event)" />
    <FormSelect label="Employment Type" :modelValue="modelValue.employment_type" :options="empTypeOptions" placeholder="Select type" @update:modelValue="update('employment_type', $event)" />
    <FormSelect label="Employment Status" :modelValue="modelValue.employment_status" :options="statusOptions" @update:modelValue="update('employment_status', $event)" required />
  </div>
</template>
