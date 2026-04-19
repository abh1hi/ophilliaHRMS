<script setup lang="ts">
import type { Company } from '../services/company.service'

defineProps<{
  companies: Company[]
  loading: boolean
}>()

const emit = defineEmits<{
  deactivate: [company: Company]
  reactivate: [company: Company]
}>()

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<template>
  <div class="rounded-xl border border-slate-800 overflow-hidden">
    <table class="w-full text-sm">
      <thead class="bg-slate-800/60 text-slate-400 text-xs uppercase tracking-wide">
        <tr>
          <th class="px-4 py-3 text-left font-medium">Company</th>
          <th class="px-4 py-3 text-left font-medium">Domain</th>
          <th class="px-4 py-3 text-left font-medium">Status</th>
          <th class="px-4 py-3 text-left font-medium">Created</th>
          <th class="px-4 py-3 text-right font-medium">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-800">
        <tr v-if="loading">
          <td colspan="5" class="px-4 py-8 text-center text-slate-500">Loading...</td>
        </tr>
        <tr v-else-if="companies.length === 0">
          <td colspan="5" class="px-4 py-8 text-center text-slate-500">No companies found</td>
        </tr>
        <tr
          v-for="company in companies"
          :key="company.id"
          class="bg-slate-900 hover:bg-slate-800/50 transition-colors"
        >
          <td class="px-4 py-3 text-white font-medium">{{ company.name }}</td>
          <td class="px-4 py-3 text-slate-400">{{ company.domain || '—' }}</td>
          <td class="px-4 py-3">
            <span
              :class="company.is_active
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : 'bg-red-500/15 text-red-400 border border-red-500/30'"
              class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
            >
              {{ company.is_active ? 'Active' : 'Inactive' }}
            </span>
          </td>
          <td class="px-4 py-3 text-slate-400">{{ formatDate(company.created_at) }}</td>
          <td class="px-4 py-3 text-right space-x-2">
            <button
              v-if="company.is_active"
              @click="emit('deactivate', company)"
              class="text-xs text-red-400 hover:text-red-300 border border-red-800 hover:border-red-600 px-2.5 py-1 rounded-lg transition-colors"
            >
              Deactivate
            </button>
            <button
              v-else
              @click="emit('reactivate', company)"
              class="text-xs text-emerald-400 hover:text-emerald-300 border border-emerald-800 hover:border-emerald-600 px-2.5 py-1 rounded-lg transition-colors"
            >
              Reactivate
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
