<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  UserCircle,
  ShieldCheck,
  MapPin,
  Building2,
  Activity,
  Layers,
  LogOut,
  ArrowUpRight
} from 'lucide-vue-next'
import AppTopNav from '../components/layout/AppTopNav.vue'
import AppSubSidebar from '../components/layout/AppSubSidebar.vue'
import DashboardOverview from '../components/dashboard/DashboardOverview.vue'
import EmployeeListPanel from '../components/employees/EmployeeListPanel.vue'
import BulkImportQueuePanel from '../components/employees/queue-import/BulkImportQueuePanel.vue'
import DepartmentPanel from '../components/hrsetup/DepartmentPanel.vue'
import BranchPanel from '../components/hrsetup/BranchPanel.vue'
import DesignationPanel from '../components/hrsetup/DesignationPanel.vue'
import EmploymentTypePanel from '../components/hrsetup/EmploymentTypePanel.vue'
import EmployeeGradePanel from '../components/hrsetup/EmployeeGradePanel.vue'
import EmployeeGroupPanel from '../components/hrsetup/EmployeeGroupPanel.vue'
import ShiftTypePanel from '../components/shifts/ShiftTypePanel.vue'
import ShiftLocationPanel from '../components/shifts/ShiftLocationPanel.vue'
import ShiftAssignmentPanel from '../components/shifts/ShiftAssignmentPanel.vue'
import ShiftRequestPanel from '../components/shifts/ShiftRequestPanel.vue'
import ShiftSchedulePanel from '../components/shifts/ShiftSchedulePanel.vue'
import RosterPanel from '../components/shifts/RosterPanel.vue'
import AttendanceOverviewPanel from '../components/attendance/AttendanceOverviewPanel.vue'
import AttendanceRecordsPanel from '../components/attendance/AttendanceRecordsPanel.vue'
import AttendanceCheckinPanel from '../components/attendance/AttendanceCheckinPanel.vue'
import AttendanceRequestPanel from '../components/attendance/AttendanceRequestPanel.vue'
import BulkAttendancePanel from '../components/attendance/BulkAttendancePanel.vue'
import UploadAttendancePanel from '../components/attendance/UploadAttendancePanel.vue'
import HolidayCalendarPanel from '../components/attendance/HolidayCalendarPanel.vue'
import OvertimePolicyPanel from '../components/overtime/OvertimePolicyPanel.vue'
import OvertimeRecordsPanel from '../components/overtime/OvertimeRecordsPanel.vue'
import OvertimeRequestPanel from '../components/overtime/OvertimeRequestPanel.vue'
import OvertimeReportsPanel from '../components/overtime/OvertimeReportsPanel.vue'
import LeavePeriodPanel from '../components/leaves/LeavePeriodPanel.vue'
import HolidayListPanel from '../components/leaves/HolidayListPanel.vue'
import LeaveTypePanel from '../components/leaves/LeaveTypePanel.vue'
import LeaveBalanceSummaryPanel from '../components/leaves/LeaveBalanceSummaryPanel.vue'
import LeavePolicyPanel from '../components/leaves/LeavePolicyPanel.vue'
import LeavePolicyAssignmentPanel from '../components/leaves/LeavePolicyAssignmentPanel.vue'
import LeaveAllocationPanel from '../components/leaves/LeaveAllocationPanel.vue'
import LeaveBlockListPanel from '../components/leaves/LeaveBlockListPanel.vue'
import CompensatoryLeavePanel from '../components/leaves/CompensatoryLeavePanel.vue'
import LeaveEncashmentPanel from '../components/leaves/LeaveEncashmentPanel.vue'
import LeaveLedgerPanel from '../components/leaves/LeaveLedgerPanel.vue'
import WorkspaceHubView from '../components/workspace/WorkspaceHubView.vue'
import WorkspaceCalendarView from '../components/workspace/WorkspaceCalendarView.vue'
import WorkspaceBoardView from '../components/workspace/WorkspaceBoardView.vue'
import WorkspaceNotesPanel from '../components/workspace/WorkspaceNotesPanel.vue'
import WorkspaceSettingsView from '../components/workspace/WorkspaceSettingsView.vue'
import HelpView from './HelpView.vue'
import { getEmployeeProfile, logout, decodeToken } from '../services/auth.service'
import { getToken } from '../services/http'
import type { EmployeeProfile } from '../services/auth.service'
import OnboardingBanner from '../components/onboarding/OnboardingBanner.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const router = useRouter()
const route = useRoute()
const currentTab = ref((route.query.tab as string) || 'dashboard')
const employeeProfile = ref<EmployeeProfile | null>(null)
const companyName = ref(localStorage.getItem('company_name') || 'Ophillia HRMS')

