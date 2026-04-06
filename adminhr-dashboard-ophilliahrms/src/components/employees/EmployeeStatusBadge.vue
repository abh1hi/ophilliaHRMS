<script setup lang="ts">
import BadgeChip from '../ui/BadgeChip.vue'
import type { Employee } from '../../services/employee.service'

defineProps<{ status: Employee['employment_status'] | string }>()
</script>

<template>
  <BadgeChip :status="status" />
</template>
