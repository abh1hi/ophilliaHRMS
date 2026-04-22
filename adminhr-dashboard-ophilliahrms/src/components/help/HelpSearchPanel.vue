<script setup lang="ts">
import { Search } from 'lucide-vue-next'

defineProps<{
  modelValue: string
  shown: number
  total: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

function updateValue(event: Event) {
  emit('update:modelValue', (event.target as HTMLInputElement).value)
}
</script>

<template>
  <div class="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
    <label class="sr-only" for="help-search">Search documentation</label>
    <div class="flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
      <Search class="h-4 w-4 shrink-0 text-slate-400" />
      <input
        id="help-search"
        :value="modelValue"
        type="search"
        placeholder="Search modules, roles, errors..."
        class="w-full bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400"
        @input="updateValue"
      >
    </div>
    <p class="mt-2 px-1 text-xs text-slate-400">{{ shown }} of {{ total }} modules shown</p>
  </div>
</template>
