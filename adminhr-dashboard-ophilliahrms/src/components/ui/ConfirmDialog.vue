<script setup lang="ts">
import { AlertTriangle } from 'lucide-vue-next'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './alert-dialog'

const props = defineProps<{
  open: boolean
  title?: string
  message?: string
  confirmLabel?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

function updateOpen(val: boolean) {
  if (!val) emit('cancel')
}
</script>

<template>
  <AlertDialog :open="open" @update:open="updateOpen">
    <AlertDialogContent>
      <AlertDialogHeader>
        <div class="flex items-center gap-4">
          <div class="w-10 h-10 bg-destructive/10 rounded-full flex items-center justify-center shrink-0">
            <AlertTriangle class="w-5 h-5 text-destructive" />
          </div>
          <div>
            <AlertDialogTitle>{{ title || 'Are you sure?' }}</AlertDialogTitle>
            <AlertDialogDescription class="mt-1">
              {{ message || 'This action cannot be undone.' }}
            </AlertDialogDescription>
          </div>
        </div>
      </AlertDialogHeader>
      <AlertDialogFooter class="mt-4">
        <AlertDialogCancel @click="emit('cancel')">Cancel</AlertDialogCancel>
        <AlertDialogAction
          @click="emit('confirm')"
          :disabled="loading"
          class="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
        >
          {{ loading ? 'Processing...' : (confirmLabel || 'Delete') }}
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>

<style scoped>
/* Removed old transitions as Shadcn uses tailwindcss-animate */
</style>
