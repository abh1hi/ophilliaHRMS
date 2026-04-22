<script setup lang="ts">
import type { DocSidebarItem } from './helpTypes'

defineProps<{
  items: DocSidebarItem[]
  activeId: string
}>()

const emit = defineEmits<{
  (e: 'select', id: string): void
}>()
</script>

<template>
  <aside class="space-y-4">
    <div class="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <p class="px-2 pb-2 text-xs font-semibold uppercase tracking-widest text-slate-400">Documentation</p>
      <nav class="space-y-1" aria-label="Help modules">
        <button
          v-for="item in items"
          :key="item.id"
          type="button"
          :class="[
            'flex w-full items-start gap-3 rounded-md px-3 py-2.5 text-left transition',
            activeId === item.id
              ? 'bg-slate-900 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-50 hover:text-slate-950'
          ]"
          @click="emit('select', item.id)"
        >
          <span
            :class="[
              'mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md',
              activeId === item.id ? 'bg-white/10 text-white' : 'bg-slate-100 text-slate-500'
            ]"
          >
            <component :is="item.icon" class="h-4 w-4" />
          </span>
          <span class="min-w-0">
            <span class="block text-sm font-semibold leading-5">{{ item.title }}</span>
            <span :class="['mt-0.5 block text-xs leading-4', activeId === item.id ? 'text-slate-300' : 'text-slate-400']">
              {{ item.category }}
            </span>
          </span>
        </button>
      </nav>
    </div>
  </aside>
</template>
