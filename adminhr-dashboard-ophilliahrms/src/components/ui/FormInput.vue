<script setup lang="ts">
import { Input } from './input'
import { Label } from './label'

defineProps<{
  label: string
  modelValue: string | number | undefined
  type?: string
  placeholder?: string
  error?: string
  required?: boolean
  autocomplete?: string
  disabled?: boolean
}>()

defineEmits<{ (e: 'update:modelValue', val: string): void }>()
</script>

<template>
  <div class="space-y-2">
    <Label :class="{ 'text-destructive': !!error }">
      {{ label }}<span v-if="required" class="text-destructive ml-0.5">*</span>
    </Label>
    <Input
      :type="type || 'text'"
      :model-value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :autocomplete="autocomplete || 'off'"
      :disabled="disabled"
      :class="{ 'border-destructive focus-visible:ring-destructive': !!error }"
      @update:model-value="$emit('update:modelValue', $event.toString())"
    />
    <p v-if="error" class="text-[0.8rem] font-medium text-destructive">
      {{ error }}
    </p>
  </div>
</template>
