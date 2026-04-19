<script setup lang="ts">
import { ref } from 'vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Input } from '../ui/input'
import { Button } from '../ui/button'
import { Label } from '../ui/label'
import { Eye, EyeOff } from 'lucide-vue-next'
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
  <div class="space-y-6">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <FormInput label="First Name" :modelValue="modelValue.first_name" @update:modelValue="update('first_name', $event)" required autocomplete="given-name" />
      <FormInput label="Last Name" :modelValue="modelValue.last_name" @update:modelValue="update('last_name', $event)" required autocomplete="family-name" />
    </div>
    <FormSelect label="Gender" :modelValue="modelValue.gender" :options="genderOptions" placeholder="Select gender" @update:modelValue="update('gender', $event)" />
    <FormInput label="Date of Birth" type="date" :modelValue="modelValue.date_of_birth" @update:modelValue="update('date_of_birth', $event)" />
    
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <FormInput label="Company Email" type="email" :modelValue="modelValue.email" @update:modelValue="update('email', $event)" required autocomplete="email" />
      <FormInput label="Personal Email" type="email" :modelValue="modelValue.personal_email" @update:modelValue="update('personal_email', $event)" autocomplete="email" />
    </div>
    
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <FormInput label="Phone" type="tel" :modelValue="modelValue.phone" @update:modelValue="update('phone', $event)" autocomplete="tel" />
      <FormInput label="Phone 2" type="tel" :modelValue="modelValue.phone_2" @update:modelValue="update('phone_2', $event)" autocomplete="tel" />
    </div>
    
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <FormInput label="Project" :modelValue="modelValue.project" @update:modelValue="update('project', $event)" />
      <FormInput label="Referred By" :modelValue="modelValue.referred_by" @update:modelValue="update('referred_by', $event)" />
    </div>

    <!-- Initial password — only shown when creating a new employee -->
    <div v-if="isNewEmployee" class="pt-6 border-t">
      <h3 class="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Login Credentials</h3>
      
      <div class="space-y-2">
        <Label class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Initial Password</Label>
        <div class="relative max-w-sm">
          <Input
            :type="showPassword ? 'text' : 'password'"
            :model-value="modelValue.initial_password ?? ''"
            placeholder="Leave blank to auto-generate"
            class="pr-10"
            @update:model-value="update('initial_password', $event as string)"
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            class="absolute right-0 top-0 h-full w-10 hover:bg-transparent"
            @click="showPassword = !showPassword"
          >
            <Eye v-if="!showPassword" class="h-4 w-4 text-muted-foreground" />
            <EyeOff v-else class="h-4 w-4 text-muted-foreground" />
          </Button>
        </div>
        <p class="text-[10px] text-muted-foreground italic">
          If left blank, a password will be auto-generated and must be reset on first login.
        </p>
      </div>
    </div>
  </div>
</template>
