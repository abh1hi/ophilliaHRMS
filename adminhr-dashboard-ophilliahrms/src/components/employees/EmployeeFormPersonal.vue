<script setup lang="ts">
import { ref } from 'vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import { EyeIcon, EyeOffIcon } from 'lucide-vue-next'
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

// Password visibility toggle (create mode only)
const showPassword = ref(false)
const isNewEmployee = !props.modelValue.id
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

    <!-- Initial password — only shown when creating a new employee -->
    <div v-if="isNewEmployee" class="pt-2 border-t border-slate-100">
      <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Login Credentials</p>
      <div class="space-y-1.5">
        <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide">
          Initial Password
        </label>
        <div class="relative">
          <input
            :type="showPassword ? 'text' : 'password'"
            :value="modelValue.initial_password ?? ''"
            placeholder="Leave blank to auto-generate"
            autocomplete="new-password"
            @input="update('initial_password', ($event.target as HTMLInputElement).value)"
            class="w-full bg-slate-50/50 border border-slate-200/60 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-2.5 pr-10 outline-none transition-all"
          />
          <button
            type="button"
            @click="showPassword = !showPassword"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
            tabindex="-1"
          >
            <EyeIcon v-if="!showPassword" class="w-4 h-4" />
            <EyeOffIcon v-else class="w-4 h-4" />
          </button>
        </div>
        <p class="text-xs text-slate-400">If left blank, a password will be auto-generated and must be reset on first login.</p>
      </div>
    </div>
  </div>
</template>
