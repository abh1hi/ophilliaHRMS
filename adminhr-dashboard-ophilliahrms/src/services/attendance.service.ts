import { apiFetchData, apiFetchAuth, getToken, authHeaders } from './http'
import { API_BASE } from '../config'

export interface AttendanceRecord {
  id: string
  company_id: string
  employee_id: string
  date: string
  clock_in: string
  clock_out?: string
  work_hours?: number
  overtime_hours: number
  status: string
  state: string
  method: string
  notes?: string
  shift_number: number
  created_at: string
  updated_at: string
}

export interface AttendanceListResponse {
  total: number
  skip: number
  limit: number
  records: AttendanceRecord[]
}

export interface AttendanceFilters {
  employee_id?: string
  date_from?: string
  date_to?: string
  status?: string
  skip?: number
  limit?: number
}

export interface UploadResult {
  total: number
  succeeded: number
  failed: number
  errors: Array<{ row: number; error: string }>
}

export async function listAttendanceRecords(filters: AttendanceFilters = {}): Promise<AttendanceListResponse> {
  const params = new URLSearchParams()
  if (filters.employee_id) params.set('employee_id', filters.employee_id)
  if (filters.date_from) params.set('date_from', filters.date_from)
  if (filters.date_to) params.set('date_to', filters.date_to)
  if (filters.status) params.set('status', filters.status)
  if (filters.skip !== undefined) params.set('skip', String(filters.skip))
  if (filters.limit !== undefined) params.set('limit', String(filters.limit))
  const qs = params.toString() ? `?${params}` : ''
  return apiFetchData<AttendanceListResponse>(`/attendance${qs}`)
}

export async function updateAttendanceRecord(id: string, payload: Partial<AttendanceRecord>): Promise<AttendanceRecord> {
  return apiFetchData<AttendanceRecord>(`/attendance/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function downloadAttendanceTemplate(): Promise<void> {
  const response = await fetch(`${API_BASE}/attendance/upload/template`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  })
  if (!response.ok) throw new Error('Failed to download template')
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'attendance_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export async function uploadAttendanceCsv(file: File): Promise<UploadResult> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(`${API_BASE}/attendance/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: formData,
  })
  const body = await response.json()
  if (!response.ok) {
    throw new Error(body?.error?.message ?? `Error ${response.status}`)
  }
  return body.data as UploadResult
}

export async function getEmployeesForBulk(
  departmentId?: string,
  branchId?: string
): Promise<any[]> {
  const params = new URLSearchParams()
  if (departmentId) params.set('department_id', departmentId)
  if (branchId) params.set('branch_id', branchId)
  const qs = params.toString() ? `?${params}` : ''
  const res = await apiFetchAuth<{ success: boolean; data: any[] }>(`/attendance/employees${qs}`)
  return res.data ?? []
}
