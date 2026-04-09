<script setup lang="ts">
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import type { Employee } from '../../services/employee.service'

const props = defineProps<{ modelValue: Partial<Employee> }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: Partial<Employee>): void }>()

function update(key: keyof Employee, val: string) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}

const statusOptions = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive (Resigned)' },
  { value: 'terminated', label: 'Terminated' },
]
</script>

<template>
  <div class="space-y-5">
    <div class="p-4 bg-rose-50/50 border border-rose-200/60 rounded-[16px] text-sm text-rose-700">
      ⚠️ Once status is set to <strong>Inactive</strong> or <strong>Terminated</strong> and a Relieving Date is set, this employee will not be accessible in future transactions.
    </div>
    <FormSelect label="Employment Status" :modelValue="modelValue.employment_status" :options="statusOptions" @update:modelValue="update('employment_status', $event)" />
    <FormInput label="Resignation Date" type="date" :modelValue="modelValue.resignation_date" @update:modelValue="update('resignation_date', $event)" />
    <FormInput label="Relieving Date" type="date" :modelValue="modelValue.relieving_date" @update:modelValue="update('relieving_date', $event)" />
  </div>
</template>
