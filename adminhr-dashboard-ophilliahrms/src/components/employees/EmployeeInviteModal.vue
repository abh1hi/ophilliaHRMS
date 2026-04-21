<script setup lang="ts">
import { ref } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog'
import { Button } from '../ui/button'
import { Textarea } from '../ui/textarea'
import { Copy, Check as CheckIcon } from 'lucide-vue-next'
import type { SendInviteResponse } from '../../services/employee.service'

const props = defineProps<{
  open: boolean
  inviteResult: SendInviteResponse | null
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
}>()

const copySuccess = ref(false)

async function copyInviteUrl() {
  if (!props.inviteResult?.invite_url) return
  try {
    await navigator.clipboard.writeText(props.inviteResult.invite_url)
    copySuccess.value = true
    setTimeout(() => { copySuccess.value = false }, 2000)
  } catch (err) {
    console.error('Failed to copy', err)
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>Invite Link Ready</DialogTitle>
        <DialogDescription v-if="inviteResult">
          Share this link with <span class="font-bold text-foreground">{{ inviteResult.email }}</span>. It expires on
          {{ inviteResult.expires_at ? new Date(inviteResult.expires_at).toLocaleDateString() : '7 days from now' }}.
        </DialogDescription>
      </DialogHeader>
      
      <div class="mt-4" v-if="inviteResult">
        <Textarea
          readonly
          :value="inviteResult.invite_url"
          rows="3"
          class="font-mono text-xs bg-muted resize-none focus-visible:ring-0"
        />
      </div>

      <DialogFooter class="flex justify-end gap-2 mt-4">
        <Button variant="ghost" @click="emit('update:open', false)">
          Close
        </Button>
        <Button @click="copyInviteUrl" class="gap-2 px-6">
          <CheckIcon v-if="copySuccess" class="w-4 h-4" />
          <Copy v-else class="w-4 h-4" />
          {{ copySuccess ? 'Copied!' : 'Copy Link' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
