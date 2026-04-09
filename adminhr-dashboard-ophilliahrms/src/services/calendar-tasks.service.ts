import { apiFetchData } from './http'

const BASE = '/calendar/tasks'

export interface TaskAssignee {
  id: string
  employee_id: string
  assigned_at: string
  assigned_by?: string
}

export interface TaskComment {
  id: string
  task_id: string
  author_id: string
  parent_comment_id?: string
  body: string
  status: 'active' | 'edited' | 'deleted'
  edited_at?: string
  created_at: string
  updated_at: string
}

export interface CalendarTask {
  id: string
  company_id: string
  workspace_id?: string
  event_id?: string
  parent_task_id?: string
  title: string
  description?: string
  status: 'todo' | 'in_progress' | 'blocked' | 'in_review' | 'done' | 'cancelled'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  due_date?: string
  start_date?: string
  estimated_hours?: number
  actual_hours?: number
  created_by: string
  completed_at?: string
  tags: string[]
  attachments: { name: string; url: string; mime_type: string }[]
  assignees: TaskAssignee[]
  subtask_count?: number
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  workspace_id?: string
  event_id?: string
  parent_task_id?: string
  title: string
  description?: string
  status?: string
  priority?: string
  due_date?: string
  start_date?: string
  estimated_hours?: number
  tags?: string[]
  assignees?: string[]
}

export interface TaskUpdate {
  title?: string
  description?: string
  priority?: string
  due_date?: string
  start_date?: string
  estimated_hours?: number
  actual_hours?: number
  tags?: string[]
}

export interface TaskListParams {
  workspace_id?: string
  status?: string
  priority?: string
  assignee_id?: string
  due_before?: string
  due_after?: string
  page?: number
  page_size?: number
}

// Tasks
export const listTasks = (params: TaskListParams = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)]))
  ).toString()
  return apiFetchData<CalendarTask[]>(qs ? `${BASE}?${qs}` : BASE)
}

export const getTask = (id: string) =>
  apiFetchData<CalendarTask>(`${BASE}/${id}`)

export const createTask = (payload: TaskCreate) =>
  apiFetchData<CalendarTask>(BASE, { method: 'POST', body: JSON.stringify(payload) })

export const updateTask = (id: string, payload: TaskUpdate) =>
  apiFetchData<CalendarTask>(`${BASE}/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })

export const updateTaskStatus = (id: string, status: string) =>
  apiFetchData<CalendarTask>(`${BASE}/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) })

export const deleteTask = (id: string) =>
  apiFetchData<void>(`${BASE}/${id}`, { method: 'DELETE' })

// Assignees
export const addAssignee = (taskId: string, employeeId: string) =>
  apiFetchData<TaskAssignee>(`${BASE}/${taskId}/assignees`, {
    method: 'POST',
    body: JSON.stringify({ employee_id: employeeId }),
  })

export const removeAssignee = (taskId: string, employeeId: string) =>
  apiFetchData<void>(`${BASE}/${taskId}/assignees/${employeeId}`, { method: 'DELETE' })

// Comments
export const listComments = (taskId: string) =>
  apiFetchData<TaskComment[]>(`${BASE}/${taskId}/comments`)

export const addComment = (taskId: string, body: string, parentCommentId?: string) =>
  apiFetchData<TaskComment>(`${BASE}/${taskId}/comments`, {
    method: 'POST',
    body: JSON.stringify({ body, parent_comment_id: parentCommentId }),
  })

export const editComment = (taskId: string, commentId: string, body: string) =>
  apiFetchData<TaskComment>(`${BASE}/${taskId}/comments/${commentId}`, {
    method: 'PATCH',
    body: JSON.stringify({ body }),
  })

export const deleteComment = (taskId: string, commentId: string) =>
  apiFetchData<void>(`${BASE}/${taskId}/comments/${commentId}`, { method: 'DELETE' })

// Subtasks
export const listSubtasks = (taskId: string) =>
  apiFetchData<CalendarTask[]>(`${BASE}/${taskId}/subtasks`)

export const createSubtask = (taskId: string, payload: Omit<TaskCreate, 'parent_task_id'>) =>
  apiFetchData<CalendarTask>(`${BASE}/${taskId}/subtasks`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
