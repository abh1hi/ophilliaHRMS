const BASE_URL = '/api/v1'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('sa_access_token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const resp = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (resp.status === 401) {
    localStorage.removeItem('sa_access_token')
    localStorage.removeItem('sa_refresh_token')
    window.location.href = '/login'
    throw new Error('Session expired')
  }

  const body = await resp.json().catch(() => ({}))

  if (!resp.ok) {
    throw new Error(body?.detail || body?.message || `HTTP ${resp.status}`)
  }

  return body as T
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(data) }),
  patch: <T>(path: string, data: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
