<script setup lang="ts">
import {
  LayoutDashboard,
  Users,
  Calendar,
  UserCircle,
  ArrowLeft,
  Building2,
  Briefcase,
  GitBranch,
  Star,
  Users2,
  Tag,
  ChevronDown,
  ChevronRight,
  LogOut,
  Clock,
  MapPin,
  CalendarRange,
  ArrowLeftRight,
  LayoutGrid,
  CalendarCheck,
  LogIn,
  FileText,
  CheckSquare,
  Upload,
  Umbrella,
  CalendarDays,
  Shield,
  BookOpen,
  Slash,
  Coins,
  BarChart3,
  List,
  Kanban,
  StickyNote,
  Settings,
  Wallet,
  Database,
  Activity,
  TrendingUp,
  Settings2,
  Monitor,
  HelpCircle,
  PieChart
} from 'lucide-vue-next'
import { ref } from 'vue'

const props = defineProps<{
  currentTab: string
  companyName?: string
  userRole?: string
}>()

const emit = defineEmits<{
  (e: 'navigate', tab: string): void
  (e: 'logout'): void
}>()

const hrSetupOpen = ref(false)
const shiftOpen = ref(false)
const attendanceOpen = ref(false)
const employeesOpen = ref(false)
const leaveOpen = ref(false)
const workspaceOpen = ref(false)
const overtimeOpen = ref(false)

const mainNav = [
  { key: 'dashboard', label: 'Dashboard',  icon: LayoutDashboard, subtitle: 'Company overview'    },
  { key: 'payroll',   label: 'Payroll',    icon: Wallet,           subtitle: 'Payroll management' },
]

const employeesNav = [
  { key: 'employees',              label: 'Employee Directory', icon: Users     },
  { key: 'employees-import-queue', label: 'Bulk Import',        icon: Database  },
]

const hrSetupNav = [
  { key: 'departments',      label: 'Departments',      icon: Building2 },
  { key: 'branches',         label: 'Branches',         icon: GitBranch },
  { key: 'designations',     label: 'Designations',     icon: Briefcase },
  { key: 'employment-types', label: 'Employment Types', icon: Tag       },
  { key: 'employee-grades',  label: 'Employee Grades',  icon: Star      },
  { key: 'employee-groups',  label: 'Employee Groups',  icon: Users2    },
]

const shiftNav = [
  { key: 'shift-types',       label: 'Shift Types',       icon: Clock          },
  { key: 'shift-locations',   label: 'Shift Locations',   icon: MapPin         },
  { key: 'shift-requests',    label: 'Shift Requests',    icon: ArrowLeftRight },
  { key: 'shift-schedules',   label: 'Shift Schedules',   icon: LayoutGrid     },
  { key: 'roster',            label: 'Roster',            icon: Calendar       },
]

const attendanceNav = [
  { key: 'attendance-records',              label: 'Attendance Records',   icon: CalendarCheck },
  { key: 'attendance-checkins',             label: 'Check-ins',            icon: LogIn         },
  { key: 'attendance-requests',             label: 'Attendance Adjustments', icon: FileText    },
  { key: 'attendance-bulk',                 label: 'Bulk Attendance',      icon: CheckSquare   },
  { key: 'attendance-upload',               label: 'Import from Biometric', icon: Upload       },
  { key: 'holiday-calendars-attendance',    label: 'Holiday Calendars',    icon: CalendarDays  },
]

const leaveNav = [
  { key: 'leave-periods',            label: 'Leave Periods',     icon: CalendarDays  },
  { key: 'holiday-lists',            label: 'Holiday Lists',     icon: Umbrella      },
  { key: 'leave-types',              label: 'Leave Types',       icon: Tag           },
  { key: 'leave-policies',           label: 'Leave Policies',    icon: Shield        },
  { key: 'leave-policy-assignments', label: 'Policy Assignments', icon: BookOpen     },
  { key: 'leave-allocations',        label: 'Leave Allocations', icon: List          },
  { key: 'leave-balance',            label: 'Leave Balances',    icon: PieChart      },
  { key: 'leave-block-lists',        label: 'Leave Block Lists', icon: Slash         },
  { key: 'compensatory-leave',       label: 'Compensatory Leave', icon: CalendarCheck},
  { key: 'leave-encashments',        label: 'Leave Encashment',  icon: Coins         },
  { key: 'leave-ledger',             label: 'Leave Ledger',      icon: BarChart3     },
]

const overtimeNav = [
  { key: 'ot-policies', label: 'Overtime Policies', icon: Settings2  },
  { key: 'ot-records',  label: 'Overtime Records',  icon: Clock      },
  { key: 'ot-requests', label: 'Overtime Requests', icon: FileText   },
  { key: 'ot-reports',  label: 'Overtime Reports',  icon: BarChart3  },
]

