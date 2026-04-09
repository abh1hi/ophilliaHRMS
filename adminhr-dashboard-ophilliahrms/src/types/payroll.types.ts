export interface PayrollRun {
  id: string
  period_start: string
  period_end: string
  run_type: string
  status: 'draft' | 'computed' | 'approved' | 'processing' | 'processed' | 'paid' | 'locked' | 'failed'
  created_at: string
  updated_at: string
  created_by?: string
  total_employees?: number
  total_amount?: number
  rejection_reason?: string | null
}

export interface Payslip {
  id: string
  payroll_run_id: string
  employee_id: string
  employee_name?: string
  gross_salary?: number
  net_salary?: number
  deductions?: number
  status: string
  created_at: string
  updated_at: string
}
