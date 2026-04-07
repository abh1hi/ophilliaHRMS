<script setup lang="ts">
import {
  LayoutDashboardIcon, UsersIcon, CalendarIcon, UserCircleIcon,
  ArrowLeftIcon, BuildingIcon, BriefcaseIcon, GitBranchIcon,
  StarIcon, UsersRoundIcon, TagIcon, ChevronDownIcon, ChevronRightIcon,
  LogOutIcon, ClockIcon, MapPinIcon, CalendarRangeIcon, ArrowLeftRightIcon, LayoutGridIcon,
  CalendarCheckIcon, LogInIcon, FileTextIcon, CheckSquareIcon, UploadIcon,
  UmbrellaIcon, CalendarDaysIcon, ShieldIcon, BookOpenIcon, SlashIcon,
  CoinsIcon, BarChart3Icon, ListIcon, KanbanIcon, StickyNoteIcon, SettingsIcon,
  WalletIcon,
} from 'lucide-vue-next'
import { ref } from 'vue'

const props = defineProps<{
  currentTab: string
  companyName?: string
  userRole?: string
}>()

const emit = defineEmits<{
  (e: 'navigate', tab: string): void
  (e: 'switch-entity'): void
  (e: 'logout'): void
}>()

const hrSetupOpen = ref(false)
const shiftOpen = ref(false)
const attendanceOpen = ref(false)

const mainNav = [
  { key: 'dashboard',  label: 'Dashboard',  icon: LayoutDashboardIcon },
  { key: 'employees',  label: 'Employees',  icon: UsersIcon           },
  { key: 'payroll',    label: 'Payroll',    icon: WalletIcon          },
]

const hrSetupNav = [
  { key: 'departments',       label: 'Departments',       icon: BuildingIcon    },
  { key: 'branches',          label: 'Branches',          icon: GitBranchIcon   },
  { key: 'designations',      label: 'Designations',      icon: BriefcaseIcon   },
  { key: 'employment-types',  label: 'Employment Types',  icon: TagIcon         },
  { key: 'employee-grades',   label: 'Employee Grades',   icon: StarIcon        },
  { key: 'employee-groups',   label: 'Employee Groups',   icon: UsersRoundIcon  },
]

const shiftNav = [
  { key: 'shift-types',       label: 'Shift Types',       icon: ClockIcon           },
  { key: 'shift-locations',   label: 'Shift Locations',   icon: MapPinIcon          },
  { key: 'shift-assignments', label: 'Shift Assignments', icon: CalendarRangeIcon   },
  { key: 'shift-requests',    label: 'Shift Requests',    icon: ArrowLeftRightIcon  },
  { key: 'shift-schedules',   label: 'Shift Schedules',   icon: LayoutGridIcon      },
  { key: 'roster',            label: 'Roster',            icon: CalendarIcon        },
]

const attendanceNav = [
  { key: 'attendance-records',  label: 'Records',          icon: CalendarCheckIcon },
  { key: 'attendance-checkins', label: 'Employee Checkins', icon: LogInIcon         },
  { key: 'attendance-requests', label: 'Att. Requests',    icon: FileTextIcon      },
  { key: 'attendance-bulk',     label: 'Bulk Mark',        icon: CheckSquareIcon   },
  { key: 'attendance-upload',   label: 'Upload CSV',       icon: UploadIcon        },
]

const leaveNav = [
  { key: 'leave-periods',             label: 'Leave Periods',    icon: CalendarDaysIcon },
  { key: 'holiday-lists',             label: 'Holiday Lists',    icon: UmbrellaIcon     },
  { key: 'leave-policies',            label: 'Leave Policies',   icon: ShieldIcon       },
  { key: 'leave-policy-assignments',  label: 'Policy Assign.',   icon: BookOpenIcon     },
  { key: 'leave-allocations',         label: 'Allocations',      icon: ListIcon         },
  { key: 'leave-block-lists',         label: 'Block Lists',      icon: SlashIcon        },
  { key: 'compensatory-leave',        label: 'Compensatory',     icon: CalendarCheckIcon},
  { key: 'leave-encashments',         label: 'Encashments',      icon: CoinsIcon        },
  { key: 'leave-ledger',              label: 'Ledger',           icon: BarChart3Icon    },
]

const workspaceNav = [
  { key: 'workspace-hub',      label: 'Hub',        icon: LayoutGridIcon  },
  { key: 'workspace-calendar', label: 'Calendar',   icon: CalendarIcon    },
  { key: 'workspace-board',    label: 'Task Board', icon: KanbanIcon      },
  { key: 'workspace-notes',    label: 'Notes',      icon: StickyNoteIcon  },
  { key: 'workspace-settings', label: 'Settings',   icon: SettingsIcon    },
]

