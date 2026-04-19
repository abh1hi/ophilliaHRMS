<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Activity, Layers, ArrowUpRight, Monitor, Zap } from 'lucide-vue-next'
import StatCard from '../ui/StatCard.vue'
import RecentActivityList from './RecentActivityList.vue'
import { apiFetchData } from '../../services/http'
import { Button } from '@/components/ui/button'

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
  <div class="space-y-12 animate-in fade-in slide-in-from-bottom-5 duration-700">
    <!-- Telemetry Clusters -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <StatCard
        label="Entity Population"
        :value="loading ? '…' : stats.total_employees"
        sub="Registered Manifests"
        glow-color="#6366f1"
      />
      <StatCard
        label="Operational Nodes"
        :value="loading ? '…' : stats.active_employees"
        sub="Active Session Layer"
        glow-color="#10b981"
      />
      <StatCard
        label="Domain Units"
        :value="loading ? '…' : stats.total_departments"
        sub="Operational Clusters"
        glow-color="#a855f7"
      />
    </div>

    <!-- Activity Stream Manifest -->
    <div class="bg-white/30 backdrop-blur-2xl border border-white/60 shadow-[0_32px_64px_-16px_rgba(0,0,0,0.05)] rounded-[48px] p-12 lg:p-16 relative overflow-hidden group">
      <div class="absolute -right-20 -top-20 w-80 h-80 bg-slate-50 rounded-full blur-[100px] opacity-20 group-hover:opacity-40 transition-opacity" />
      
      <div class="relative z-10">
        <div class="flex flex-col sm:flex-row items-center justify-between mb-12 gap-6">
          <div class="space-y-1">
            <h3 class="text-3xl font-black text-slate-900 uppercase tracking-tighter flex items-center gap-3">
              <Activity class="w-8 h-8 text-slate-400" />
              Real-time Ingestion Feed
            </h3>
            <p class="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400 pl-1">Asynchronous system telemetry</p>
          </div>
          <Button variant="outline" class="rounded-full h-12 px-8 border-slate-100 text-[10px] font-black uppercase tracking-widest hover:border-indigo-100 hover:text-indigo-600 transition-all shadow-sm">
            Access Full Logs
            <ArrowUpRight class="w-3.5 h-3.5 ml-2" />
          </Button>
        </div>

        <div class="min-h-[400px]">
          <RecentActivityList :activities="activities" :loading="loading" />
        </div>
      </div>
    </div>
  </div>
</template>
