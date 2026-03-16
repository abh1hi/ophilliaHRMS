<template>
  <div>
    <!-- ── Saffron Header ── -->
    <div class="saffron-header px-5 pt-12 pb-7">
      <div class="d-flex align-center gap-4">
        <v-avatar size="52" style="background:rgba(255,255,255,0.25); border:2px solid rgba(255,255,255,0.5);">
          <span class="text-h6 font-weight-black" style="color:#FFFFFF;">{{ initials }}</span>
        </v-avatar>
        <div class="flex-grow-1">
          <p class="text-body-2 mb-0" style="color:rgba(255,255,255,0.8);">{{ greeting }},</p>
          <h1 class="text-h6 font-weight-bold" style="color:#FFFFFF;">{{ emp.first_name }} {{ emp.last_name }}</h1>
          <p class="text-caption" style="color:rgba(255,255,255,0.7);">{{ emp.designation }}<span v-if="emp.department"> · {{ emp.department }}</span></p>
        </div>
        <v-chip :color="emp.employment_status === 'active' ? '#C8E6C9' : '#FFE0B2'" size="small" variant="flat" style="color:#1C1B1F; font-weight:600;">{{ emp.employment_status }}</v-chip>
      </div>
    </div>

    <div class="pa-4 pb-nav">

      <!-- Attendance status -->
      <v-card class="mb-5" elevation="1" style="border-left:4px solid #FF9933;">
        <v-card-text class="pa-4">
          <div class="d-flex align-center gap-3">
            <v-avatar :color="statusColor" variant="tonal" size="46">
              <v-icon :color="statusColor" size="22">{{ statusIcon }}</v-icon>
            </v-avatar>
            <div class="flex-grow-1">
              <p class="text-subtitle-2 font-weight-bold mb-0">{{ statusLabel }}</p>
              <p v-if="todayRecord?.clock_in" class="text-body-2 mb-0" style="color:#49454F;">
                In: {{ formatTime(todayRecord.clock_in) }}<template v-if="todayRecord.clock_out"> · Out: {{ formatTime(todayRecord.clock_out) }}</template>
              </p>
              <p class="text-caption" style="color:#79747E;">{{ todayDate }}</p>
            </div>
            <v-chip v-if="pendingCount > 0" color="warning" size="small" variant="tonal">{{ pendingCount }} pending</v-chip>
          </div>
        </v-card-text>
      </v-card>

      <!-- Quick actions -->
      <p class="section-label mb-3">Quick Actions</p>
      <v-row dense class="mb-5">
        <v-col cols="4" v-for="a in quickActions" :key="a.page">
          <v-card :id="'go-' + a.page + '-btn'" elevation="0" class="text-center" style="border:1px solid rgba(255,153,51,0.2); cursor:pointer;" @click="$emit('navigate', a.page)">
            <v-card-text class="py-5 px-2">
              <v-avatar color="primary-container" size="44" class="mb-2">
                <v-icon color="primary" size="22">{{ a.icon }}</v-icon>
              </v-avatar>
              <p class="text-caption font-weight-bold" style="color:#1C1B1F;">{{ a.label }}</p>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Today's tasks -->
      <template v-if="todayRecord?.tasks?.length">
        <p class="section-label mb-3">Today's Tasks</p>
        <v-card elevation="0" class="mb-5" style="border:1px solid rgba(255,153,51,0.15);">
          <v-list density="compact" bg-color="transparent" class="py-1">
            <v-list-item v-for="t in todayRecord.tasks" :key="t.id" class="px-4">
              <template #prepend>
                <v-icon :color="taskColor(t.status)" size="16" class="mr-3">{{ taskIcon(t.status) }}</v-icon>
              </template>
              <v-list-item-title class="text-body-2">{{ t.title }}</v-list-item-title>
              <template #append>
                <v-chip :color="taskColor(t.status)" size="x-small" variant="tonal">{{ taskLabel(t.status) }}</v-chip>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </template>

      <!-- Day summary (after punch-out) -->
      <template v-if="todayRecord?.work_hours != null">
        <p class="section-label mb-3">Today's Summary</p>
        <v-card elevation="0" style="border:1px solid rgba(255,153,51,0.15);">
          <v-card-text class="pa-4">
            <v-row>
              <v-col cols="4" class="text-center">
                <p class="text-h6 font-weight-black" style="color:#FF9933;">{{ todayRecord.work_hours?.toFixed(1) }}h</p>
                <p class="text-caption" style="color:#79747E;">Work Hours</p>
              </v-col>
              <v-col cols="4" class="text-center border-x">
                <p class="text-h6 font-weight-black" style="color:#B35C00;">{{ todayRecord.overtime_hours?.toFixed(1) }}h</p>
                <p class="text-caption" style="color:#79747E;">Overtime</p>
              </v-col>
              <v-col cols="4" class="text-center">
                <p class="text-h6 font-weight-black" style="color:#FF9933;">
                  <template v-if="todayRecord.day_rating">{{ '⭐'.repeat(todayRecord.day_rating) }}</template>
                  <template v-else>—</template>
                </p>
                <p class="text-caption" style="color:#79747E;">Rating</p>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </template>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getTodayRecord } from '../services/attendance'
import type { AttendanceRecord } from '../services/attendance'

const props = defineProps<{ employee: any }>()
defineEmits<{ navigate: [page: string] }>()
const emp = computed(() => props.employee)
const todayRecord = ref<AttendanceRecord | null>(null)

const quickActions = [
  { page: 'attendance', icon: 'mdi-clipboard-check-outline', label: 'Attendance' },
  { page: 'leave',      icon: 'mdi-calendar-multiselect',    label: 'Leave'      },
  { page: 'profile',    icon: 'mdi-account-outline',         label: 'Profile'    },
]

const initials     = computed(() => `${emp.value?.first_name?.[0] ?? ''}${emp.value?.last_name?.[0] ?? ''}`.toUpperCase())
const greeting     = computed(() => { const h = new Date().getHours(); return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening' })
const todayDate    = computed(() => new Date().toLocaleDateString('en-IN', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }))
const statusColor  = computed(() => !todayRecord.value ? 'warning' : todayRecord.value.clock_out ? 'success' : 'primary')
const statusIcon   = computed(() => !todayRecord.value ? 'mdi-clock-outline' : todayRecord.value.clock_out ? 'mdi-check-circle-outline' : 'mdi-timeline-clock-outline')
const statusLabel  = computed(() => !todayRecord.value ? 'Not yet punched in today' : todayRecord.value.clock_out ? 'Day complete — punched out' : 'Currently working')
const pendingCount = computed(() => (todayRecord.value?.tasks ?? []).filter(t => t.status === 'pending').length)

function formatTime(iso: string) { return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) }
function taskColor(s: string) { return ({ pending: 'warning', completed: 'success', partially_completed: 'primary', not_completed: 'error' } as any)[s] ?? 'default' }
function taskIcon(s: string)  { return ({ pending: 'mdi-circle-outline', completed: 'mdi-check-circle', partially_completed: 'mdi-circle-half-full', not_completed: 'mdi-close-circle' } as any)[s] ?? 'mdi-circle' }
function taskLabel(s: string) { return ({ pending: 'Pending', completed: 'Done', partially_completed: 'Partial', not_completed: 'Not Done' } as any)[s] ?? s }

onMounted(async () => { try { todayRecord.value = await getTodayRecord() } catch { /* no record */ } })
</script>
