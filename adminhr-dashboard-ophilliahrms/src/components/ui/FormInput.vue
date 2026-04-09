<script setup lang="ts">
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
  <div class="space-y-1.5">
    <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide">
      {{ label }}<span v-if="required" class="text-rose-500 ml-0.5">*</span>
    </label>
    <input
      :type="type || 'text'"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :autocomplete="autocomplete || 'off'"
      :disabled="disabled"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      :class="[
        'w-full bg-slate-50/50 border text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-2.5 outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed',
        error ? 'border-rose-300 focus:ring-rose-200' : 'border-slate-200/60'
      ]"
    />
    <p v-if="error" class="text-xs text-rose-500">{{ error }}</p>
  </div>
</template>
