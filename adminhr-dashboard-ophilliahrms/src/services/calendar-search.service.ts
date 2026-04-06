import { apiFetchData } from './http'

const BASE = '/calendar/search'

export interface SearchResult {
  id: string
  type: 'event' | 'task' | 'comment'
  title?: string
  body?: string
  start_time?: string
  status?: string
  priority?: string
  workspace_id?: string
  calendar_id?: string
  task_id?: string
  rank: number
}

export interface SearchParams {
  q: string
  type?: 'events' | 'tasks' | 'comments'
  workspace_id?: string
  fields?: string
}

export const search = (params: SearchParams) => {
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined) as [string, string][])
  ).toString()
  return apiFetchData<SearchResult[]>(`${BASE}?${qs}`)
}
