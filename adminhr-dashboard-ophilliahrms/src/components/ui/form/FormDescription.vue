<script setup>
import { cn } from "@/lib/utils";
import { useFormField } from "./useFormField";

const props = defineProps({
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
});

const { formDescriptionId } = useFormField();
</script>

<template>
  <p
    :id="formDescriptionId"
    :class="cn('text-sm text-muted-foreground', props.class)"
  >
    <slot />
  </p>
</template>
