<script setup lang="ts">
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from './sheet'

const props = defineProps<{
  open: boolean
  title: string
  subtitle?: string
  width?: string // e.g. 'sm:max-w-xl'
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

function updateOpen(val: boolean) {
  if (!val) {
    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur()
    }
    emit('close')
  }
}
</script>

<template>
  <Sheet :open="open" @update:open="updateOpen">
    <SheetContent :class="['flex flex-col h-full', width || 'sm:max-w-2xl']" side="right">
      <SheetHeader class="text-left">
        <SheetTitle class="text-xl font-bold">{{ title }}</SheetTitle>
        <SheetDescription v-if="subtitle" class="text-sm">
          {{ subtitle }}
        </SheetDescription>
        <SheetDescription v-else class="sr-only">
          {{ title }}
        </SheetDescription>
      </SheetHeader>
      
      <!-- Scrollable Content -->
      <div class="flex-1 overflow-y-auto py-6 -mx-6 px-6">
        <slot />
      </div>

      <!-- Footer -->
      <div v-if="$slots.footer" class="shrink-0 border-t border-border pt-6">
        <slot name="footer" />
      </div>
    </SheetContent>
  </Sheet>
</template>

<style scoped>
/* Removed old transitions as Shadcn uses tailwindcss-animate */
</style>
