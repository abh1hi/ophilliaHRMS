<script setup lang="ts">
import { ref, onMounted } from 'vue'
import StatCard from '../ui/StatCard.vue'
import RecentActivityList from './RecentActivityList.vue'
import { apiFetchData } from '../../services/http'

interface StatsResponse {
  total_employees: number
  active_employees: number
  total_departments: number
}

const stats = ref<StatsResponse>({ total_employees: 0, active_employees: 0, total_departments: 0 })
const activities = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await apiFetchData<StatsResponse>('/employees/stats')
    stats.value = data
  } catch (err) {
    console.error('Dashboard stats fetch failed', err)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-8">
    <!-- Stat Cards -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <StatCard
        label="Total Employees"
        :value="loading ? '…' : stats.total_employees"
        sub="registered in the system"
        glow-color="bg-emerald-100/50"
      />
      <StatCard
        label="Active Employees"
        :value="loading ? '…' : stats.active_employees"
        sub="currently active"
        glow-color="bg-blue-100/50"
      />
      <StatCard
        label="Departments"
        :value="loading ? '…' : stats.total_departments"
        sub="across the company"
        glow-color="bg-purple-100/50"
      />
    </div>

    <!-- Recent Activity -->
    <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)] rounded-[24px] p-8">
      <div class="flex items-center justify-between mb-8">
        <h3 class="text-xl font-bold text-slate-900">Recent Activity</h3>
        <button class="bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full px-5 py-2 text-sm font-medium transition-colors shadow-sm">
          View All
        </button>
      </div>
      <RecentActivityList :activities="activities" :loading="loading" />
    </div>
  </div>
</template>
