import { apiFetchData } from './http'

const BASE = '/leave/leave-ledger'

export interface LeaveLedgerEntry {
  id: string
  company_id: string
  employee_id: string
  leave_type_id: string
  from_date: string
  to_date: string
  leaves: number
  transaction_type: 'allocation' | 'application' | 'adjustment' | 'encashment' | 'carry_forward'
  transaction_name?: string
  is_carry_forward: number
  is_expired: number
  is_lwp: number
  holiday_list_id?: string
  created_at?: string
}

export interface LeaveLedgerList {
  total: number
  skip: number
  limit: number
  entries: LeaveLedgerEntry[]
}

export async function listLeaveLedgerEntries(params?: {
  employee_id?: string
  leave_type_id?: string
  transaction_type?: string
  from_date?: string
  to_date?: string
  skip?: number
  limit?: number
}): Promise<LeaveLedgerList> {
  const q = new URLSearchParams()
  if (params) Object.entries(params).forEach(([k, v]) => v !== undefined && q.set(k, String(v)))
  return apiFetchData<LeaveLedgerList>(`${BASE}/?${q}`)
}
