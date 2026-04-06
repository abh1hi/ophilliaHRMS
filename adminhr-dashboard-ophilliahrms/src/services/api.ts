interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta: any | null;
  error: {
    code: string;
    message: string;
  } | null;
}

const BASE_URL = '/api'

const apiFetch = async <T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> => {
  const token = localStorage.getItem('access_token')
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  const result: ApiResponse<T> = await response.json()

  if (!response.ok) {
    throw new Error(result.error?.message || 'Something went wrong')
  }

  return result
}

export const authApi = {
  login: (credentials: any) => apiFetch<any>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials)
  }),
  getProfile: () => apiFetch<any>('/auth/profile'),
}

export const companyApi = {
  getCompanies: () => apiFetch<any[]>('/companies'),
  getStats: (companyId: string | number) => apiFetch<any>(`/companies/${companyId}/stats`),
  getRecentActivity: (companyId: string | number) => apiFetch<any[]>(`/companies/${companyId}/activity`),
}

export const employeeApi = {
  getEmployees: (params: Record<string, string> = {}) => {
    const query = new URLSearchParams(params).toString()
    return apiFetch<any[]>(`/employees?${query}`)
  }
}