const claims = decodeToken(getToken())
const userRole = claims?.role ?? ''

const userName = computed(() => {
  if (!employeeProfile.value) return claims?.email ?? '—'
  const { first_name, last_name } = employeeProfile.value
  return `${first_name ?? ''} ${last_name ?? ''}`.trim() || claims?.email || '—'
})

onMounted(async () => {
  employeeProfile.value = await getEmployeeProfile()
})

const headerTitles: Record<string, { title: string; subtitle: string }> = {
  dashboard:                  { title: 'Dashboard',             subtitle: `Welcome back to ${companyName.value}`                    },
  employees:                  { title: 'Employees',             subtitle: 'Manage your workforce'                                   },
  'employees-import-queue':   { title: 'Bulk Import',           subtitle: 'Import employees from CSV'                               },
  payroll:                    { title: 'Payroll',               subtitle: 'Manage compensation and payroll runs'                     },
  attendance:                 { title: 'Attendance',            subtitle: 'Track employee attendance, shift readiness, and alerts'   },
  departments:                { title: 'Departments',           subtitle: 'Manage organizational structure'                         },
  branches:                   { title: 'Branches',              subtitle: 'Manage office locations'                                 },
  designations:               { title: 'Designations',          subtitle: 'Define job titles and roles'                             },
  'employment-types':         { title: 'Employment Types',      subtitle: 'Define employment categories'                            },
  'employee-grades':          { title: 'Employee Grades',       subtitle: 'Define grade levels'                                     },
  'employee-groups':          { title: 'Employee Groups',       subtitle: 'Organize employees into groups'                          },
  'attendance-records':       { title: 'Attendance Records',    subtitle: 'View and manage daily attendance'                        },
  'attendance-checkins':      { title: 'Check-ins',             subtitle: 'Real-time attendance check-ins'                          },
  'attendance-requests':      { title: 'Attendance Adjustments', subtitle: 'Review and approve attendance requests'                 },
  'attendance-bulk':          { title: 'Bulk Attendance',       subtitle: 'Upload attendance data in bulk'                          },
  'attendance-upload':        { title: 'Upload Attendance',     subtitle: 'Import from external biometric systems'                  },
  'holiday-calendars-attendance': { title: 'Holiday Calendars', subtitle: 'Manage public and optional holidays'                     },
  'ot-policies':              { title: 'Overtime Policies',     subtitle: 'Define overtime thresholds and pay rates'                 },
  'ot-records':               { title: 'Overtime Records',      subtitle: 'Auto-calculated overtime from clock-in/out data'          },
  'ot-requests':              { title: 'Overtime Requests',     subtitle: 'Submit and review overtime requests'                      },
  'ot-reports':               { title: 'Overtime Reports',      subtitle: 'Monthly overtime analytics by employee'                   },
  'leave-periods':            { title: 'Leave Periods',         subtitle: 'Define annual leave cycles'                              },
  'holiday-lists':            { title: 'Holiday Lists',         subtitle: 'Manage company and public holidays'                      },
  'leave-types':              { title: 'Leave Types',           subtitle: 'Manage leave categories and entitlements'                },
  'leave-balance':            { title: 'Leave Balances',        subtitle: 'Current leave balances by employee and type'            },
  'leave-policies':           { title: 'Leave Policies',        subtitle: 'Define leave rules and entitlements'                     },
  'leave-policy-assignments': { title: 'Policy Assignments',    subtitle: 'Assign leave policies to employees'                      },
  'leave-allocations':        { title: 'Leave Allocations',     subtitle: 'Manage employee leave balances'                          },
  'leave-block-lists':        { title: 'Leave Block Lists',     subtitle: 'Restrict leave during specific periods'                  },
  'compensatory-leave':       { title: 'Compensatory Leave',    subtitle: 'Manage comp-off and overtime leave'                      },
  'leave-encashments':        { title: 'Leave Encashment',      subtitle: 'Process leave encashment requests'                       },
  'leave-ledger':             { title: 'Leave Ledger',          subtitle: 'Complete leave history and audit trail'                  },
  'shift-types':              { title: 'Shift Types',           subtitle: 'Define work shift patterns'                              },
  'shift-locations':          { title: 'Shift Locations',       subtitle: 'Manage work locations for shifts'                        },
  'shift-assignments':        { title: 'Shift Assignments',     subtitle: 'Assign shifts to employees'                              },
  'shift-requests':           { title: 'Shift Requests',        subtitle: 'Review employee shift change requests'                   },
  'shift-schedules':          { title: 'Shift Schedules',       subtitle: 'View and manage shift schedules'                         },
  roster:                     { title: 'Roster',                subtitle: 'Visual shift roster management'                          },
  'workspace-hub':            { title: 'Workspace',             subtitle: 'Team collaboration hub'                                  },
  'workspace-calendar':       { title: 'Calendar',              subtitle: 'Team calendar and events'                                },
  'workspace-board':          { title: 'Task Board',            subtitle: 'Kanban-style task management'                            },
  'workspace-notes':          { title: 'Notes',                 subtitle: 'Team notes and knowledge base'                           },
  'workspace-settings':       { title: 'Workspace Settings',    subtitle: 'Configure workspace preferences'                         },
  profile:                    { title: 'My Profile',            subtitle: 'Your account and personal details'                       },
  help:                       { title: 'Help & Guide',          subtitle: 'Documentation and how-to guides for HR staff'            },
}

