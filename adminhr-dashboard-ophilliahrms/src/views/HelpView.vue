<script setup lang="ts">
import { computed, ref } from 'vue'
import DocSection from '@/components/help/DocSection.vue'
import DocSidebar from '@/components/help/DocSidebar.vue'
import HelpEmptyState from '@/components/help/HelpEmptyState.vue'
import HelpHowToFlows from '@/components/help/HelpHowToFlows.vue'
import HelpOverview from '@/components/help/HelpOverview.vue'
import HelpSearchPanel from '@/components/help/HelpSearchPanel.vue'
import HelpUxNotes from '@/components/help/HelpUxNotes.vue'
import { modules, systemFlows, uxImprovements } from '@/components/help/helpContent'
import { howToFlows } from '@/components/help/helpHowToFlows'

const emit = defineEmits<{ (e: 'navigate', tab: string): void }>()

const query = ref('')
const activeModuleId = ref(modules[0].id)
const openBlocks = ref<Set<string>>(new Set(
  modules.flatMap(module => module.blocks.slice(0, 2).map(block => `${module.id}:${block.title}`)),
))

const filteredModules = computed(() => {
  const text = query.value.trim().toLowerCase()
  if (!text) return modules

  return modules.filter(module => {
    const haystack = [
      module.title,
      module.summary,
      module.category,
      ...module.audience,
      ...module.blocks.flatMap(block => [block.title, ...block.bullets]),
    ].join(' ').toLowerCase()

    return haystack.includes(text)
  })
})

const filteredHowToFlows = computed(() => {
  const text = query.value.trim().toLowerCase()
  if (!text) return howToFlows

  return howToFlows.filter(flow => {
    const haystack = [
      flow.title,
      flow.summary,
      flow.owner,
      flow.outcome,
      ...flow.prerequisites,
      ...flow.steps.flatMap(step => [step.title, step.detail, step.expectedResult]),
      ...flow.checks,
    ].join(' ').toLowerCase()

    return haystack.includes(text)
  })
})

const sidebarItems = computed(() => filteredModules.value.map(({ id, title, category, icon, summary }) => ({
  id,
  title,
  category,
  icon,
  summary,
})))

const activeModule = computed(() => (
  filteredModules.value.find(module => module.id === activeModuleId.value)
  ?? filteredModules.value[0]
  ?? modules[0]
))

function selectModule(id: string) {
  activeModuleId.value = id
  requestAnimationFrame(() => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function toggleBlock(key: string) {
  const next = new Set(openBlocks.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  openBlocks.value = next
}

function expandActive() {
  openBlocks.value = new Set(activeModule.value.blocks.map(block => `${activeModule.value.id}:${block.title}`))
}

function collapseAll() {
  openBlocks.value = new Set()
}

function navigate(tab: string) {
  emit('navigate', tab)
}
</script>

<template>
  <div class="space-y-6">
    <HelpOverview
      :flows="systemFlows"
      @expand-active="expandActive"
      @collapse-all="collapseAll"
    />

    <section class="grid gap-6 lg:h-[calc(100vh-12rem)] lg:grid-cols-[300px_1fr] lg:overflow-hidden">
      <div class="space-y-4 lg:h-full lg:self-start lg:overflow-y-auto lg:pr-2">
        <HelpSearchPanel
          v-model="query"
          :shown="filteredModules.length"
          :total="modules.length"
        />

        <DocSidebar
          :items="sidebarItems"
          :active-id="activeModule.id"
          @select="selectModule"
        />
      </div>

      <main class="space-y-5 lg:h-full lg:overflow-y-auto lg:pr-2">
        <HelpHowToFlows
          v-if="filteredHowToFlows.length"
          :flows="filteredHowToFlows"
          @navigate="navigate"
        />

        <HelpUxNotes :items="uxImprovements" />

        <DocSection
          v-for="module in filteredModules"
          :key="module.id"
          :module="module"
          :open-blocks="openBlocks"
          @toggle="toggleBlock"
          @navigate="navigate"
        />

        <HelpEmptyState v-if="filteredModules.length === 0 && filteredHowToFlows.length === 0" />
      </main>
    </section>
  </div>
</template>
