import { http } from './http'

export interface Company {
  id: string
  name: string
  domain?: string
  is_active: boolean
  created_at: string
}

export interface AdminUser {
  id: string
  email: string
  role: string
  is_company_owner: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CompanyListResponse {
  total: number
  companies: Company[]
}

export interface CreateCompanyPayload {
  name: string
  domain?: string
  admin: {
    email: string
    password: string
  }
}

export interface CompanyWithAdminResponse {
  company: Company
  admin: AdminUser
}

export function listCompanies(): Promise<CompanyListResponse> {
  return http.get<CompanyListResponse>('/auth/companies')
}

export function createCompanyWithAdmin(payload: CreateCompanyPayload): Promise<CompanyWithAdminResponse> {
  return http.post<CompanyWithAdminResponse>('/auth/companies', payload)
}

export function deactivateCompany(companyId: string): Promise<Company> {
  return http.delete<Company>(`/auth/companies/${companyId}`)
}

export function reactivateCompany(companyId: string): Promise<Company> {
  return http.patch<Company>(`/auth/companies/${companyId}`, { is_active: true })
}
