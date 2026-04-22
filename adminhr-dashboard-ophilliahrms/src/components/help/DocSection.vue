<script setup lang="ts">
import { ChevronDown, ChevronRight, ExternalLink } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import type { DocModule } from './helpTypes'

defineProps<{
  module: DocModule
  openBlocks: Set<string>
}>()

const emit = defineEmits<{
  (e: 'toggle', key: string): void
  (e: 'navigate', tab: string): void
}>()
</script>

<template>
  <article :id="module.id" class="scroll-mt-6 rounded-lg border border-slate-200 bg-white shadow-sm">
    <header class="border-b border-slate-100 p-5">
      <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-widest text-slate-400">{{ module.category }}</p>
          <h2 class="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{{ module.title }}</h2>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{{ module.summary }}</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <span
              v-for="role in module.audience"
              :key="role"
              class="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-600"
            >
              {{ role }}
            </span>
          </div>
        </div>

        <div v-if="module.navTabs?.length" class="flex shrink-0 flex-wrap gap-2">
          <Button
            v-for="item in module.navTabs"
            :key="item.tab"
            variant="outline"
            size="sm"
            class="rounded-md"
            @click="emit('navigate', item.tab)"
          >
            {{ item.label }}
            <ExternalLink class="ml-2 h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </header>

    <div class="divide-y divide-slate-100">
      <section v-for="(block, index) in module.blocks" :key="block.title">
        <button
          type="button"
          class="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition hover:bg-slate-50"
          @click="emit('toggle', `${module.id}:${block.title}`)"
        >
          <span>
            <span class="text-sm font-semibold text-slate-950">{{ index + 1 }}. {{ block.title }}</span>
            <span class="mt-1 block text-xs text-slate-500">{{ block.bullets[0] }}</span>
          </span>
          <component
            :is="openBlocks.has(`${module.id}:${block.title}`) ? ChevronDown : ChevronRight"
            class="h-4 w-4 shrink-0 text-slate-400"
          />
        </button>

        <div v-if="openBlocks.has(`${module.id}:${block.title}`)" class="px-5 pb-5">
          <ul class="grid gap-2 md:grid-cols-2">
            <li
              v-for="bullet in block.bullets"
              :key="bullet"
              class="rounded-md border border-slate-100 bg-slate-50 px-3 py-2 text-sm leading-6 text-slate-700"
            >
              {{ bullet }}
            </li>
          </ul>
        </div>
      </section>
    </div>
  </article>
</template>
