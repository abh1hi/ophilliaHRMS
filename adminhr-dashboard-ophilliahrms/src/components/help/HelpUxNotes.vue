<script setup lang="ts">
import { Database } from 'lucide-vue-next'

defineProps<{
  items: string[]
}>()
</script>

<template>
  <section class="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
    <div class="flex items-start gap-3">
      <Database class="mt-0.5 h-5 w-5 shrink-0 text-slate-700" />
      <div>
        <h3 class="font-semibold text-slate-950">Suggested UI/UX improvements included in this implementation</h3>
        <ul class="mt-3 grid gap-2 md:grid-cols-2">
          <li
            v-for="item in items"
            :key="item"
            class="rounded-md bg-slate-50 px-3 py-2 text-sm leading-6 text-slate-700"
          >
            {{ item }}
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>
