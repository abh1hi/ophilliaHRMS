<script setup lang="ts">
import { Label } from './label'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './select'

defineProps<{
  label: string
  modelValue: string | undefined
  options: { value: string; label: string }[]
  placeholder?: string
  error?: string
  required?: boolean
  disabled?: boolean
}>()

defineEmits<{ (e: 'update:modelValue', val: string): void }>()
</script>

<template>
  <div class="space-y-2">
    <Label :class="{ 'text-destructive': !!error }">
      {{ label }}<span v-if="required" class="text-destructive ml-0.5">*</span>
    </Label>
    
    <Select
      :model-value="modelValue === '' ? '__EMPTY__' : modelValue"
      :disabled="disabled"
      @update:model-value="$emit('update:modelValue', $event === '__EMPTY__' ? '' : $event)"
    >
      <SelectTrigger :class="{ 'border-destructive ring-destructive': !!error }">
        <SelectValue :placeholder="placeholder" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectItem
            v-for="opt in options"
            :key="opt.value === '' ? '__EMPTY__' : opt.value"
            :value="opt.value === '' ? '__EMPTY__' : opt.value"
          >
            {{ opt.label }}
          </SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
    
    <p v-if="error" class="text-[0.8rem] font-medium text-destructive">
      {{ error }}
    </p>
  </div>
</template>
