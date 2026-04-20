<script setup lang="ts">
import { Info } from 'lucide-vue-next'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

defineProps<{ text: string }>()
</script>

<template>
  <TooltipProvider :delay-duration="200">
    <Tooltip>
      <TooltipTrigger as-child>
        <Info class="w-3.5 h-3.5 text-slate-400 cursor-help inline-block ml-1 align-middle hover:text-slate-600 transition-colors" />
      </TooltipTrigger>
      <TooltipContent class="max-w-xs text-xs leading-relaxed">{{ text }}</TooltipContent>
    </Tooltip>
  </TooltipProvider>
</template>
