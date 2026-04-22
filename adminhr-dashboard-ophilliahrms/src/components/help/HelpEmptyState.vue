<script setup lang="ts">
import { Search } from 'lucide-vue-next'
</script>

<template>
  <section class="rounded-lg border border-slate-200 bg-white p-10 text-center shadow-sm">
    <Search class="mx-auto h-8 w-8 text-slate-300" />
    <h3 class="mt-4 font-semibold text-slate-950">No documentation matches your search</h3>
    <p class="mt-2 text-sm text-slate-500">Try a module name such as payroll, leave, attendance, roles, or bulk upload.</p>
  </section>
</template>
