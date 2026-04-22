<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Search, LayoutDashboard, Users, Calendar, Clock, Umbrella, Settings2, Monitor, Activity, TrendingUp, HelpCircle, Wallet, ArrowRight } from 'lucide-vue-next'
import { useCommandPaletteStore } from '../../stores/commandPalette.store'

const emit = defineEmits<{ (e: 'navigate', tab: string): void }>()
const palette = useCommandPaletteStore()

const query = ref('')
const inputRef = ref<HTMLInputElement | null>(null)
const activeIndex = ref(0)

interface NavItem { key: string; label: string; group: string; icon: any }

const allNav: NavItem[] = [
  { key: 'dashboard',                  label: 'Dashboard',               group: 'Main',       icon: LayoutDashboard },
  { key: 'payroll',                    label: 'Payroll',                  group: 'Main',       icon: Wallet          },
  { key: 'employees',                  label: 'Employee Directory',       group: 'Employees',  icon: Users           },
  { key: 'employees-import-queue',     label: 'Bulk Import',              group: 'Employees',  icon: Users           },
  { key: 'attendance-records',         label: 'Attendance Records',       group: 'Attendance', icon: Activity        },
  { key: 'attendance-checkins',        label: 'Check-ins',                group: 'Attendance', icon: Activity        },
  { key: 'attendance-requests',        label: 'Attendance Adjustments',   group: 'Attendance', icon: Activity        },
  { key: 'attendance-bulk',            label: 'Bulk Attendance',          group: 'Attendance', icon: Activity        },
  { key: 'attendance-upload',          label: 'Import from Biometric',    group: 'Attendance', icon: Activity        },
  { key: 'ot-policies',                label: 'Overtime Policies',        group: 'Overtime',   icon: TrendingUp      },
  { key: 'ot-records',                 label: 'Overtime Records',         group: 'Overtime',   icon: TrendingUp      },
  { key: 'ot-requests',                label: 'Overtime Requests',        group: 'Overtime',   icon: TrendingUp      },
  { key: 'ot-reports',                 label: 'Overtime Reports',         group: 'Overtime',   icon: TrendingUp      },
  { key: 'leave-periods',              label: 'Leave Periods',            group: 'Leave',      icon: Umbrella        },
  { key: 'holiday-lists',              label: 'Holiday Lists',            group: 'Leave',      icon: Umbrella        },
  { key: 'leave-types',                label: 'Leave Types',              group: 'Leave',      icon: Umbrella        },
  { key: 'leave-balance',              label: 'Leave Balances',           group: 'Leave',      icon: Umbrella        },
  { key: 'leave-policies',             label: 'Leave Policies',           group: 'Leave',      icon: Umbrella        },
  { key: 'leave-policy-assignments',   label: 'Policy Assignments',       group: 'Leave',      icon: Umbrella        },
  { key: 'leave-allocations',          label: 'Leave Allocations',        group: 'Leave',      icon: Umbrella        },
  { key: 'leave-block-lists',          label: 'Leave Block Lists',        group: 'Leave',      icon: Umbrella        },
  { key: 'compensatory-leave',         label: 'Compensatory Leave',       group: 'Leave',      icon: Umbrella        },
  { key: 'leave-encashments',          label: 'Leave Encashment',         group: 'Leave',      icon: Umbrella        },
  { key: 'leave-ledger',               label: 'Leave Ledger',             group: 'Leave',      icon: Umbrella        },
  { key: 'departments',                label: 'Departments',              group: 'HR Setup',   icon: Settings2       },
  { key: 'branches',                   label: 'Branches',                 group: 'HR Setup',   icon: Settings2       },
  { key: 'designations',               label: 'Designations',             group: 'HR Setup',   icon: Settings2       },
  { key: 'employment-types',           label: 'Employment Types',         group: 'HR Setup',   icon: Settings2       },
  { key: 'employee-grades',            label: 'Employee Grades',          group: 'HR Setup',   icon: Settings2       },
  { key: 'employee-groups',            label: 'Employee Groups',          group: 'HR Setup',   icon: Settings2       },
  { key: 'shift-types',                label: 'Shift Types',              group: 'Shifts',     icon: Clock           },
  { key: 'shift-locations',            label: 'Shift Locations',          group: 'Shifts',     icon: Clock           },
  { key: 'shift-requests',             label: 'Shift Requests',           group: 'Shifts',     icon: Clock           },
  { key: 'shift-schedules',            label: 'Shift Schedules',          group: 'Shifts',     icon: Clock           },
  { key: 'roster',                     label: 'Roster',                   group: 'Shifts',     icon: Calendar        },
  { key: 'workspace-hub',              label: 'Team Hub',                 group: 'Workspace',  icon: Monitor         },
  { key: 'workspace-calendar',         label: 'Workspace Calendar',       group: 'Workspace',  icon: Monitor         },
  { key: 'workspace-board',            label: 'Task Board',               group: 'Workspace',  icon: Monitor         },
  { key: 'workspace-notes',            label: 'Notes',                    group: 'Workspace',  icon: Monitor         },
  { key: 'help',                       label: 'Help & Guide',             group: 'Other',      icon: HelpCircle      },
  { key: 'profile',                    label: 'My Profile',               group: 'Other',      icon: Users           },
]

