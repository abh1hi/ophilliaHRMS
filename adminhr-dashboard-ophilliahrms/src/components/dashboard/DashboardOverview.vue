<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Activity, Clock, CalendarCheck, AlertCircle, TrendingUp, ArrowUpRight } from 'lucide-vue-next'
import StatCard from '../ui/StatCard.vue'
import RecentActivityList from './RecentActivityList.vue'
import { apiFetchData } from '../../services/http'
import { Button } from '@/components/ui/button'

interface StatsResponse {
  total_employees: number
  active_employees: number
  total_departments: number
}

const router = useRouter()

const stats = ref<StatsResponse>({ total_employees: 0, active_employees: 0, total_departments: 0 })
const pendingLeaves = ref(0)
const pendingAttendance = ref(0)
const upcomingPayroll = ref<string | null>(null)
const openOvertimeRequests = ref(0)
const activities = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [statsData, leavesData, attendanceData, overtimeData, payrollData] = await Promise.allSettled([
      apiFetchData<StatsResponse>('/employees/stats'),
      apiFetchData<any>('/leaves/requests?status=pending&limit=1'),
      apiFetchData<any>('/attendance/requests?status=pending&limit=1'),
      apiFetchData<any>('/overtime/requests?status=pending&limit=1'),
      apiFetchData<any>('/payroll/runs?limit=5'),
    ])

    if (statsData.status === 'fulfilled') stats.value = statsData.value

    if (leavesData.status === 'fulfilled') {
      pendingLeaves.value = leavesData.value?.total ?? (Array.isArray(leavesData.value) ? leavesData.value.length : 0)
    }

    if (attendanceData.status === 'fulfilled') {
      pendingAttendance.value = attendanceData.value?.total ?? (Array.isArray(attendanceData.value) ? attendanceData.value.length : 0)
    }

    if (overtimeData.status === 'fulfilled') {
      openOvertimeRequests.value = overtimeData.value?.total ?? (Array.isArray(overtimeData.value) ? overtimeData.value.length : 0)
    }

    if (payrollData.status === 'fulfilled') {
      const runs = payrollData.value?.runs ?? payrollData.value ?? []
      const nextRun = runs.find((r: any) => r.status === 'open' || r.status === 'draft')
      upcomingPayroll.value = nextRun?.period_start ?? null
    }
  } catch (err) {
    console.error('Dashboard stats fetch failed', err)
  } finally {
    loading.value = false
  }
})

function navigate(tab: string) {
  router.push({ query: { tab } })
}
</script>

<template>
  <div class="space-y-12 animate-in fade-in slide-in-from-bottom-5 duration-700">
    <!-- Primary Stats -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <StatCard
        label="Total Employees"
        :value="loading ? '…' : stats.total_employees"
        sub="All registered employees"
        glow-color="#6366f1"
      />
      <StatCard
        label="Active Employees"
        :value="loading ? '…' : stats.active_employees"
        sub="Currently active"
        glow-color="#10b981"
      />
      <StatCard
        label="Departments"
        :value="loading ? '…' : stats.total_departments"
        sub="Across your organisation"
        glow-color="#a855f7"
      />
    </div>

    <!-- Pending Action Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-5">
      <button
        @click="navigate('leave-requests')"
        class="group bg-white/40 backdrop-blur-xl rounded-[24px] border border-white/20 p-6 text-left hover:bg-white/60 hover:border-amber-100 hover:shadow-lg transition-all duration-300"
      >
        <div class="flex items-center justify-between mb-3">
          <div class="h-9 w-9 rounded-xl bg-amber-50 flex items-center justify-center">
            <CalendarCheck class="w-4 h-4 text-amber-600" />
          </div>
          <ArrowUpRight class="w-4 h-4 text-slate-300 group-hover:text-amber-500 transition-colors" />
        </div>
        <p class="text-3xl font-black text-slate-900 mb-1">{{ loading ? '…' : pendingLeaves }}</p>
        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Pending Leaves</p>
      </button>

      <button
        @click="navigate('attendance-adjustments')"
        class="group bg-white/40 backdrop-blur-xl rounded-[24px] border border-white/20 p-6 text-left hover:bg-white/60 hover:border-blue-100 hover:shadow-lg transition-all duration-300"
      >
        <div class="flex items-center justify-between mb-3">
          <div class="h-9 w-9 rounded-xl bg-blue-50 flex items-center justify-center">
            <Clock class="w-4 h-4 text-blue-600" />
          </div>
          <ArrowUpRight class="w-4 h-4 text-slate-300 group-hover:text-blue-500 transition-colors" />
        </div>
        <p class="text-3xl font-black text-slate-900 mb-1">{{ loading ? '…' : pendingAttendance }}</p>
        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Pending Attendance</p>
      </button>

      <button
        @click="navigate('payroll-runs')"
        class="group bg-white/40 backdrop-blur-xl rounded-[24px] border border-white/20 p-6 text-left hover:bg-white/60 hover:border-emerald-100 hover:shadow-lg transition-all duration-300"
      >
        <div class="flex items-center justify-between mb-3">
          <div class="h-9 w-9 rounded-xl bg-emerald-50 flex items-center justify-center">
            <TrendingUp class="w-4 h-4 text-emerald-600" />
          </div>
          <ArrowUpRight class="w-4 h-4 text-slate-300 group-hover:text-emerald-500 transition-colors" />
        </div>
        <p class="text-3xl font-black text-slate-900 mb-1 truncate">{{ loading ? '…' : upcomingPayroll ?? 'N/A' }}</p>
        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Upcoming Payroll</p>
      </button>

      <button
        @click="navigate('overtime-requests')"
        class="group bg-white/40 backdrop-blur-xl rounded-[24px] border border-white/20 p-6 text-left hover:bg-white/60 hover:border-rose-100 hover:shadow-lg transition-all duration-300"
      >
        <div class="flex items-center justify-between mb-3">
          <div class="h-9 w-9 rounded-xl bg-rose-50 flex items-center justify-center">
            <AlertCircle class="w-4 h-4 text-rose-600" />
          </div>
          <ArrowUpRight class="w-4 h-4 text-slate-300 group-hover:text-rose-500 transition-colors" />
        </div>
        <p class="text-3xl font-black text-slate-900 mb-1">{{ loading ? '…' : openOvertimeRequests }}</p>
        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Open Overtime Req.</p>
      </button>
    </div>

    <!-- Recent Activity -->
    <div class="bg-white/30 backdrop-blur-2xl border border-white/60 shadow-[0_32px_64px_-16px_rgba(0,0,0,0.05)] rounded-[48px] p-12 lg:p-16 relative overflow-hidden group">
      <div class="absolute -right-20 -top-20 w-80 h-80 bg-slate-50 rounded-full blur-[100px] opacity-20 group-hover:opacity-40 transition-opacity" />

      <div class="relative z-10">
        <div class="flex flex-col sm:flex-row items-center justify-between mb-12 gap-6">
          <div class="space-y-1">
            <h3 class="text-3xl font-black text-slate-900 uppercase tracking-tighter flex items-center gap-3">
              <Activity class="w-8 h-8 text-slate-400" />
              Recent Activity
            </h3>
            <p class="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400 pl-1">Latest actions across the HRMS</p>
          </div>
          <Button variant="outline" class="rounded-full h-12 px-8 border-slate-100 text-[10px] font-black uppercase tracking-widest hover:border-indigo-100 hover:text-indigo-600 transition-all shadow-sm">
            View All Logs
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