const hrSetupKeys = hrSetupNav.map(n => n.key)
const shiftNavKeys = shiftNav.map(n => n.key)
const attendanceNavKeys = attendanceNav.map(n => n.key)
const leaveNavKeys = leaveNav.map(n => n.key)
const workspaceNavKeys = workspaceNav.map(n => n.key)

const leaveOpen = ref(false)
const workspaceOpen = ref(false)
</script>

<template>
  <aside class="w-72 bg-white/40 backdrop-blur-lg border-r border-slate-200/60 p-6 flex flex-col pt-10 relative z-20 shrink-0">
    <!-- Brand -->
    <div class="flex items-center space-x-3 mb-10 pl-2">
      <div class="w-10 h-10 bg-slate-900 rounded-[14px] flex items-center justify-center shadow-md shrink-0">
        <span class="text-white text-lg font-bold font-serif leading-none italic">O</span>
      </div>
      <div class="overflow-hidden">
        <div class="font-bold text-lg tracking-tight text-slate-900 truncate">{{ companyName || 'Ophillia HRMS' }}</div>
        <div class="text-xs text-slate-500 font-medium">HR Administration</div>
      </div>
    </div>

    <!-- Main Nav -->
    <nav class="flex-1 space-y-1 overflow-y-auto pr-2">
      <button
        v-for="item in mainNav"
        :key="item.key"
        @click="emit('navigate', item.key)"
        :class="[
          'w-full flex items-center space-x-3 px-4 py-3 rounded-[16px] transition-all duration-300 font-medium text-sm',
          currentTab === item.key
            ? 'bg-slate-900 text-white shadow-md'
            : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
        ]"
      >
        <component :is="item.icon" class="w-4 h-4" />
        <span>{{ item.label }}</span>
      </button>

      <!-- Attendance Group -->
      <div class="pt-2">
        <button
          @click="attendanceOpen = !attendanceOpen"
          :class="[
            'w-full flex items-center justify-between px-4 py-3 rounded-[16px] transition-all duration-300 font-medium text-sm',
            attendanceNavKeys.includes(currentTab)
              ? 'bg-slate-100 text-slate-900'
              : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
          ]"
        >
          <div class="flex items-center space-x-3">
            <CalendarIcon class="w-4 h-4" />
            <span>Attendance</span>
          </div>
          <component :is="attendanceOpen ? ChevronDownIcon : ChevronRightIcon" class="w-4 h-4" />
        </button>

        <Transition name="accordion">
          <div v-if="attendanceOpen" class="ml-4 mt-1 space-y-1 border-l border-slate-200/60 pl-3">
            <button
              v-for="item in attendanceNav"
              :key="item.key"
              @click="emit('navigate', item.key)"
              :class="[
                'w-full flex items-center space-x-3 px-3 py-2.5 rounded-[12px] transition-all duration-200 font-medium text-sm',
                currentTab === item.key
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-400 hover:bg-slate-100 hover:text-slate-800'
              ]"
            >
              <component :is="item.icon" class="w-4 h-4" />
              <span>{{ item.label }}</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- Leave Management Group -->
      <div class="pt-2">
        <button
          @click="leaveOpen = !leaveOpen"
          :class="[
            'w-full flex items-center justify-between px-4 py-3 rounded-[16px] transition-all duration-300 font-medium text-sm',
            leaveNavKeys.includes(currentTab)
              ? 'bg-slate-100 text-slate-900'
              : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
          ]"
        >
          <div class="flex items-center space-x-3">
            <UmbrellaIcon class="w-4 h-4" />
            <span>Leave Management</span>
          </div>
          <component :is="leaveOpen ? ChevronDownIcon : ChevronRightIcon" class="w-4 h-4" />
        </button>

        <Transition name="accordion">
          <div v-if="leaveOpen" class="ml-4 mt-1 space-y-1 border-l border-slate-200/60 pl-3">
            <button
              v-for="item in leaveNav"
              :key="item.key"
              @click="emit('navigate', item.key)"
              :class="[
                'w-full flex items-center space-x-3 px-3 py-2.5 rounded-[12px] transition-all duration-200 font-medium text-sm',
                currentTab === item.key
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-400 hover:bg-slate-100 hover:text-slate-800'
              ]"
            >
              <component :is="item.icon" class="w-4 h-4" />
              <span>{{ item.label }}</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- Workspace Group -->
      <div class="pt-2">
        <button
          @click="workspaceOpen = !workspaceOpen"
          :class="[
            'w-full flex items-center justify-between px-4 py-3 rounded-[16px] transition-all duration-300 font-medium text-sm',
            workspaceNavKeys.includes(currentTab)
              ? 'bg-slate-100 text-slate-900'
              : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
          ]"
        >
          <div class="flex items-center space-x-3">
            <LayoutGridIcon class="w-4 h-4" />
            <span>Workspace</span>
          </div>
          <component :is="workspaceOpen ? ChevronDownIcon : ChevronRightIcon" class="w-4 h-4" />
        </button>

        <Transition name="accordion">
          <div v-if="workspaceOpen" class="ml-4 mt-1 space-y-1 border-l border-slate-200/60 pl-3">
            <button
              v-for="item in workspaceNav"
              :key="item.key"
              @click="emit('navigate', item.key)"
              :class="[
                'w-full flex items-center space-x-3 px-3 py-2.5 rounded-[12px] transition-all duration-200 font-medium text-sm',
                currentTab === item.key
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-400 hover:bg-slate-100 hover:text-slate-800'
              ]"
            >
              <component :is="item.icon" class="w-4 h-4" />
              <span>{{ item.label }}</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- HR Setup Group -->
      <div class="pt-2">
        <button
          @click="hrSetupOpen = !hrSetupOpen"
          :class="[
            'w-full flex items-center justify-between px-4 py-3 rounded-[16px] transition-all duration-300 font-medium text-sm',
            hrSetupKeys.includes(currentTab)
              ? 'bg-slate-100 text-slate-900'
              : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
          ]"
        >
          <div class="flex items-center space-x-3">
            <BriefcaseIcon class="w-4 h-4" />
            <span>HR Setup</span>
          </div>
          <component :is="hrSetupOpen ? ChevronDownIcon : ChevronRightIcon" class="w-4 h-4" />
        </button>

        <Transition name="accordion">
          <div v-if="hrSetupOpen" class="ml-4 mt-1 space-y-1 border-l border-slate-200/60 pl-3">
            <button
              v-for="item in hrSetupNav"
              :key="item.key"
              @click="emit('navigate', item.key)"
              :class="[
                'w-full flex items-center space-x-3 px-3 py-2.5 rounded-[12px] transition-all duration-200 font-medium text-sm',
                currentTab === item.key
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-400 hover:bg-slate-100 hover:text-slate-800'
              ]"
            >
              <component :is="item.icon" class="w-4 h-4" />
              <span>{{ item.label }}</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- Shift Management Group -->
      <div class="pt-2">
        <button
          @click="shiftOpen = !shiftOpen"
          :class="[
            'w-full flex items-center justify-between px-4 py-3 rounded-[16px] transition-all duration-300 font-medium text-sm',
            shiftNavKeys.includes(currentTab)
              ? 'bg-slate-100 text-slate-900'
              : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
          ]"
        >
          <div class="flex items-center space-x-3">
            <ClockIcon class="w-4 h-4" />
            <span>Shift Management</span>
          </div>
          <component :is="shiftOpen ? ChevronDownIcon : ChevronRightIcon" class="w-4 h-4" />
        </button>

        <Transition name="accordion">
          <div v-if="shiftOpen" class="ml-4 mt-1 space-y-1 border-l border-slate-200/60 pl-3">
            <button
              v-for="item in shiftNav"
              :key="item.key"
              @click="emit('navigate', item.key)"
              :class="[
                'w-full flex items-center space-x-3 px-3 py-2.5 rounded-[12px] transition-all duration-200 font-medium text-sm',
                currentTab === item.key
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-400 hover:bg-slate-100 hover:text-slate-800'
              ]"
            >
              <component :is="item.icon" class="w-4 h-4" />
              <span>{{ item.label }}</span>
            </button>
          </div>
        </Transition>
      </div>
    </nav>

    <!-- Bottom Nav -->
    <div class="mt-auto space-y-1 border-t border-slate-200/50 pt-4">
      <button
        @click="emit('navigate', 'profile')"
        :class="[
          'w-full flex items-center space-x-3 px-4 py-3 rounded-[16px] transition-all duration-300 font-medium text-sm',
          currentTab === 'profile'
            ? 'bg-slate-900 text-white shadow-md'
            : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
        ]"
      >
        <UserCircleIcon class="w-4 h-4" />
        <span>Profile</span>
      </button>

      <!-- Switch Entity: only for super_admin -->
      <button
        v-if="userRole === 'super_admin'"
        @click="emit('switch-entity')"
        class="w-full flex items-center space-x-3 px-4 py-3 rounded-[16px] transition-all duration-300 font-medium text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-900"
      >
        <ArrowLeftIcon class="w-4 h-4" />
        <span>Switch Entity</span>
      </button>

      <button
        @click="emit('logout')"
        class="w-full flex items-center space-x-3 px-4 py-3 rounded-[16px] transition-all duration-300 font-medium text-sm text-slate-500 hover:bg-rose-50 hover:text-rose-600"
      >
        <LogOutIcon class="w-4 h-4" />
        <span>Logout</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.accordion-enter-active, .accordion-leave-active { transition: all 0.25s ease; overflow: hidden; }
.accordion-enter-from, .accordion-leave-to { opacity: 0; max-height: 0; }
.accordion-enter-to, .accordion-leave-from { opacity: 1; max-height: 500px; }
</style>
