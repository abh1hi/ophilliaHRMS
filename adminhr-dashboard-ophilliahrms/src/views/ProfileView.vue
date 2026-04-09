<script setup lang="ts">
// Profile is now embedded inside DashboardView as an inline tab.
// This standalone route redirects there so old links still work.
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  router.replace({ name: 'Dashboard', query: { tab: 'profile' } })
})
</script>

<template>
  <div />
</template>
