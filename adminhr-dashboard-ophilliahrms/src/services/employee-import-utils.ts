import type { Employee } from './employee.types'

// ─── Constants ───────────────────────────────────────────────────────────────
export const TEMPLATE_HEADERS = [
  'first_name', 'last_name', 'email',
  'phone', 'phone_2', 'gender', 'date_of_birth', 'personal_email',
  'employee_code', 'date_joined', 'employment_status', 'designation', 'joining_salary', 'role', 'project',
  'department',
  'salary_mode', 'bank_name', 'bank_branch', 'bank_account_number', 'ifsc_code',
  'door_no', 'street', 'village_town', 'pin_code',
  'aadhaar_number', 'pan_number', 'uan_number', 'esi_number', 'driving_license_number',
  'emergency_contact_name', 'emergency_contact_number', 'emergency_contact_relation',
  'highest_qualification', 'institute_name', 'year_of_passing', 'percentage',
  'last_firm_name', 'last_designation', 'years_of_experience', 'last_drawn_salary', 'reason_to_quit',
  'health_issues', 'allergies', 'referred_by',
]

export const EMPLOYEE_SYSTEM_FIELDS = TEMPLATE_HEADERS

const GENDER_MAP: Record<string, string> = {
  male: 'male', m: 'male', man: 'male',
  female: 'female', f: 'female', woman: 'female',
  other: 'other', o: 'other',
}
const STATUS_MAP: Record<string, string> = {
  active: 'active', a: 'active',
  inactive: 'inactive', i: 'inactive',
  terminated: 'terminated', t: 'terminated',
}
const SALARY_MODE_MAP: Record<string, string> = {
  bank: 'bank', cheque: 'cheque', check: 'cheque', cash: 'cash',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
export function normaliseField(field: string, val: string): string {
  const v = val.trim()
  if (field === 'gender')            return GENDER_MAP[v.toLowerCase()] ?? v
  if (field === 'employment_status') return STATUS_MAP[v.toLowerCase()]  ?? v
  if (field === 'salary_mode')       return SALARY_MODE_MAP[v.toLowerCase()] ?? v
  return v
}

export function isAlreadyExistsError(msg: string): boolean {
  const lower = msg.toLowerCase()
  return (
    lower.includes('409') ||
    lower.includes('already exist') ||
    lower.includes('already registered') ||
    lower.includes('duplicate') ||
    lower.includes('unique constraint') ||
    lower.includes('conflict')
  )
}

export function parseCsvLine(line: string): string[] {
  const fields: string[] = []
  let current = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') { current += '"'; i++ }
      else inQuotes = !inQuotes
    } else if (ch === ',' && !inQuotes) {
      fields.push(current.trim())
      current = ''
    } else {
      current += ch
    }
  }
  fields.push(current.trim())
  return fields
}

export function parseCsv(text: string): { headers: string[]; rows: Record<string, string>[] } {
  const lines = text.split(/\r?\n/).filter(l => l.trim() !== '')
  if (lines.length === 0) return { headers: [], rows: [] }
  const headers = parseCsvLine(lines[0]).map(h => h.toLowerCase().replace(/\s+/g, '_'))
  const rows = lines.slice(1).map(line => {
    const values = parseCsvLine(line)
    const row: Record<string, string> = {}
    headers.forEach((h, i) => { row[h] = values[i] ?? '' })
    return row
  })
  return { headers, rows }
}

export async function parseCsvHeaders(file: File): Promise<string[]> {
  const text = await file.text()
  const firstLine = text.split(/\r?\n/)[0] ?? ''
  return parseCsvLine(firstLine).map(h => h.toLowerCase().replace(/\s+/g, '_'))
}

export async function parseXlsxHeaders(file: File): Promise<string[]> {
  const { read, utils } = await import('xlsx')
  const buffer = await file.arrayBuffer()
  const wb = read(buffer, { type: 'array', sheetRows: 1 })
  const ws = wb.Sheets[wb.SheetNames[0]]
  if (!ws) return []
  const rows = utils.sheet_to_json<string[]>(ws, { header: 1 })
  const headers = (rows[0] ?? []) as string[]
  return headers.map(h => String(h ?? '').trim().toLowerCase().replace(/\s+/g, '_').replace(/-/g, '_'))
}

export function generateEmployeePassword(): string {
  const _UP = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
  const _LO = 'abcdefghjkmnpqrstuvwxyz'
  const _DG = '23456789'
  const _SP = '@#$!'
  const _ALL = _UP + _LO + _DG + _SP
  const pick = (s: string) => s[Math.floor(Math.random() * s.length)]
  const chars = [pick(_UP), pick(_LO), pick(_DG), pick(_SP),
                 ...Array.from({ length: 6 }, () => pick(_ALL))]
  for (let i = chars.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [chars[i], chars[j]] = [chars[j], chars[i]]
  }
  return chars.join('')
}

export function buildEmployeePayload(
  data: Record<string, string>,
  departmentId?: string,
): Record<string, any> {
  const today = new Date().toISOString().slice(0, 10)
  const payload: Record<string, any> = {
    first_name:        data.first_name?.trim(),
    last_name:         data.last_name?.trim(),
    email:             data.email?.toLowerCase().trim(),
    date_joined:       data.date_joined?.trim() || today,
    employment_status: data.employment_status?.trim() || 'active',
  }
  const strings = [
    'phone', 'phone_2', 'personal_email', 'designation', 'employee_code',
    'pan_number', 'aadhaar_number', 'bank_account_number', 'bank_name', 'bank_branch',
    'driving_license_number', 'uan_number', 'esi_number', 'ifsc_code',
    'door_no', 'street', 'village_town', 'pin_code', 'project',
    'last_firm_name', 'last_designation', 'reason_to_quit', 'years_of_experience',
  ]
  for (const f of strings) {
    if (data[f]?.trim()) payload[f] = data[f].trim()
  }
  if (data.gender?.trim())         payload.gender         = data.gender.toLowerCase().trim()
  if (data.date_of_birth?.trim())  payload.date_of_birth  = data.date_of_birth.trim()
  if (data.salary_mode?.trim())    payload.salary_mode    = data.salary_mode.toLowerCase().trim()

  const parseNum = (v: string) => { const n = parseFloat(v.replace(/,/g, '')); return isNaN(n) ? undefined : n }
  if (data.joining_salary?.trim())   payload.joining_salary   = parseNum(data.joining_salary)
  if (data.last_drawn_salary?.trim()) payload.last_drawn_salary = parseNum(data.last_drawn_salary)

  if (departmentId) payload.department_id = departmentId
  return payload
}
