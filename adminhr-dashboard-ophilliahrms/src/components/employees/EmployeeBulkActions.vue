<script setup lang="ts">
import { Users, Download, RefreshCw } from 'lucide-vue-next'
import { Button } from '../ui/button'

const props = defineProps<{
  selectedCount: number
  bulkInviting: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'bulk-invite'): void
  (e: 'export'): void
  (e: 'refresh'): void
}>()
</script>

<template>
  <div class="flex items-center gap-2 flex-wrap">
    <!-- Bulk Invite — only when not_registered employees are selected -->
    <Button
      v-if="selectedCount > 0"
      @click="emit('bulk-invite')"
      :disabled="bulkInviting"
      class="rounded-full gap-2 px-4 h-9 bg-blue-600 text-white hover:bg-blue-700"
    >
      <Users class="w-3.5 h-3.5" />
      {{ bulkInviting ? 'Inviting…' : `Invite ${selectedCount} Selected` }}
    </Button>

    <!-- Export CSV — always visible -->
    <Button
      variant="outline"
      @click="emit('export')"
      class="rounded-full gap-2 px-4 h-9"
    >
      <Download class="w-3.5 h-3.5" />
      Export CSV
    </Button>

    <Button
      variant="outline"
      @click="emit('refresh')"
      :disabled="loading"
      class="rounded-full gap-2 px-4 h-9"
      title="Refresh list"
    >
      <RefreshCw :class="['w-3.5 h-3.5', loading ? 'animate-spin' : '']" />
      Refresh
    </Button>
  </div>
</template>
