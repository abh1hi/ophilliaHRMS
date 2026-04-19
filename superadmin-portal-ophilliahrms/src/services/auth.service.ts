import { http } from './http'

export interface TokenClaims {
  sub: string
  role: string
  email: string
  company_id?: string
  exp: number
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export function decodeToken(token: string): TokenClaims | null {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/'))) as TokenClaims
  } catch {
    return null
  }
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return http.post<LoginResponse>('/auth/login', { email, password })
}