const filtered = computed(() => {
  const q = query.value.toLowerCase().trim()
  if (!q) return allNav.slice(0, 8)
  return allNav.filter(n =>
    n.label.toLowerCase().includes(q) || n.group.toLowerCase().includes(q)
  ).slice(0, 12)
})

watch(() => palette.isOpen, async (open) => {
  if (open) {
    query.value = ''
    activeIndex.value = 0
    await nextTick()
    inputRef.value?.focus()
  }
})

watch(filtered, () => { activeIndex.value = 0 })

function select(item: NavItem) {
  emit('navigate', item.key)
  palette.close()
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIndex.value = Math.min(activeIndex.value + 1, filtered.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIndex.value = Math.max(activeIndex.value - 1, 0)
  } else if (e.key === 'Enter') {
    const item = filtered.value[activeIndex.value]
    if (item) select(item)
  } else if (e.key === 'Escape') {
    palette.close()
  }
}

const groupColors: Record<string, string> = {
  Main: 'bg-slate-100 text-slate-600',
  Employees: 'bg-blue-50 text-blue-600',
  Attendance: 'bg-violet-50 text-violet-600',
  Overtime: 'bg-orange-50 text-orange-600',
  Leave: 'bg-emerald-50 text-emerald-600',
  'HR Setup': 'bg-slate-100 text-slate-600',
  Shifts: 'bg-cyan-50 text-cyan-600',
  Workspace: 'bg-indigo-50 text-indigo-600',
  Other: 'bg-slate-100 text-slate-500',
}
</script>

<template>
  <Teleport to="body">
    <Transition name="palette">
      <div
        v-if="palette.isOpen"
        class="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
        @click.self="palette.close()"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" @click="palette.close()" />

        <!-- Panel -->
        <div class="relative w-full max-w-xl bg-white rounded-[28px] shadow-2xl shadow-slate-900/20 border border-slate-200 overflow-hidden">
          <!-- Search input -->
          <div class="flex items-center gap-3 px-5 py-4 border-b border-slate-100">
            <Search class="w-4 h-4 text-slate-400 shrink-0" />
            <input
              ref="inputRef"
              v-model="query"
              @keydown="onKey"
              placeholder="Search or jump to any section…"
              class="flex-1 text-sm text-slate-800 placeholder:text-slate-400 bg-transparent outline-none"
            />
            <kbd class="text-[10px] font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-lg">ESC</kbd>
          </div>

          <!-- Results -->
          <ul class="max-h-[360px] overflow-y-auto py-2" role="listbox">
            <li v-if="!filtered.length" class="px-5 py-8 text-center text-sm text-slate-400">
              No results for "{{ query }}"
            </li>
            <li
              v-for="(item, i) in filtered"
              :key="item.key"
              @click="select(item)"
              @mousemove="activeIndex = i"
              :class="[
                'flex items-center gap-3 px-5 py-3 cursor-pointer transition-colors',
                activeIndex === i ? 'bg-slate-50' : 'hover:bg-slate-50'
              ]"
              role="option"
            >
              <div :class="['w-7 h-7 rounded-lg flex items-center justify-center shrink-0', groupColors[item.group] ?? 'bg-slate-100 text-slate-500']">
                <component :is="item.icon" class="w-3.5 h-3.5" />
              </div>
              <div class="flex-1 min-w-0">
                <span class="text-sm font-medium text-slate-800">{{ item.label }}</span>
              </div>
              <span class="text-[9px] font-bold uppercase tracking-widest text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full shrink-0">{{ item.group }}</span>
              <ArrowRight v-if="activeIndex === i" class="w-3 h-3 text-slate-400 shrink-0" />
            </li>
          </ul>

          <!-- Footer hint -->
          <div class="px-5 py-2.5 border-t border-slate-100 flex items-center gap-4 text-[10px] text-slate-400 font-medium">
            <span><kbd class="bg-slate-100 px-1.5 rounded font-bold">↑↓</kbd> navigate</span>
            <span><kbd class="bg-slate-100 px-1.5 rounded font-bold">↵</kbd> select</span>
            <span><kbd class="bg-slate-100 px-1.5 rounded font-bold">ESC</kbd> close</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.palette-enter-active, .palette-leave-active { transition: all 0.15s ease; }
.palette-enter-from, .palette-leave-to { opacity: 0; }
.palette-enter-from .relative, .palette-leave-to .relative { transform: scale(0.96) translateY(-8px); }
</style>
