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
    <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide">Current Address</p>
    <FormInput label="Door / Flat No." :modelValue="modelValue.door_no" @update:modelValue="update('door_no', $event)" autocomplete="address-line1" />
    <FormInput label="Street / Area" :modelValue="modelValue.street" @update:modelValue="update('street', $event)" autocomplete="address-line2" />
    <FormInput label="Village / Town / City" :modelValue="modelValue.village_town" @update:modelValue="update('village_town', $event)" autocomplete="address-level2" />
    <FormInput label="PIN Code" :modelValue="modelValue.pin_code" @update:modelValue="update('pin_code', $event)" autocomplete="postal-code" />

    <div class="pt-4 border-t border-slate-200/60">
      <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">Official IDs</p>
      <div class="space-y-4">
        <FormInput label="Aadhaar Number" :modelValue="modelValue.aadhaar_number" @update:modelValue="update('aadhaar_number', $event)" autocomplete="off" />
        <FormInput label="PAN Number" :modelValue="modelValue.pan_number" @update:modelValue="update('pan_number', $event)" autocomplete="off" />
        <FormInput label="UAN Number" :modelValue="modelValue.uan_number" @update:modelValue="update('uan_number', $event)" autocomplete="off" />
        <FormInput label="ESI Number" :modelValue="modelValue.esi_number" @update:modelValue="update('esi_number', $event)" autocomplete="off" />
        <FormInput label="Driving License Number" :modelValue="modelValue.driving_license_number" @update:modelValue="update('driving_license_number', $event)" autocomplete="off" />
      </div>
    </div>
  </div>
</template>
