import { apiFetch, apiFetchData, apiFetchAuth } from './http'
import type { PaginationMeta } from './http'

// ─── Types ────────────────────────────────────────────────────────────────────
export interface Employee {
  id: string
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
  department?: string
  designation?: string
  grade?: string
  branch?: string
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
}

export interface ListEmployeesParams {
  page?: number
  page_size?: number
  search?: string
  department_id?: string
  employment_status?: string
  sort?: string
  order?: 'asc' | 'desc'
}

export interface EmployeeListResult {
  data: Employee[]
  meta: PaginationMeta
}

// Raw shape returned by the backend list endpoint (non-enveloped)
interface RawEmployeeList {
  total: number
  skip: number
  limit: number
  employees: Employee[]
}

// ─── Employee API ─────────────────────────────────────────────────────────────
export async function listEmployees(params: ListEmployeesParams = {}): Promise<EmployeeListResult> {
  const query = new URLSearchParams(params as Record<string, string>).toString()
  // The list endpoint returns a raw EmployeeListResponse (no envelope wrapper)
  const raw = await apiFetchAuth<RawEmployeeList>(`/employees?${query}`)
  return {
    data: raw.employees ?? [],
    meta: {
      page: raw.limit > 0 ? Math.floor(raw.skip / raw.limit) + 1 : 1,
      page_size: raw.limit,
      total_items: raw.total,
      total_pages: raw.limit > 0 ? Math.ceil(raw.total / raw.limit) : 1,
    },
  }
}

export async function getEmployee(id: string): Promise<Employee> {
  return apiFetchData<Employee>(`/employees/${id}`)
}

export async function createEmployee(payload: Partial<Employee>): Promise<Employee> {
  return apiFetchData<Employee>('/employees', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateEmployee(id: string, payload: Partial<Employee>): Promise<Employee> {
  return apiFetchData<Employee>(`/employees/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteEmployee(id: string): Promise<void> {
  await apiFetch<null>(`/employees/${id}`, { method: 'DELETE' })
}
