<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppSidebar from '../components/layout/AppSidebar.vue'
import AppHeader from '../components/layout/AppHeader.vue'
import DashboardOverview from '../components/dashboard/DashboardOverview.vue'
import EmployeeListPanel from '../components/employees/EmployeeListPanel.vue'
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
import AttendanceRecordsPanel from '../components/attendance/AttendanceRecordsPanel.vue'
import AttendanceCheckinPanel from '../components/attendance/AttendanceCheckinPanel.vue'
import AttendanceRequestPanel from '../components/attendance/AttendanceRequestPanel.vue'
import BulkAttendancePanel from '../components/attendance/BulkAttendancePanel.vue'
import UploadAttendancePanel from '../components/attendance/UploadAttendancePanel.vue'
import LeavePeriodPanel from '../components/leaves/LeavePeriodPanel.vue'
import HolidayListPanel from '../components/leaves/HolidayListPanel.vue'
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
import { getEmployeeProfile, logout, decodeToken } from '../services/auth.service'
import { getToken, clearTokens } from '../services/http'
import type { EmployeeProfile } from '../services/auth.service'

const router = useRouter()
const route = useRoute()
const currentTab = ref((route.query.tab as string) || 'dashboard')
const employeeProfile = ref<EmployeeProfile | null>(null)
const companyName = ref(localStorage.getItem('company_name') || 'Ophillia HRMS')

// Decode role directly from the stored JWT — no extra round trip needed
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
  dashboard:          { title: 'Overview',         subtitle: `What's happening today at ${companyName.value}` },
  employees:          { title: 'Employees',         subtitle: 'Manage your entire workforce'                  },
  attendance:         { title: 'Attendance',        subtitle: 'Track and review attendance records'           },
  departments:        { title: 'HR Setup',          subtitle: 'Departments'                                   },
  branches:           { title: 'HR Setup',          subtitle: 'Branches'                                      },
  designations:       { title: 'HR Setup',          subtitle: 'Designations'                                  },
  'employment-types': { title: 'HR Setup',          subtitle: 'Employment Types'                              },
  'employee-grades':  { title: 'HR Setup',          subtitle: 'Employee Grades'                               },
  'employee-groups':  { title: 'HR Setup',          subtitle: 'Employee Groups'                               },
  'attendance-records':  { title: 'Attendance',       subtitle: 'Records'                                       },
  'attendance-checkins': { title: 'Attendance',       subtitle: 'Employee Checkins'                             },
  'attendance-requests': { title: 'Attendance',       subtitle: 'Regularization Requests'                      },
  'attendance-bulk':     { title: 'Attendance',       subtitle: 'Bulk Mark'                                    },
  'attendance-upload':   { title: 'Attendance',       subtitle: 'Upload CSV'                                   },
  'leave-periods':            { title: 'Leave Management', subtitle: 'Leave Periods'          },
  'holiday-lists':            { title: 'Leave Management', subtitle: 'Holiday Lists'          },
  'leave-policies':           { title: 'Leave Management', subtitle: 'Leave Policies'         },
  'leave-policy-assignments': { title: 'Leave Management', subtitle: 'Policy Assignments'     },
  'leave-allocations':        { title: 'Leave Management', subtitle: 'Leave Allocations'      },
  'leave-block-lists':        { title: 'Leave Management', subtitle: 'Block Lists'            },
  'compensatory-leave':       { title: 'Leave Management', subtitle: 'Compensatory Leave'     },
  'leave-encashments':        { title: 'Leave Management', subtitle: 'Leave Encashments'      },
  'leave-ledger':             { title: 'Leave Management', subtitle: 'Leave Ledger'           },
  'shift-types':       { title: 'Shift Management', subtitle: 'Shift Types'                                   },
  'shift-locations':   { title: 'Shift Management', subtitle: 'Shift Locations'                               },
  'shift-assignments': { title: 'Shift Management', subtitle: 'Shift Assignments'                             },
  'shift-requests':    { title: 'Shift Management', subtitle: 'Shift Requests'                                },
  'shift-schedules':   { title: 'Shift Management', subtitle: 'Shift Schedules'                               },
  roster:              { title: 'Shift Management', subtitle: 'Roster View'                                   },
  'workspace-hub':      { title: 'Workspace',   subtitle: 'Your team hub'           },
  'workspace-calendar': { title: 'Workspace',   subtitle: 'Calendar'                },
  'workspace-board':    { title: 'Workspace',   subtitle: 'Task Board'              },
  'workspace-notes':    { title: 'Workspace',   subtitle: 'Google Keep Notes'       },
  'workspace-settings': { title: 'Workspace',   subtitle: 'Settings'               },
  profile:            { title: 'My Profile',        subtitle: 'Your account information'                      },
}

function navigate(tab: string) {
  currentTab.value = tab
}

function switchEntity() {
  router.push('/select-company')
}

