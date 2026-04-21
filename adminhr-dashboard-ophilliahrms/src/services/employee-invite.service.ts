import { apiFetchAuth } from './http'
import type { Employee, SendInviteResponse } from './employee.types'

/** Send (or resend) a portal invite. Returns invite_url for HR to copy and share manually. */
export async function sendEmployeeInvite(id: string): Promise<SendInviteResponse> {
  return apiFetchAuth<SendInviteResponse>(`/employees/${id}/send-invite`, { method: 'POST' })
}

/** Resend invite — generates new token. Old token stays valid until it expires. */
export async function resendEmployeeInvite(id: string): Promise<SendInviteResponse> {
  return apiFetchAuth<SendInviteResponse>(`/employees/${id}/resend-invite`, { method: 'POST' })
}

/** Revoke invite — sets account back to not_registered. */
export async function revokeEmployeeInvite(id: string): Promise<void> {
  await apiFetchAuth(`/employees/${id}/revoke-invite`, { method: 'POST' })
}

/** Disable employee's portal access (sets auth account is_active=false). */
export async function disableEmployeeAccount(id: string): Promise<Employee> {
  return apiFetchAuth<Employee>(`/employees/${id}/disable-account`, { method: 'POST' })
}
