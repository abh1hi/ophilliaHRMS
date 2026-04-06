<script setup lang="ts">
defineProps<{ tabs: { key: string; label: string }[]; activeTab: string }>()
defineEmits<{ (e: 'tab', key: string): void }>()
</script>

<template>
  <div class="space-y-6">
    <!-- Sub-tab pills -->
    <div class="flex flex-wrap gap-2">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="$emit('tab', tab.key)"
        :class="[
          'px-4 py-2 rounded-full text-sm font-semibold transition-all duration-200',
          activeTab === tab.key
            ? 'bg-slate-900 text-white shadow-sm'
            : 'bg-white/60 border border-slate-200 text-slate-500 hover:border-slate-300 hover:text-slate-800'
        ]"
      >
        {{ tab.label }}
      </button>
    </div>
    <!-- Content -->
    <slot />
  </div>
</template>
