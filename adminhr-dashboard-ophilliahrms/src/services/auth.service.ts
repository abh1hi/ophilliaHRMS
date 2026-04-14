import { apiFetchData, apiFetchAuth, apiFetchDirect, saveTokens, clearTokens } from './http'

// ─── Types ────────────────────────────────────────────────────────────────────
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

/** Decoded JWT claims included in every Ophillia HRMS access token */
export interface TokenClaims {
  sub: string
  role: string
  email: string
  company_id?: string
  exp: number
}

export interface AuthUser {
  id: string
  email: string
  role: string
  company_id?: string
}

export interface EmployeeProfile {
  id: string
  first_name: string
  last_name: string
  email: string
  employment_status?: string
  department?: { id: string; name: string }
  designation?: { id: string; name: string }
  branch?: { id: string; name: string }
}

// ─── JWT Decoder ──────────────────────────────────────────────────────────────
export function decodeToken(token: string): TokenClaims | null {
  try {
    const payload = token.split('.')[1]
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
    return decoded as TokenClaims
  } catch {
    return null
  }
}

// ─── Auth API ─────────────────────────────────────────────────────────────────
export async function login(email: string, password: string): Promise<LoginResponse & { claims: TokenClaims }> {
  const data = await apiFetchDirect<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })

  saveTokens(data.access_token, data.refresh_token ?? '')

  const claims = decodeToken(data.access_token)
  if (!claims) throw new Error('Invalid token received from server')

  if (claims.company_id) {
    localStorage.setItem('selected_company_id', claims.company_id)
  }

  return { ...data, claims }
}

export async function getAuthUser(): Promise<AuthUser> {
  return apiFetchDirect<AuthUser>('/auth/me')
}

export async function getEmployeeProfile(): Promise<EmployeeProfile | null> {
  try {
    return await apiFetchData<EmployeeProfile>('/employees/me')
  } catch {
    return null
  }
}

export function logout(): void {
  clearTokens()
}

// ─── Post-Login Context ───────────────────────────────────────────────────────
export interface Company {
  id: string
  name: string
  domain?: string
  is_active: boolean
  created_at: string
}

export interface PostLoginContext {
  role: string
  next_action: 'COMPLETE_ONBOARDING' | 'SELECT_COMPANY' | 'ENTER_DASHBOARD' | 'CREATE_COMPANY'
  onboarding_status?: string
  companies?: Company[]
  selected_company?: string
}

export async function postLoginContext(): Promise<PostLoginContext> {
  return apiFetchAuth<PostLoginContext>('/auth/post-login-context')
}

// ─── Company Management (Super Admin) ────────────────────────────────────────
export async function createCompany(name: string, domain?: string): Promise<Company> {
  return apiFetchDirect<Company>('/auth/companies', {
    method: 'POST',
    body: JSON.stringify({ name, ...(domain ? { domain } : {}) }),
  })
}

export async function selectCompany(companyId: string): Promise<LoginResponse> {
  const data = await apiFetchDirect<LoginResponse>('/auth/select-company', {
    method: 'POST',
    body: JSON.stringify({ company_id: companyId }),
  })
  saveTokens(data.access_token, data.refresh_token ?? '')
  localStorage.setItem('selected_company_id', companyId)
  return data
}

// ─── User Management (Admin / Super Admin) ────────────────────────────────────
export interface CreateUserPayload {
  email: string
  password: string
  role: string
  company_id?: string
}

export async function createUser(payload: CreateUserPayload): Promise<AuthUser> {
  return apiFetchDirect<AuthUser>('/auth/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
