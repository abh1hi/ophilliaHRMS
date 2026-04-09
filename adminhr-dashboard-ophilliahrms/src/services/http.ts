import { API_BASE } from '../config'

// ─── Token Storage ─────────────────────────────────────────────────────────────
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
  localStorage.removeItem('selected_company_id')
}

export function authHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${getToken()}`,
  }
}

// ─── Standard Response Envelope (per API contract) ────────────────────────────
export interface ApiResponse<T> {
  success: boolean
  data: T
  meta: PaginationMeta | null
  error: { code: string; message: string } | null
}

export interface PaginationMeta {
  page: number
  page_size: number
  total_items: number
  total_pages: number
}

// ─── Base Fetch Helper ─────────────────────────────────────────────────────────
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const headers = {
    ...authHeaders(),
    ...(options.headers as Record<string, string>),
  }

  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers })
  const body: ApiResponse<T> = await response.json()

  if (!response.ok || body?.success === false) {
    const msg = body?.error?.message ?? `Error ${response.status}`
    throw new Error(msg)
  }

  return body
}

// ─── Raw fetch (unwraps data directly) ────────────────────────────────────────
export async function apiFetchData<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await apiFetch<T>(endpoint, options)
  return res.data
}

// ─── Authenticated raw fetch (auth headers but no envelope assumption) ───────────
// Use this for endpoints that return non-enveloped JSON but still require a JWT.
export async function apiFetchAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = {
    ...authHeaders(),
    ...(options.headers as Record<string, string>),
  }
  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers })
  const body: T = await response.json()
  if (!response.ok) {
    const msg = (body as any)?.error?.message ?? (body as any)?.detail ?? `Error ${response.status}`
    throw new Error(msg)
  }
  return body
}

// ─── Direct fetch (for public endpoints that don't use envelope format) ───────────
export async function apiFetchDirect<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers })
  const body: T = await response.json()

  if (!response.ok) {
    throw new Error(`Error ${response.status}`)
  }

  return body
}
