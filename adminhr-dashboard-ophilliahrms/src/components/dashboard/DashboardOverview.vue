<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Activity, Clock, CalendarCheck, AlertCircle, TrendingUp, ArrowUpRight } from 'lucide-vue-next'
import StatCard from '../ui/StatCard.vue'
import RecentActivityList from './RecentActivityList.vue'
import { apiFetchData } from '../../services/http'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

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
  <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
    <!-- Primary Stats -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
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
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <button
        v-for="action in [
          { label: 'Pending Leaves', value: pendingLeaves, icon: CalendarCheck, color: 'amber', tab: 'leave-requests' },
          { label: 'Pending Attendance', value: pendingAttendance, icon: Clock, color: 'blue', tab: 'attendance-adjustments' },
          { label: 'Upcoming Payroll', value: upcomingPayroll ?? 'N/A', icon: TrendingUp, color: 'emerald', tab: 'payroll-runs' },
          { label: 'Open Overtime Req.', value: openOvertimeRequests, icon: AlertCircle, color: 'rose', tab: 'overtime-requests' }
        ]"
        :key="action.label"
        @click="navigate(action.tab)"
        class="group bg-white rounded-xl border border-slate-200 p-5 text-left hover:border-slate-300 hover:shadow-sm transition-all duration-200"
      >
        <div class="flex items-center justify-between mb-4">
          <div :class="[`h-9 w-9 rounded-lg flex items-center justify-center bg-${action.color}-50`]">
            <component :is="action.icon" :class="[`w-5 h-5 text-${action.color}-600`]" />
          </div>
          <ArrowUpRight class="w-4 h-4 text-slate-300 group-hover:text-slate-900 transition-colors" />
        </div>
        <p class="text-2xl font-bold text-slate-900 mb-0.5 truncate">{{ loading ? '…' : action.value }}</p>
        <p class="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">{{ action.label }}</p>
      </button>
    </div>

    <!-- Recent Activity -->
    <Card class="border-slate-200 shadow-sm">
      <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-7">
        <div class="space-y-1">
          <CardTitle class="text-xl font-bold flex items-center gap-2">
            <Activity class="w-5 h-5 text-slate-400" />
            Recent Activity
          </CardTitle>
          <CardDescription class="text-xs">Latest actions across the HRMS portal</CardDescription>
        </div>
        <Button variant="outline" size="sm" class="h-9 px-4 text-xs font-semibold">
          View All Logs
          <ArrowUpRight class="w-3.5 h-3.5 ml-2" />
        </Button>
      </CardHeader>
      <CardContent>
        <div class="min-h-[300px]">
          <RecentActivityList :activities="activities" :loading="loading" />
        </div>
      </CardContent>
    </Card>
  </div>
</template>
