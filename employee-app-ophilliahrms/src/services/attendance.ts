// Attendance API service for employee-app
// Base URL points at the gateway via env (defaults to localhost in dev)

import { authHeaders } from './api'

const API_BASE = '/api/v1'

async function handleResponse<T>(res: Response): Promise<T> {
  const body = await res.json()
  if (!res.ok) {
    throw new Error(body?.error?.message ?? body?.detail ?? `API error ${res.status}`)
  }
  return (body?.data ?? body) as T
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Task {
  id: string
  attendance_record_id: string
  employee_id: string
  assigned_by: string | null
  title: string
  details: string | null
  estimated_finish_time: string | null
  expected_expenses: number | null
  status: 'pending' | 'completed' | 'partially_completed' | 'not_completed'
  completion_notes: string | null
  actual_expenses: number | null
  created_at: string
  updated_at: string
}

export interface AttendanceRecord {
  id: string
  employee_id: string
  clock_in: string
  clock_out: string | null
  clock_in_lat: number | null
  clock_in_lng: number | null
  clock_out_lat: number | null
  clock_out_lng: number | null
  clock_in_location_name: string | null
  clock_out_location_name: string | null
  work_hours: number | null
  overtime_hours: number
  day_rating: number | null
  status: string
  method: string
  notes: string | null
  date: string
  tasks: Task[]
}

export interface TaskCreate {
  title: string
  details?: string
  estimated_finish_time?: string
  expected_expenses?: number
}

export interface TaskCompleteItem {
  task_id: string
  status: 'completed' | 'partially_completed' | 'not_completed'
  completion_notes?: string
  actual_expenses?: number
}

export interface TaskAssignRequest {
  target_employee_id: string
  title: string
  details?: string
  estimated_finish_time?: string
  expected_expenses?: number
}

// ─── API functions ────────────────────────────────────────────────────────────

export async function getTodayRecord(): Promise<AttendanceRecord | null> {
  const res = await fetch(`${API_BASE}/attendance/me/today`, { headers: authHeaders() })
  if (res.status === 204 || res.status === 404) return null
  const body = await res.json()
  if (!res.ok) return null
  return (body?.data ?? body) as AttendanceRecord
}

export async function clockIn(
  lat: number | null,
  lng: number | null,
  locationName?: string
): Promise<AttendanceRecord> {
  const res = await fetch(`${API_BASE}/attendance/clock-in`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ latitude: lat, longitude: lng, location_name: locationName }),
  })
  return handleResponse<AttendanceRecord>(res)
}

export async function clockOut(
  lat: number | null,
  lng: number | null,
  locationName: string | undefined,
  dayRating: number,
  taskCompletions: TaskCompleteItem[]
): Promise<AttendanceRecord> {
  const res = await fetch(`${API_BASE}/attendance/clock-out`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      latitude: lat,
      longitude: lng,
      location_name: locationName,
      day_rating: dayRating,
      task_completions: taskCompletions,
    }),
  })
  return handleResponse<AttendanceRecord>(res)
}

export async function addTask(recordId: string, data: TaskCreate): Promise<Task> {
  const res = await fetch(`${API_BASE}/attendance/tasks?record_id=${recordId}`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<Task>(res)
}

export async function updateTask(taskId: string, data: Partial<TaskCreate>): Promise<Task> {
  const res = await fetch(`${API_BASE}/attendance/tasks/${taskId}`, {
    method: 'PATCH',
    headers: authHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<Task>(res)
}

export async function deleteTask(taskId: string): Promise<void> {
  await fetch(`${API_BASE}/attendance/tasks/${taskId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })
}

export async function completeTask(taskId: string, data: Omit<TaskCompleteItem, 'task_id'>): Promise<Task> {
  const res = await fetch(`${API_BASE}/attendance/tasks/${taskId}/complete`, {
    method: 'PATCH',
    headers: authHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<Task>(res)
}

export async function assignTaskToEmployee(data: TaskAssignRequest): Promise<Task> {
  const res = await fetch(`${API_BASE}/attendance/tasks/assign`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<Task>(res)
}

// ─── Geolocation helper ───────────────────────────────────────────────────────

export function getCurrentPosition(): Promise<{ lat: number; lng: number }> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not supported'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      (err) => reject(new Error(err.message)),
      { timeout: 8000, maximumAge: 30000 }
    )
  })
}
