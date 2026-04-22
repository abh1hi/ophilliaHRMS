<script setup lang="ts">
import type { HelpFlow } from './helpTypes'
import { Button } from '@/components/ui/button'

defineProps<{
  flows: HelpFlow[]
}>()

const emit = defineEmits<{
  (e: 'expand-active'): void
  (e: 'collapse-all'): void
}>()
</script>

<template>
  <section class="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
    <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-widest text-slate-400">Ophillia HRMS documentation</p>
        <h2 class="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Complete HRMS help hub</h2>
        <p class="mt-3 max-w-4xl text-sm leading-6 text-slate-600">
          A production-ready documentation system for Admin, HR, Manager, and Employee users. Each module explains the
          purpose, prerequisites, workflow, step-by-step usage, rules, troubleshooting, and recommended operating practice.
        </p>
      </div>

      <div class="flex flex-wrap gap-2">
        <Button variant="outline" class="rounded-md" @click="emit('expand-active')">Expand active module</Button>
        <Button variant="outline" class="rounded-md" @click="emit('collapse-all')">Collapse all</Button>
      </div>
    </div>

    <div class="mt-5 grid gap-3 md:grid-cols-4">
      <div
        v-for="flow in flows"
        :key="flow.title"
        class="rounded-lg border border-slate-200 bg-slate-50 p-4"
      >
        <component :is="flow.icon" class="h-5 w-5 text-slate-700" />
        <h3 class="mt-3 text-sm font-semibold text-slate-950">{{ flow.title }}</h3>
        <ul class="mt-3 space-y-2">
          <li v-for="point in flow.points" :key="point" class="text-xs leading-5 text-slate-600">{{ point }}</li>
        </ul>
      </div>
    </div>
  </section>
</template>
