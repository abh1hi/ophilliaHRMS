import type { PaginationMeta } from './http'
import type { Department } from './department.service'
import type { Designation } from './designation.service'
import type { Branch } from './branch.service'
import type { EmployeeGrade } from './employee-grade.service'

// ─── Core Types ──────────────────────────────────────────────────────────────
export interface Employee {
  id: string
  user_id?: string
  employee_code?: string
  // Personal
  first_name: string
  last_name: string
  gender?: string
  date_of_birth?: string
  email: string
  phone?: string
  phone_2?: string
  personal_email?: string
  // Joining
  date_joined?: string
  offer_date?: string
  confirmation_date?: string
  contract_end_date?: string
  notice_days?: number
  date_of_retirement?: string
  employment_type?: string
  employment_status: 'active' | 'inactive' | 'terminated'
  // Dept & Grade
  department_id?: string
  department?: Department
  designation_id?: string
  designation_rel?: Designation
  designation?: string  // Keep for legacy/string storage
  grade_id?: string
  grade?: EmployeeGrade
  branch_id?: string
  branch?: Branch
  reports_to?: string
  // Salary & Banking
  salary_mode?: 'bank' | 'cheque' | 'cash'
  bank_name?: string
  bank_branch?: string
  bank_account_number?: string
  ifsc_code?: string
  joining_salary?: number
  // Contact
  door_no?: string
  street?: string
  village_town?: string
  pin_code?: string
  // IDs
  aadhaar_number?: string
  pan_number?: string
  uan_number?: string
  esi_number?: string
  driving_license_number?: string
  // Emergency
  emergency_contact_name?: string
  emergency_contact_number?: string
  emergency_contact_relation?: string
  // Education
  highest_qualification?: string
  institute_name?: string
  year_of_passing?: string
  percentage?: string
  // Experience
  last_firm_name?: string
  last_designation?: string
  years_of_experience?: string
  last_drawn_salary?: number
  reason_to_quit?: string
  // Exit
  resignation_date?: string
  relieving_date?: string
  // Misc
  project?: string
  role?: string
  staff_photo_url?: string
  referred_by?: string
  health_issues?: string
  allergies?: string
  created_at?: string
  updated_at?: string
  // Account provisioning (read-only)
  account_status?: 'not_registered' | 'invited' | 'active' | 'suspended'
  invite_expires_at?: string | null
}

export interface ListEmployeesParams {
  page?: number
  page_size?: number
  search?: string
  department_id?: string
  employment_status?: string
  account_status?: string
  sort?: string
  order?: 'asc' | 'desc'
}

export interface EmployeeListResult {
  data: Employee[]
  meta: PaginationMeta
}

export interface RawEmployeeList {
  total: number
  skip: number
  limit: number
  employees: Employee[]
}

// ─── Account Provisioning Types ──────────────────────────────────────────────
export interface SendInviteResponse {
  employee_id: string
  email: string
  invite_url: string
  expires_at: string
  account_status: string
}

// ─── Bulk Import Types (Legacy) ──────────────────────────────────────────────
export interface EmployeeImportResult {
  total: number
  succeeded: number
  skipped: number
  failed: number
  errors: Array<{ row: number; field?: string; error: string; skipped?: boolean }>
}

export interface ImportProgress {
  done: number
  total: number
}

// ─── New Import Pipeline Types ───────────────────────────────────────────────
export interface AutoCorrection {
  row: number
  field: string
  original: string
  fixed: string
}

export interface RowIssue {
  row: number
  field: string
  error: string
  suggested_fix: string
  original_value: string
  is_warning: boolean
  is_cross_row: boolean
}

export interface PreviewRow {
  index: number
  data: Record<string, string>
  status: string
  issues: RowIssue[]
}

export interface PreviewSummary {
  valid: number
  warnings: number
  errors: number
  auto_corrections: number
  cross_row_duplicates: number
}

export interface ImportPreviewResult {
  rows: PreviewRow[]
  summary: PreviewSummary
  auto_corrections: AutoCorrection[]
}

export interface ImportJobUploadResult {
  job_id: string
  total_rows: number
  auto_corrections: AutoCorrection[]
  cross_row_warnings: RowIssue[]
  idempotent: boolean
}

export interface ImportJob {
  id: string
  company_id: string
  uploaded_by: string
  file_name: string
  file_size_bytes?: number
  schema_version: string
  status: string
  duplicate_strategy: string
  total_rows: number
  succeeded_rows: number
  failed_rows: number
  skipped_rows: number
  error_log?: Array<Record<string, string>>
  auto_corrections?: AutoCorrection[]
  created_at: string
  completed_at?: string
}