const workspaceNav = [
  { key: 'workspace-hub',      label: 'Team Hub',     icon: LayoutGrid  },
  { key: 'workspace-calendar', label: 'Calendar',     icon: Calendar    },
  { key: 'workspace-board',    label: 'Task Board',   icon: Kanban      },
  { key: 'workspace-notes',    label: 'Notes',        icon: StickyNote  },
  { key: 'workspace-settings', label: 'Settings',     icon: Settings    },
]

const employeesNavKeys  = employeesNav.map(n => n.key)
const hrSetupKeys       = hrSetupNav.map(n => n.key)
const shiftNavKeys      = shiftNav.map(n => n.key)
const attendanceNavKeys = attendanceNav.map(n => n.key)
const leaveNavKeys      = leaveNav.map(n => n.key)
const overtimeNavKeys   = overtimeNav.map(n => n.key)
const workspaceNavKeys  = workspaceNav.map(n => n.key)
</script>

<template>
  <aside class="w-80 h-screen bg-white/40 backdrop-blur-2xl border-r border-white/20 p-8 flex flex-col pt-12 relative z-20 shrink-0 shadow-[4px_0_24px_-12px_rgba(0,0,0,0.05)]">
    <!-- Brand -->
    <div class="flex items-center space-x-4 mb-14 pl-2 group cursor-pointer" @click="emit('navigate', 'dashboard')">
      <div class="w-12 h-12 bg-slate-900 rounded-[18px] flex items-center justify-center shadow-xl shadow-slate-200/50 shrink-0 transition-transform group-hover:scale-105 group-active:scale-95 duration-300">
        <span class="text-white text-xl font-bold font-serif leading-none italic select-none">O</span>
      </div>
      <div class="overflow-hidden space-y-0.5">
        <div class="font-black text-sm uppercase tracking-widest text-slate-900 truncate leading-none">{{ companyName || 'Ophillia HRMS' }}</div>
        <div class="text-[9px] text-slate-400 font-bold uppercase tracking-[0.2em]">HR Management</div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 space-y-2 overflow-y-auto pr-3 no-scrollbar pb-10">
      <div class="space-y-1">
        <button
          v-for="item in mainNav"
          :key="item.key"
          @click="emit('navigate', item.key)"
          :class="[
            'w-full flex items-center space-x-4 px-5 py-4 rounded-[22px] transition-all duration-500 group relative overflow-hidden',
            currentTab === item.key
              ? 'bg-slate-900 text-white shadow-2xl shadow-slate-200 active:scale-95'
              : 'text-slate-500 hover:bg-white hover:text-slate-900 hover:shadow-sm'
          ]"
        >
          <div :class="['w-8 h-8 rounded-xl flex items-center justify-center transition-colors', currentTab === item.key ? 'bg-white/10' : 'bg-slate-50 group-hover:bg-white']">
            <component :is="item.icon" class="w-4 h-4" />
          </div>
          <div class="text-left">
            <div class="text-[11px] font-black uppercase tracking-widest">{{ item.label }}</div>
            <div :class="['text-[9px] font-bold uppercase tracking-tight transition-colors', currentTab === item.key ? 'text-slate-400' : 'text-slate-300 group-hover:text-slate-400']">{{ item.subtitle }}</div>
          </div>
        </button>
      </div>

      <!-- Collapsible Clusters -->
      <div v-for="cluster in [
        { label: 'Employees',  icon: Users,       open: employeesOpen,  toggle: () => employeesOpen  = !employeesOpen,  items: employeesNav,  keys: employeesNavKeys,  subtitle: 'Workforce management' },
        { label: 'Attendance', icon: Activity,    open: attendanceOpen, toggle: () => attendanceOpen = !attendanceOpen, items: attendanceNav, keys: attendanceNavKeys, subtitle: 'Time & Attendance'    },
        { label: 'Overtime',   icon: TrendingUp,  open: overtimeOpen,   toggle: () => overtimeOpen   = !overtimeOpen,   items: overtimeNav,   keys: overtimeNavKeys,   subtitle: 'Overtime management'  },
        { label: 'Leave',      icon: Umbrella,    open: leaveOpen,      toggle: () => leaveOpen      = !leaveOpen,      items: leaveNav,      keys: leaveNavKeys,      subtitle: 'Leave management'     },
        { label: 'Workspace',  icon: Monitor,     open: workspaceOpen,  toggle: () => workspaceOpen  = !workspaceOpen,  items: workspaceNav,  keys: workspaceNavKeys,  subtitle: 'Shared environment'   },
        { label: 'HR Setup',   icon: Settings2,   open: hrSetupOpen,    toggle: () => hrSetupOpen    = !hrSetupOpen,    items: hrSetupNav,    keys: hrSetupKeys,       subtitle: 'Core Governance'      },
        { label: 'Shifts',     icon: Clock,       open: shiftOpen,      toggle: () => shiftOpen      = !shiftOpen,      items: shiftNav,      keys: shiftNavKeys,      subtitle: 'Shift management'     },
      ]" :key="cluster.label" class="pt-2">
        <button
          @click="cluster.toggle()"
          :class="[
            'w-full flex items-center justify-between px-5 py-3.5 rounded-[20px] transition-all duration-300 group',
            cluster.keys.includes(currentTab)
              ? 'bg-slate-50/50 text-slate-900 shadow-inner'
              : 'text-slate-500 hover:bg-white hover:text-slate-900'
          ]"
        >
          <div class="flex items-center space-x-4">
            <div :class="['w-7 h-7 rounded-lg flex items-center justify-center transition-colors', cluster.keys.includes(currentTab) ? 'bg-white shadow-sm' : 'bg-slate-50 group-hover:bg-white']">
              <component :is="cluster.icon" class="w-3.5 h-3.5" />
            </div>
            <div class="text-left">
              <div class="text-[10px] font-black uppercase tracking-widest leading-none">{{ cluster.label }}</div>
              <div class="text-[8px] font-bold text-slate-400 uppercase tracking-tight mt-1">{{ cluster.subtitle }}</div>
            </div>
          </div>
          <component :is="cluster.open ? ChevronDown : ChevronRight" class="w-3.5 h-3.5 text-slate-300 transition-transform group-hover:scale-110" />
        </button>

        <Transition name="accordion">
          <div v-if="cluster.open" class="ml-8 mt-2 space-y-1 mb-2">
            <button
              v-for="item in cluster.items"
              :key="item.key"
              @click="emit('navigate', item.key)"
              :class="[
                'w-full flex items-center space-x-3 px-4 py-2.5 rounded-[14px] transition-all duration-300 group',
                currentTab === item.key
                  ? 'bg-slate-900 text-white shadow-lg shadow-slate-200'
                  : 'text-slate-400 hover:text-slate-900'
              ]"
            >
              <component :is="item.icon" class="w-3.5 h-3.5" />
              <span class="text-[10px] font-bold uppercase tracking-widest">{{ item.label }}</span>
            </button>
          </div>
        </Transition>
      </div>
    </nav>

    <!-- Bottom Controls -->
    <div class="mt-auto space-y-1 pt-6 border-t border-white/20">
      <button
        @click="emit('navigate', 'profile')"
        :class="[
          'w-full flex items-center space-x-4 px-5 py-4 rounded-[22px] transition-all duration-300 group',
          currentTab === 'profile'
            ? 'bg-slate-100 text-slate-900'
            : 'text-slate-400 hover:bg-white hover:text-slate-900 shadow-sm'
        ]"
      >
        <div class="w-8 h-8 rounded-xl bg-slate-50 flex items-center justify-center group-hover:bg-white transition-colors">
          <UserCircle class="w-4 h-4" />
        </div>
        <div class="text-left">
          <div class="text-[10px] font-black uppercase tracking-widest leading-none">My Profile</div>
          <div class="text-[8px] font-bold text-slate-400 uppercase tracking-tight mt-1">Account settings</div>
        </div>
      </button>

      <button
        @click="emit('navigate', 'help')"
        :class="[
          'w-full flex items-center space-x-4 px-5 py-4 rounded-[22px] transition-all duration-300 group',
          currentTab === 'help'
            ? 'bg-slate-100 text-slate-900'
            : 'text-slate-400 hover:bg-white hover:text-slate-900 shadow-sm'
        ]"
      >
        <div class="w-8 h-8 rounded-xl bg-slate-50 flex items-center justify-center group-hover:bg-white transition-colors">
          <HelpCircle class="w-4 h-4" />
        </div>
        <div class="text-left">
          <div class="text-[10px] font-black uppercase tracking-widest leading-none">Help & Guide</div>
          <div class="text-[8px] font-bold text-slate-400 uppercase tracking-tight mt-1">Documentation</div>
        </div>
      </button>

      <button
        @click="emit('logout')"
        class="w-full flex items-center space-x-4 px-5 py-4 rounded-[22px] transition-all duration-300 text-slate-400 hover:bg-rose-50 hover:text-rose-600 group"
      >
        <div class="w-8 h-8 rounded-xl bg-slate-50 group-hover:bg-white transition-colors flex items-center justify-center">
          <LogOut class="w-4 h-4" />
        </div>
        <div class="text-left">
          <div class="text-[10px] font-black uppercase tracking-widest leading-none">Sign Out</div>
          <div class="text-[8px] font-bold text-slate-400 uppercase tracking-tight mt-1">End session</div>
        </div>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.accordion-enter-active, .accordion-leave-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); overflow: hidden; }
.accordion-enter-from, .accordion-leave-to { opacity: 0; max-height: 0; transform: translateY(-5px); }
.accordion-enter-to, .accordion-leave-from { opacity: 1; max-height: 800px; transform: translateY(0); }

.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