function handleLogout() {
  logout()
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen flex relative">

    <AppSidebar
      :current-tab="currentTab"
      :company-name="companyName"
      :user-role="userRole"
      @navigate="navigate"
      @switch-entity="switchEntity"
      @logout="handleLogout"
    />

    <!-- Main Content -->
    <main class="flex-1 p-8 sm:p-12 h-screen overflow-y-auto relative z-10">
      <AppHeader
        :title="headerTitles[currentTab]?.title"
        :subtitle="headerTitles[currentTab]?.subtitle"
        :user-name="userName"
        :user-role="userRole"
        @profile-click="navigate('profile')"
        @logout="handleLogout"
      />

      <!-- Tab content -->
      <DashboardOverview   v-if="currentTab === 'dashboard'"           />
      <EmployeeListPanel   v-else-if="currentTab === 'employees'"      />

      <!-- Attendance panels -->
      <AttendanceRecordsPanel  v-else-if="currentTab === 'attendance-records'"  />
      <AttendanceCheckinPanel  v-else-if="currentTab === 'attendance-checkins'" />
      <AttendanceRequestPanel  v-else-if="currentTab === 'attendance-requests'" />
      <BulkAttendancePanel     v-else-if="currentTab === 'attendance-bulk'"     />
      <UploadAttendancePanel   v-else-if="currentTab === 'attendance-upload'"   />

      <!-- Leave Management panels -->
      <LeavePeriodPanel           v-else-if="currentTab === 'leave-periods'"            />
      <HolidayListPanel           v-else-if="currentTab === 'holiday-lists'"            />
      <LeavePolicyPanel           v-else-if="currentTab === 'leave-policies'"           />
      <LeavePolicyAssignmentPanel v-else-if="currentTab === 'leave-policy-assignments'" />
      <LeaveAllocationPanel       v-else-if="currentTab === 'leave-allocations'"        />
      <LeaveBlockListPanel        v-else-if="currentTab === 'leave-block-lists'"        />
      <CompensatoryLeavePanel     v-else-if="currentTab === 'compensatory-leave'"       />
      <LeaveEncashmentPanel       v-else-if="currentTab === 'leave-encashments'"        />
      <LeaveLedgerPanel           v-else-if="currentTab === 'leave-ledger'"             />

      <!-- HR Setup panels -->
      <DepartmentPanel     v-else-if="currentTab === 'departments'"      />
      <BranchPanel         v-else-if="currentTab === 'branches'"         />
      <DesignationPanel    v-else-if="currentTab === 'designations'"     />
      <EmploymentTypePanel v-else-if="currentTab === 'employment-types'" />
      <EmployeeGradePanel  v-else-if="currentTab === 'employee-grades'"  />
      <EmployeeGroupPanel  v-else-if="currentTab === 'employee-groups'"  />

      <!-- Shift Management panels -->
      <ShiftTypePanel       v-else-if="currentTab === 'shift-types'"       />
      <ShiftLocationPanel   v-else-if="currentTab === 'shift-locations'"   />
      <ShiftAssignmentPanel v-else-if="currentTab === 'shift-assignments'" />
      <ShiftRequestPanel    v-else-if="currentTab === 'shift-requests'"    />
      <ShiftSchedulePanel   v-else-if="currentTab === 'shift-schedules'"   />
      <RosterPanel          v-else-if="currentTab === 'roster'"            />

      <!-- Workspace panels -->
      <WorkspaceHubView      v-else-if="currentTab === 'workspace-hub'"      />
      <WorkspaceCalendarView v-else-if="currentTab === 'workspace-calendar'" />
      <WorkspaceBoardView    v-else-if="currentTab === 'workspace-board'"    />
      <WorkspaceNotesPanel   v-else-if="currentTab === 'workspace-notes'"    />
      <WorkspaceSettingsView v-else-if="currentTab === 'workspace-settings'" />

      <!-- Profile inline panel -->
      <div v-else-if="currentTab === 'profile'" class="max-w-2xl">
        <div class="bg-white/70 backdrop-blur-md border border-slate-200/60 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)] rounded-[24px] p-8 sm:p-10">
          <div class="flex items-start gap-6">
            <div class="w-20 h-20 rounded-[20px] bg-slate-100 flex items-center justify-center border border-slate-200/60 shrink-0">
              <span class="text-3xl font-bold text-slate-400">
                {{ (employeeProfile?.first_name?.[0] ?? claims?.email?.[0] ?? '?').toUpperCase() }}
              </span>
            </div>
            <div class="space-y-1">
              <h2 class="text-xl font-bold text-slate-900">{{ userName }}</h2>
              <p class="text-sm font-medium text-slate-500 capitalize">{{ userRole.replace('_', ' ') }}</p>
              <p v-if="employeeProfile?.department" class="text-sm text-slate-400">{{ employeeProfile.department.name }}</p>
            </div>
          </div>

          <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-6 pt-6 border-t border-slate-200/50 text-sm">
            <div>
              <p class="font-semibold text-slate-500 mb-1">Email</p>
              <p class="text-slate-900">{{ claims?.email ?? '—' }}</p>
            </div>
            <div>
              <p class="font-semibold text-slate-500 mb-1">Role</p>
              <p class="text-slate-900 capitalize">{{ userRole.replace('_', ' ') }}</p>
            </div>
            <div v-if="employeeProfile?.designation">
              <p class="font-semibold text-slate-500 mb-1">Designation</p>
              <p class="text-slate-900">{{ employeeProfile.designation.name }}</p>
            </div>
            <div v-if="employeeProfile?.branch">
              <p class="font-semibold text-slate-500 mb-1">Branch</p>
              <p class="text-slate-900">{{ employeeProfile.branch.name }}</p>
            </div>
            <div v-if="employeeProfile?.employment_status">
              <p class="font-semibold text-slate-500 mb-1">Status</p>
              <p class="text-slate-900 capitalize">{{ employeeProfile.employment_status }}</p>
            </div>
          </div>

          <div class="mt-8 pt-6 border-t border-slate-200/50">
            <button
              @click="handleLogout"
              class="flex items-center gap-2 px-5 py-2.5 rounded-full border border-rose-200 text-rose-600 hover:bg-rose-50 font-medium text-sm transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </main>

  </div>
</template>
