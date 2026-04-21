import { apiFetch, apiFetchData, apiFetchAuth } from './http'
import type { Employee, ListEmployeesParams, EmployeeListResult, RawEmployeeList } from './employee.types'

// Re-export types
export * from './employee.types'

// Re-export sub-services for backward compatibility
export * from './employee-invite.service'
export * from './employee-import.service'
export * from './employee-import-legacy.service'
export * from './employee-import-utils.ts'

// ─── Core Employee API ────────────────────────────────────────────────────────

export async function listEmployees(params: ListEmployeesParams = {}): Promise<EmployeeListResult> {
  const {
    page = 1, page_size = 20,
    search, department_id, employment_status, account_status,
    sort = 'created_at', order = 'desc',
  } = params

  const skip = (page - 1) * page_size
  const limit = page_size

  const qs = new URLSearchParams()
  qs.set('skip', String(skip))
  qs.set('limit', String(limit))
  if (search)            qs.set('search', search)
  if (department_id)     qs.set('department_id', department_id)
  if (employment_status) qs.set('employment_status', employment_status)
  if (account_status)    qs.set('account_status', account_status)
  if (sort)              qs.set('sort', sort)
  if (order)             qs.set('order', order)

  const raw = await apiFetchAuth<RawEmployeeList>(`/employees?${qs.toString()}`)
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
  const result = await apiFetchData<Employee>('/employees', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
  if (!result?.id) {
    throw new Error('Server accepted the request but did not return a valid employee record')
  }
  return result
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

/** POST /employees — creates a new employee record. Alias for createEmployee but with Record<string, any>. */
export async function createEmployeeRecord(payload: Record<string, any>): Promise<Employee> {
  return apiFetchData<Employee>('/employees', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
