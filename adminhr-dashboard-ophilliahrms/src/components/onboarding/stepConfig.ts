import type { Component } from 'vue'
import DepartmentsStep from './steps/DepartmentsStep.vue'
import LeaveTypesStep from './steps/LeaveTypesStep.vue'
import AttendancePolicyStep from './steps/AttendancePolicyStep.vue'
import SalaryStructureStep from './steps/SalaryStructureStep.vue'
import FirstEmployeeStep from './steps/FirstEmployeeStep.vue'

export interface StepConfig {
  component: Component
  permissions: string[]
  retryable: boolean
  estimatedMinutes: number
  description: string
}

export const STEP_CONFIG: Record<string, StepConfig> = {
  departments: {
    component: DepartmentsStep,
    permissions: ['admin', 'hr'],
    retryable: true,
    estimatedMinutes: 1,
    description: 'Create your first department to organize employees',
  },
  leave_types: {
    component: LeaveTypesStep,
    permissions: ['admin', 'hr'],
    retryable: true,
    estimatedMinutes: 2,
    description: 'Set up leave policies and annual allocations',
  },
  attendance_policy: {
    component: AttendancePolicyStep,
    permissions: ['admin'],
    retryable: true,
    estimatedMinutes: 1,
    description: 'Define work hours and attendance tracking method',
  },
  salary_structure: {
    component: SalaryStructureStep,
    permissions: ['admin'],
    retryable: true,
    estimatedMinutes: 2,
    description: 'Configure salary components and statutory deductions',
  },
  first_employee: {
    component: FirstEmployeeStep,
    permissions: ['admin', 'hr'],
    retryable: true,
    estimatedMinutes: 1,
    description: 'Add the first member of your team',
  },
}

export const TOTAL_ESTIMATED_MINUTES = Object.values(STEP_CONFIG).reduce(
  (sum, c) => sum + c.estimatedMinutes,
  0
)
