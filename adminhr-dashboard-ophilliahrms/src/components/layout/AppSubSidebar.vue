<script setup lang="ts">
import {
  Users,
  Database,
  CalendarCheck,
  LogIn,
  FileText,
  CheckSquare,
  Upload,
  CalendarDays,
  Umbrella,
  Shield,
  BookOpen,
  List,
  Slash,
  Coins,
  BarChart3,
  Clock,
  MapPin,
  CalendarRange,
  ArrowLeftRight,
  LayoutGrid,
  Calendar,
  Kanban,
  StickyNote,
  Settings,
  Building2,
  GitBranch,
  Briefcase,
  Tag,
  Star,
  Users2,
  PieChart,
} from 'lucide-vue-next'
import { computed } from 'vue'

const props = defineProps<{
  currentTab: string
}>()

const emit = defineEmits<{
  (e: 'navigate', tab: string): void
}>()

// Sub-navigation items per section
const subNavMap: Record<string, { key: string; label: string; icon: any }[]> = {
  employees: [
    { key: 'employees',              label: 'All Employees',    icon: Users    },
    { key: 'employees-import-queue', label: 'Bulk Import',      icon: Database },
  ],
  attendance: [
    { key: 'attendance-records',  label: 'Attendance Records',  icon: CalendarCheck },
    { key: 'attendance-checkins', label: 'Check-ins',           icon: LogIn         },
    { key: 'attendance-requests', label: 'Adjustments',         icon: FileText      },
    { key: 'attendance-bulk',     label: 'Bulk Attendance',     icon: CheckSquare   },
    { key: 'attendance-upload',   label: 'Upload Attendance',   icon: Upload        },
  ],
  leaves: [
    { key: 'leave-periods',             label: 'Leave Periods',      icon: CalendarDays  },
    { key: 'holiday-lists',             label: 'Holiday Lists',      icon: Umbrella      },
    { key: 'leave-types',               label: 'Leave Types',        icon: Tag           },
    { key: 'leave-policies',            label: 'Leave Policies',     icon: Shield        },
    { key: 'leave-policy-assignments',  label: 'Policy Assignments', icon: BookOpen      },
    { key: 'leave-allocations',         label: 'Allocations',        icon: List          },
    { key: 'leave-balance',             label: 'Leave Balances',     icon: PieChart      },
    { key: 'leave-block-lists',         label: 'Leave Block Lists',  icon: Slash         },
    { key: 'compensatory-leave',        label: 'Compensatory Leave', icon: CalendarCheck },
    { key: 'leave-encashments',         label: 'Leave Encashment',   icon: Coins         },
    { key: 'leave-ledger',              label: 'Leave Ledger',       icon: BarChart3     },
  ],
  shifts: [
    { key: 'shift-types',       label: 'Shift Types',      icon: Clock          },
    { key: 'shift-locations',   label: 'Locations',        icon: MapPin         },
    { key: 'shift-assignments', label: 'Assignments',      icon: CalendarRange  },
    { key: 'shift-requests',    label: 'Shift Requests',   icon: ArrowLeftRight },
    { key: 'shift-schedules',   label: 'Schedules',        icon: LayoutGrid     },
    { key: 'roster',            label: 'Roster',           icon: Calendar       },
  ],
  workspace: [
    { key: 'workspace-hub',      label: 'Workspace',          icon: LayoutGrid },
    { key: 'workspace-calendar', label: 'Calendar',           icon: Calendar   },
    { key: 'workspace-board',    label: 'Task Board',         icon: Kanban     },
    { key: 'workspace-notes',    label: 'Notes',              icon: StickyNote },
    { key: 'workspace-settings', label: 'Settings',           icon: Settings   },
  ],
  hrsetup: [
    { key: 'departments',       label: 'Departments',       icon: Building2 },
    { key: 'branches',          label: 'Branches',          icon: GitBranch },
    { key: 'designations',      label: 'Designations',      icon: Briefcase },
    { key: 'employment-types',  label: 'Employment Types',  icon: Tag       },
    { key: 'employee-grades',   label: 'Employee Grades',   icon: Star      },
    { key: 'employee-groups',   label: 'Employee Groups',   icon: Users2    },
  ],
}

// Map tabs to their section
const tabToSection: Record<string, string> = {
  employees: 'employees',
  'employees-import-queue': 'employees',
  'attendance-records': 'attendance',
  'attendance-checkins': 'attendance',
  'attendance-requests': 'attendance',
  'attendance-bulk': 'attendance',
  'attendance-upload': 'attendance',
  'leave-periods': 'leaves',
  'holiday-lists': 'leaves',
  'leave-types': 'leaves',
  'leave-balance': 'leaves',
  'leave-policies': 'leaves',
  'leave-policy-assignments': 'leaves',
  'leave-allocations': 'leaves',
  'leave-block-lists': 'leaves',
  'compensatory-leave': 'leaves',
  'leave-encashments': 'leaves',
  'leave-ledger': 'leaves',
  'shift-types': 'shifts',
  'shift-locations': 'shifts',
  'shift-assignments': 'shifts',
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
}

const currentSection = computed(() => tabToSection[props.currentTab])
const items = computed(() => (currentSection.value ? subNavMap[currentSection.value] ?? [] : []))

// Expose whether there are sub-nav items to show
defineExpose({ hasItems: computed(() => items.value.length > 0) })
</script>

<template>
  <aside
    v-if="items.length > 0"
    class="w-52 shrink-0 bg-white border-r border-slate-200 h-full overflow-y-auto no-scrollbar"
  >
    <nav class="p-3 space-y-0.5">
      <button
        v-for="item in items"
        :key="item.key"
        @click="emit('navigate', item.key)"
        :class="[
          'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors text-left',
          currentTab === item.key
            ? 'bg-indigo-50 text-indigo-700 font-semibold'
            : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 font-normal'
        ]"
      >
        <component
          :is="item.icon"
          :class="['w-4 h-4 shrink-0', currentTab === item.key ? 'text-indigo-600' : 'text-slate-400']"
        />
        {{ item.label }}
      </button>
    </nav>
  </aside>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
