import { apiFetchData } from './http'

export interface EmployeeGrade {
  id: string
  company_id: string
  name: string
  default_leave_policy?: string
  default_salary_structure?: string
  is_active: number
  created_at?: string
  updated_at?: string
}

export async function listEmployeeGrades(): Promise<EmployeeGrade[]> {
  return apiFetchData<EmployeeGrade[]>('/employee-grades')
}

export async function createEmployeeGrade(payload: Partial<EmployeeGrade>): Promise<EmployeeGrade> {
  return apiFetchData<EmployeeGrade>('/employee-grades', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateEmployeeGrade(id: string, payload: Partial<EmployeeGrade>): Promise<EmployeeGrade> {
  return apiFetchData<EmployeeGrade>(`/employee-grades/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteEmployeeGrade(id: string): Promise<void> {
  await apiFetchData<EmployeeGrade>(`/employee-grades/${id}`, { method: 'DELETE' })
}
