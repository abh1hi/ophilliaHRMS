import { apiFetchData } from './http'

export interface OvertimePolicy {
  id: string
  company_id: string
  employee_id?: string
  department_id?: string
  location_id?: string
  jurisdiction: 'INDIA' | 'EU' | 'CUSTOM'
  compliance_profile?: string
  daily_ot_threshold_hours: number
  weekly_ot_threshold_hours: number
  max_daily_hours: number
  daily_ot_multiplier: number
  weekly_ot_multiplier: number
  weekend_multiplier: number
  holiday_multiplier: number
  prefer_comp_off: boolean
  comp_off_ratio: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export async function listOvertimePolicies(params?: {
  employee_id?: string
  department_id?: string
  location_id?: string
}): Promise<OvertimePolicy[]> {
  const q = new URLSearchParams()
  if (params?.employee_id)  q.set('employee_id', params.employee_id)
  if (params?.department_id) q.set('department_id', params.department_id)
  if (params?.location_id)  q.set('location_id', params.location_id)
  const qs = q.toString() ? `?${q.toString()}` : ''
  return apiFetchData<OvertimePolicy[]>(`/overtime/policies${qs}`)
}

export async function createOvertimePolicy(payload: Partial<OvertimePolicy>): Promise<OvertimePolicy> {
  return apiFetchData<OvertimePolicy>('/overtime/policies', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function createFromTemplate(template_key: 'INDIA_FACTORIES_ACT' | 'EU_WTD_48H'): Promise<OvertimePolicy> {
  return apiFetchData<OvertimePolicy>('/overtime/policies/from-template', {
    method: 'POST',
    body: JSON.stringify({ template_key }),
  })
}

export async function updateOvertimePolicy(id: string, payload: Partial<OvertimePolicy>): Promise<OvertimePolicy> {
  return apiFetchData<OvertimePolicy>(`/overtime/policies/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteOvertimePolicy(id: string): Promise<void> {
  await apiFetchData<void>(`/overtime/policies/${id}`, { method: 'DELETE' })
}
