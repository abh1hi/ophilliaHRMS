<script setup lang="ts">
import { ref } from 'vue'
import { CheckCircle2, ChevronDown, ChevronRight, ExternalLink, ListChecks } from 'lucide-vue-next'
import type { HowToFlow } from './helpTypes'
import { Button } from '@/components/ui/button'

defineProps<{
  flows: HowToFlow[]
}>()

const emit = defineEmits<{
  (e: 'navigate', tab: string): void
}>()

const openFlowIds = ref<Set<string>>(new Set(['setup-attendance']))

function toggleFlow(id: string) {
  const next = new Set(openFlowIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  openFlowIds.value = next
}
</script>

<template>
  <section class="rounded-lg border border-slate-200 bg-white shadow-sm">
    <header class="border-b border-slate-100 p-5">
      <div class="flex items-start gap-3">
        <ListChecks class="mt-1 h-5 w-5 shrink-0 text-slate-700" />
        <div>
          <p class="text-xs font-semibold uppercase tracking-widest text-slate-400">How-to flows</p>
          <h3 class="mt-1 text-xl font-semibold text-slate-950">End-to-end setup workflows</h3>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Use these operational flows when you need to configure a full module from zero to production-ready.
            Each flow lists prerequisites, exact setup steps, expected results, and final readiness checks.
          </p>
        </div>
      </div>
    </header>

    <div class="divide-y divide-slate-100">
      <article v-for="flow in flows" :key="flow.id">
        <button
          type="button"
          class="flex w-full items-start justify-between gap-4 px-5 py-4 text-left transition hover:bg-slate-50"
          @click="toggleFlow(flow.id)"
        >
          <span>
            <span class="text-base font-semibold text-slate-950">{{ flow.title }}</span>
            <span class="mt-1 block text-sm leading-6 text-slate-600">{{ flow.summary }}</span>
            <span class="mt-2 block text-xs font-semibold uppercase tracking-widest text-slate-400">
              Owner: {{ flow.owner }}
            </span>
          </span>
          <component
            :is="openFlowIds.has(flow.id) ? ChevronDown : ChevronRight"
            class="mt-1 h-4 w-4 shrink-0 text-slate-400"
          />
        </button>

        <div v-if="openFlowIds.has(flow.id)" class="space-y-5 px-5 pb-5">
          <div class="rounded-md border border-emerald-100 bg-emerald-50 px-4 py-3">
            <p class="text-xs font-semibold uppercase tracking-widest text-emerald-700">Target outcome</p>
            <p class="mt-1 text-sm leading-6 text-emerald-900">{{ flow.outcome }}</p>
          </div>

          <div>
            <p class="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">Prerequisites</p>
            <ul class="grid gap-2 md:grid-cols-2">
              <li
                v-for="item in flow.prerequisites"
                :key="item"
                class="rounded-md border border-slate-100 bg-slate-50 px-3 py-2 text-sm leading-6 text-slate-700"
              >
                {{ item }}
              </li>
            </ul>
          </div>

          <div>
            <p class="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">Step-by-step setup</p>
            <ol class="space-y-3">
              <li
                v-for="(step, index) in flow.steps"
                :key="step.title"
                class="rounded-lg border border-slate-200 bg-white p-4"
              >
                <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div class="flex gap-3">
                    <span class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-bold text-white">
                      {{ index + 1 }}
                    </span>
                    <div>
                      <h4 class="font-semibold text-slate-950">{{ step.title }}</h4>
                      <p class="mt-1 text-sm leading-6 text-slate-600">{{ step.detail }}</p>
                      <p class="mt-2 text-sm leading-6 text-emerald-700">
                        Expected result: {{ step.expectedResult }}
                      </p>
                    </div>
                  </div>

                  <Button
                    v-if="step.tab"
                    variant="outline"
                    size="sm"
                    class="shrink-0 rounded-md"
                    @click="emit('navigate', step.tab)"
                  >
                    Open
                    <ExternalLink class="ml-2 h-3.5 w-3.5" />
                  </Button>
                </div>
              </li>
            </ol>
          </div>

          <div>
            <p class="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">Readiness checks</p>
            <div class="grid gap-2 md:grid-cols-2">
              <div
                v-for="check in flow.checks"
                :key="check"
                class="flex gap-2 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700"
              >
                <CheckCircle2 class="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                <span>{{ check }}</span>
              </div>
            </div>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
