<script setup lang="ts">
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import type { Employee } from '../../services/employee.service'

const props = defineProps<{ modelValue: Partial<Employee> }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: Partial<Employee>): void }>()

function update(key: keyof Employee, val: string) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}

const salaryModes = [
  { value: 'bank', label: 'Bank Transfer' },
  { value: 'cheque', label: 'Cheque' },
  { value: 'cash', label: 'Cash' },
]
</script>

<template>
  <div class="space-y-5">
    <FormInput label="Joining Salary (₹)" type="number" :modelValue="modelValue.joining_salary?.toString()" @update:modelValue="update('joining_salary', $event)" />
    <FormSelect label="Salary Payment Mode" :modelValue="modelValue.salary_mode" :options="salaryModes" placeholder="Select mode" @update:modelValue="update('salary_mode', $event)" />
    <div class="pt-2 border-t border-slate-200/60">
      <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">Banking Details</p>
      <div class="space-y-4">
        <FormInput label="Bank Name" :modelValue="modelValue.bank_name" @update:modelValue="update('bank_name', $event)" autocomplete="off" />
        <FormInput label="Bank Branch" :modelValue="modelValue.bank_branch" @update:modelValue="update('bank_branch', $event)" autocomplete="off" />
        <FormInput label="Account Number" :modelValue="modelValue.bank_account_number" @update:modelValue="update('bank_account_number', $event)" autocomplete="off" />
        <FormInput label="IFSC Code" :modelValue="modelValue.ifsc_code" @update:modelValue="update('ifsc_code', $event)" autocomplete="off" />
      </div>
    </div>
  </div>
</template>
