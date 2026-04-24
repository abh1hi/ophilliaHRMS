import { apiFetchData } from './http'

export interface Notification {
  id: string
  company_id: string
  recipient_id: string
  recipient_role: string
  type: string
  title: string
  body?: string
  is_read: boolean
  related_record_id?: string | null
  related_record_type?: string | null
  created_at: string
}

export interface NotificationListResponse {
  total: number
  items: Notification[]
}

export interface UnreadCountResponse {
  unread_count: number
}

export async function getUnreadCount(): Promise<number> {
  try {
    const res = await apiFetchData<UnreadCountResponse>('/notifications/unread-count')
    return res.unread_count ?? 0
  } catch {
    return 0
  }
}

export async function listNotifications(limit = 20): Promise<Notification[]> {
  try {
    const res = await apiFetchData<NotificationListResponse>(`/notifications?limit=${limit}`)
    return res.items ?? []
  } catch {
    return []
  }
}

export async function markNotificationRead(id: string): Promise<void> {
  await apiFetchData<void>(`/notifications/${id}/read`, { method: 'PATCH' })
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiFetchData<void>('/notifications/read-all', { method: 'PATCH' })
}