const pageTitle = computed(() => headerTitles[currentTab.value]?.title ?? '')
const pageSubtitle = computed(() => headerTitles[currentTab.value]?.subtitle ?? '')

function navigate(tab: string) {
  if (tab === 'payroll') {
    router.push('/payroll')
  } else {
    currentTab.value = tab
    router.replace({ query: { ...route.query, tab: tab } })
  }
}

function handleLogout() {
  logout()
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-slate-50">
    <!-- Top navigation bar -->
    <AppTopNav
      :current-tab="currentTab"
      :company-name="companyName"
      :user-role="userRole"
      :user-name="userName"
      @navigate="navigate"
      @logout="handleLogout"
    />

    <!-- Body: sub-sidebar + main content -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Sub-sidebar (only for sections that have sub-pages) -->
      <AppSubSidebar
        :current-tab="currentTab"
        @navigate="navigate"
      />

      <!-- Main content area -->
      <main class="flex-1 overflow-y-auto no-scrollbar">
        <!-- Page header -->
        <div class="px-6 pt-6 pb-4 bg-white border-b border-slate-200">
          <OnboardingBanner v-if="['admin', 'hr'].includes(userRole)" />
          <h1 class="text-xl font-semibold text-slate-900">{{ pageTitle }}</h1>
          <p v-if="pageSubtitle" class="text-sm text-slate-500 mt-0.5">{{ pageSubtitle }}</p>
        </div>

        <!-- Module content -->
        <div class="p-6">
          <DashboardOverview        v-if="currentTab === 'dashboard'"                 />
          <EmployeeListPanel        v-else-if="currentTab === 'employees'"            />
          <BulkImportQueuePanel     v-else-if="currentTab === 'employees-import-queue'" />

          <!-- Attendance -->
          <AttendanceOverviewPanel  v-else-if="currentTab === 'attendance'"           />
          <AttendanceRecordsPanel   v-else-if="currentTab === 'attendance-records'"   />
          <AttendanceCheckinPanel   v-else-if="currentTab === 'attendance-checkins'"  />
          <AttendanceRequestPanel   v-else-if="currentTab === 'attendance-requests'"  />
          <BulkAttendancePanel      v-else-if="currentTab === 'attendance-bulk'"      />
          <UploadAttendancePanel    v-else-if="currentTab === 'attendance-upload'"    />
          <HolidayCalendarPanel     v-else-if="currentTab === 'holiday-calendars-attendance'" />

          <!-- Leaves -->
          <LeavePeriodPanel           v-else-if="currentTab === 'leave-periods'"            />
          <HolidayListPanel           v-else-if="currentTab === 'holiday-lists'"            />
          <LeaveTypePanel             v-else-if="currentTab === 'leave-types'"              />
          <LeaveBalanceSummaryPanel   v-else-if="currentTab === 'leave-balance'"            />
          <LeavePolicyPanel           v-else-if="currentTab === 'leave-policies'"           />
          <LeavePolicyAssignmentPanel v-else-if="currentTab === 'leave-policy-assignments'" />
          <LeaveAllocationPanel       v-else-if="currentTab === 'leave-allocations'"        />
          <LeaveBlockListPanel        v-else-if="currentTab === 'leave-block-lists'"        />
          <CompensatoryLeavePanel     v-else-if="currentTab === 'compensatory-leave'"       />
          <LeaveEncashmentPanel       v-else-if="currentTab === 'leave-encashments'"        />
          <LeaveLedgerPanel           v-else-if="currentTab === 'leave-ledger'"             />

          <!-- HR Setup -->
          <DepartmentPanel     v-else-if="currentTab === 'departments'"      />
          <BranchPanel         v-else-if="currentTab === 'branches'"         />
          <DesignationPanel    v-else-if="currentTab === 'designations'"     />
          <EmploymentTypePanel v-else-if="currentTab === 'employment-types'" />
          <EmployeeGradePanel  v-else-if="currentTab === 'employee-grades'"  />
          <EmployeeGroupPanel  v-else-if="currentTab === 'employee-groups'"  />

          <!-- Shifts -->
          <ShiftTypePanel       v-else-if="currentTab === 'shift-types'"       />
          <ShiftLocationPanel   v-else-if="currentTab === 'shift-locations'"   />
          <ShiftAssignmentPanel v-else-if="currentTab === 'shift-assignments'" />
          <ShiftRequestPanel    v-else-if="currentTab === 'shift-requests'"    />
          <ShiftSchedulePanel   v-else-if="currentTab === 'shift-schedules'"   />
          <RosterPanel          v-else-if="currentTab === 'roster'"            />

          <!-- Overtime -->
          <OvertimePolicyPanel  v-else-if="currentTab === 'ot-policies'"  />
          <OvertimeRecordsPanel v-else-if="currentTab === 'ot-records'"   />
          <OvertimeRequestPanel v-else-if="currentTab === 'ot-requests'"  />
          <OvertimeReportsPanel v-else-if="currentTab === 'ot-reports'"   />

          <!-- Workspace -->
          <WorkspaceHubView      v-else-if="currentTab === 'workspace-hub'"      />
          <WorkspaceCalendarView v-else-if="currentTab === 'workspace-calendar'" />
          <WorkspaceBoardView    v-else-if="currentTab === 'workspace-board'"    />
          <WorkspaceNotesPanel   v-else-if="currentTab === 'workspace-notes'"    />
          <WorkspaceSettingsView v-else-if="currentTab === 'workspace-settings'" />

          <!-- Help -->
          <HelpView v-else-if="currentTab === 'help'" @navigate="navigate" />

          <!-- My Profile -->
          <div v-else-if="currentTab === 'profile'" class="max-w-3xl space-y-6">
            <!-- Profile card -->
            <div class="bg-white border border-slate-200 rounded-xl shadow-sm p-8">
              <div class="flex flex-col sm:flex-row items-center sm:items-start gap-8">
                <!-- Avatar -->
                <div class="relative shrink-0">
                  <div class="w-20 h-20 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center">
                    <span class="text-3xl font-bold text-indigo-600 uppercase select-none">
                      {{ (employeeProfile?.first_name?.[0] ?? claims?.email?.[0] ?? '?').toUpperCase() }}
                    </span>
                  </div>
                  <div class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-white" />
                </div>

                <!-- Name & role -->
                <div class="flex-1 text-center sm:text-left space-y-2">
                  <div>
                    <h2 class="text-2xl font-semibold text-slate-900">{{ userName }}</h2>
                    <p class="text-sm text-slate-500 capitalize mt-0.5">{{ userRole.replace('_', ' ') }}</p>
                  </div>
                  <div class="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                    <Badge v-if="employeeProfile?.department" variant="secondary" class="flex items-center gap-1.5 text-xs">
                      <Layers class="w-3 h-3" /> {{ employeeProfile.department.name }}
                    </Badge>
                    <Badge v-if="employeeProfile?.branch" variant="secondary" class="flex items-center gap-1.5 text-xs">
                      <MapPin class="w-3 h-3" /> {{ employeeProfile.branch.name }}
                    </Badge>
                  </div>
                </div>

                <Button
                  @click="handleLogout"
                  variant="outline"
                  class="hidden sm:flex items-center gap-2 text-rose-600 border-rose-200 hover:bg-rose-50 hover:border-rose-300"
                >
                  <LogOut class="w-4 h-4" /> Sign Out
                </Button>
              </div>

              <!-- Account details -->
              <div class="mt-8 pt-6 border-t border-slate-100">
                <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Account Details</h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  <div v-for="attr in [
                    { label: 'Email Address', value: claims?.email ?? '—', icon: UserCircle },
                    { label: 'Designation', value: employeeProfile?.designation?.name ?? '—', icon: Building2 },
                    { label: 'Role', value: userRole.replace('_', ' '), icon: ShieldCheck },
                    { label: 'Employment Status', value: employeeProfile?.employment_status ?? 'Active', icon: Activity }
                  ]" :key="attr.label" class="space-y-1">
                    <div class="flex items-center gap-1.5">
                      <component :is="attr.icon" class="w-3.5 h-3.5 text-slate-400" />
                      <p class="text-xs text-slate-400 font-medium">{{ attr.label }}</p>
                    </div>
                    <div class="bg-slate-50 border border-slate-100 rounded-lg px-3 py-2">
                      <p class="text-sm font-medium text-slate-800 capitalize truncate">{{ attr.value }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="sm:hidden mt-6">
                <Button
                  @click="handleLogout"
                  variant="outline"
                  class="w-full flex items-center justify-center gap-2 text-rose-600 border-rose-200 hover:bg-rose-50"
                >
                  <LogOut class="w-4 h-4" /> Sign Out
                </Button>
              </div>
            </div>

            <!-- Status cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pb-6">
              <div class="bg-white border border-slate-200 rounded-xl p-6 flex items-center justify-between">
                <div>
                  <p class="text-xs text-slate-400 font-medium mb-1">Account Status</p>
                  <p class="text-sm font-semibold text-slate-800">Active</p>
                </div>
                <div class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                  <ShieldCheck class="w-5 h-5 text-indigo-500" />
                </div>
              </div>
              <div class="bg-white border border-slate-200 rounded-xl p-6 flex items-center justify-between">
                <div>
                  <p class="text-xs text-slate-400 font-medium mb-1">Session</p>
                  <p class="text-sm font-semibold text-slate-800">Active</p>
                </div>
                <div class="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center">
                  <ArrowUpRight class="w-5 h-5 text-emerald-500" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
