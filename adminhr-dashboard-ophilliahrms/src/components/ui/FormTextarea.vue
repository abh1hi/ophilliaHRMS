<script setup lang="ts">
import { Textarea } from './textarea'
import { Label } from './label'

defineProps<{
  label: string
  modelValue: string | undefined
  placeholder?: string
  rows?: number
  error?: string
  required?: boolean
}>()

defineEmits<{ (e: 'update:modelValue', val: string): void }>()
</script>

<template>
  <div class="space-y-2">
    <Label :class="{ 'text-destructive': !!error }">
      {{ label }}<span v-if="required" class="text-destructive ml-0.5">*</span>
    </Label>
    <Textarea
      :model-value="modelValue"
      :placeholder="placeholder"
      :rows="rows || 3"
      :required="required"
      :class="{ 'border-destructive focus-visible:ring-destructive': !!error }"
      @update:model-value="$emit('update:modelValue', $event.toString())"
    />
    <p v-if="error" class="text-[0.8rem] font-medium text-destructive">
      {{ error }}
    </p>
  </div>
</template>
