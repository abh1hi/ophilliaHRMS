// Real API services for OphilliaHRMS employee app
// Auth: POST /api/v1/auth/login → { access_token, refresh_token, token_type }
// Profile: GET /api/v1/employees/me → full employee record

const API_BASE = '/api/v1'

// ─── Token storage ────────────────────────────────────────────────────────────
export function getToken(): string {
  return localStorage.getItem('access_token') ?? ''
}

export function saveTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

export function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export function authHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${getToken()}`,
  }
}

async function parseResponse<T>(res: Response): Promise<T> {
  const body = await res.json()
  if (!res.ok) {
    const msg = body?.error?.message ?? body?.detail ?? `Error ${res.status}`
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  // Support both wrapped { success, data } and raw FastAPI body
  return (body?.data ?? body) as T
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  return parseResponse<LoginResponse>(res)
}

// ─── Employee Profile ─────────────────────────────────────────────────────────

export interface EmployeeProfile {
  id: string
  user_id: string
  first_name: string
  last_name: string
  email: string
  phone: string | null
  phone_2: string | null
  personal_email: string | null
  gender: string | null
  date_of_birth: string | null
  designation: string | null
  department: string | null
  department_id: string | null
  date_joined: string | null
  employment_status: string
  project: string | null
  joining_salary: number | null
  role: string
  staff_photo_url: string | null
  // Address
  door_no: string | null
  street: string | null
  village_town: string | null
  pin_code: string | null
  // IDs
  aadhaar_number: string | null
  pan_number: string | null
  uan_number: string | null
  esi_number: string | null
  driving_license_number: string | null
  // Banking
  bank_name: string | null
  bank_branch: string | null
  bank_account_number: string | null
  ifsc_code: string | null
  // Emergency
  emergency_contact_name: string | null
  emergency_contact_number: string | null
  emergency_contact_relation: string | null
  // Education
  highest_qualification: string | null
  year_of_passing: string | null
  percentage: string | null
  institute_name: string | null
  // Experience
  last_firm_name: string | null
  years_of_experience: string | null
  last_designation: string | null
  last_drawn_salary: number | null
  reason_to_quit: string | null
  referred_by: string | null
  health_issues: string | null
  allergies: string | null
}

export async function getMyProfile(): Promise<EmployeeProfile> {
  const res = await fetch(`${API_BASE}/employees/me`, { headers: authHeaders() })
  return parseResponse<EmployeeProfile>(res)
}
