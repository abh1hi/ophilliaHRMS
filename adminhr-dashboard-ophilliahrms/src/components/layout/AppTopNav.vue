<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  LayoutDashboard,
  Users,
  Clock,
  CalendarDays,
  Wallet,
  Timer,
  Monitor,
  Zap,
  UserCircle,
  LogOut,
  ChevronDown,
  Building2,
  ArrowLeft,
  Search,
} from 'lucide-vue-next'
import { useCommandPaletteStore } from '../../stores/commandPalette.store'

const palette = useCommandPaletteStore()

const props = defineProps<{
  currentTab: string
  companyName?: string
  userRole?: string
  userName?: string
}>()

const emit = defineEmits<{
  (e: 'navigate', tab: string): void
  (e: 'logout'): void
}>()

const menuOpen = ref(false)

// Top-level sections shown in the nav bar
const sections = [
  { key: 'dashboard',    label: 'Dashboard',   icon: LayoutDashboard, defaultTab: 'dashboard'    },
  { key: 'employees',    label: 'Employees',   icon: Users,           defaultTab: 'employees'    },
  { key: 'attendance',   label: 'Attendance',  icon: Timer,           defaultTab: 'attendance' },
  { key: 'leaves',       label: 'Leaves',      icon: CalendarDays,    defaultTab: 'leave-periods' },
  { key: 'payroll',      label: 'Payroll',     icon: Wallet,          defaultTab: 'payroll'      },
  { key: 'shifts',       label: 'Shifts',      icon: Clock,           defaultTab: 'shift-types'  },
  { key: 'workspace',    label: 'Workspace',   icon: Monitor,         defaultTab: 'workspace-hub' },
  { key: 'hrsetup',      label: 'HR Setup',    icon: Zap,             defaultTab: 'departments'  },
]

// Map every tab to its parent section key
const tabToSection: Record<string, string> = {
  dashboard: 'dashboard',
  employees: 'employees',
  'employees-import-queue': 'employees',
  'attendance-records': 'attendance',
  attendance: 'attendance',
  'attendance-checkins': 'attendance',
  'attendance-requests': 'attendance',
  'attendance-bulk': 'attendance',
  'attendance-upload': 'attendance',
  'leave-periods': 'leaves',
  'holiday-lists': 'leaves',
  'leave-policies': 'leaves',
  'leave-policy-assignments': 'leaves',
  'leave-allocations': 'leaves',
  'leave-types': 'leaves',
  'leave-balance': 'leaves',
  'leave-block-lists': 'leaves',
  'compensatory-leave': 'leaves',
  'leave-encashments': 'leaves',
  'leave-ledger': 'leaves',
  payroll: 'payroll',
  'shift-types': 'shifts',
  'shift-locations': 'shifts',
  'shift-requests': 'shifts',
  'shift-schedules': 'shifts',
  roster: 'shifts',
  'workspace-hub': 'workspace',
  'workspace-calendar': 'workspace',
  'workspace-board': 'workspace',
  'workspace-notes': 'workspace',
  'workspace-settings': 'workspace',
  departments: 'hrsetup',
  branches: 'hrsetup',
  designations: 'hrsetup',
  'employment-types': 'hrsetup',
  'employee-grades': 'hrsetup',
  'employee-groups': 'hrsetup',
  profile: 'profile',
}

const activeSection = computed(() => tabToSection[props.currentTab] ?? 'dashboard')

function handleSectionClick(section: typeof sections[0]) {
  emit('navigate', section.defaultTab)
}

function onProfile() {
  menuOpen.value = false
  emit('navigate', 'profile')
}

function onLogout() {
  menuOpen.value = false
  emit('logout')
}
</script>

<template>
  <header class="h-14 bg-white border-b border-slate-200 flex items-center px-4 gap-0 shrink-0 z-30 relative">
    <!-- Logo + company -->
    <button
      @click="emit('navigate', 'dashboard')"
      class="flex items-center gap-2.5 mr-6 shrink-0 group"
    >
      <div class="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-sm group-hover:bg-indigo-700 transition-colors">
        <span class="text-white text-sm font-bold font-serif italic select-none">O</span>
      </div>
      <span class="text-sm font-semibold text-slate-800 truncate max-w-[140px] hidden sm:block">
        {{ companyName || 'Ophillia HRMS' }}
      </span>
    </button>

    <!-- Section tabs -->
    <nav class="flex items-center gap-0.5 flex-1 overflow-x-auto no-scrollbar">
      <button
        v-for="section in sections"
        :key="section.key"
        @click="handleSectionClick(section)"
        :class="[
          'flex items-center gap-1.5 px-3 h-14 text-sm font-medium border-b-2 transition-colors whitespace-nowrap shrink-0',
          activeSection === section.key
            ? 'border-indigo-600 text-indigo-700'
            : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
        ]"
      >
        <component :is="section.icon" class="w-4 h-4 shrink-0" />
        {{ section.label }}
      </button>
    </nav>

    <!-- CMD+K search -->
    <button
      @click="palette.open()"
      class="hidden lg:flex items-center gap-2 h-8 pl-3 pr-3 rounded-lg border border-slate-200 text-slate-400 hover:border-slate-300 hover:text-slate-600 bg-slate-50 transition-all text-xs font-medium shrink-0 mx-2"
    >
      <Search class="w-3.5 h-3.5" />
      <span class="text-slate-400">Search</span>
      <kbd class="bg-white border border-slate-200 text-slate-500 text-[10px] font-bold px-1 py-0.5 rounded ml-1">⌘K</kbd>
    </button>

    <!-- User menu -->
    <div class="flex items-center gap-3 shrink-0 ml-2">
      <div class="hidden sm:block text-right">
        <p class="text-xs font-semibold text-slate-800 leading-tight">{{ userName || '—' }}</p>
        <p class="text-xs text-slate-400 capitalize leading-tight">{{ userRole?.replace('_', ' ') }}</p>
      </div>

      <div class="relative">
        <button
          @click="menuOpen = !menuOpen"
          class="flex items-center gap-1.5 h-9 px-2.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all"
        >
          <UserCircle class="w-5 h-5" />
          <ChevronDown :class="['w-3.5 h-3.5 transition-transform', menuOpen ? 'rotate-180' : '']" />
        </button>

        <Transition name="drop">
          <div
            v-if="menuOpen"
            class="absolute top-11 right-0 w-52 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden z-50 py-1"
          >
            <div class="px-3 py-2 border-b border-slate-100">
              <p class="text-xs text-slate-400 mb-0.5">Signed in as</p>
              <p class="text-sm font-medium text-slate-800 truncate">{{ userName || '—' }}</p>
            </div>

            <button
              @click="onProfile"
              class="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <UserCircle class="w-4 h-4 text-slate-400" />
              My Profile
            </button>

            <div class="border-t border-slate-100 mt-1" />
            <button
              @click="onLogout"
              class="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-rose-600 hover:bg-rose-50 transition-colors"
            >
              <LogOut class="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Dropdown backdrop -->
    <div
      v-if="menuOpen"
      class="fixed inset-0 z-40"
      @click="menuOpen = false"
    />
  </header>
</template>

<style scoped>
.drop-enter-active, .drop-leave-active { transition: all 0.15s ease; }
.drop-enter-from, .drop-leave-to { opacity: 0; transform: translateY(-4px) scale(0.98); }
.drop-enter-to, .drop-leave-from { opacity: 1; transform: translateY(0) scale(1); }

.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
