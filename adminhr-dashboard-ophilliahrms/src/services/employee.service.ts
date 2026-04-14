import { apiFetch, apiFetchData, apiFetchAuth } from './http'
import type { PaginationMeta } from './http'

// ─── Types ────────────────────────────────────────────────────────────────────
export interface Employee {
  id: string
  user_id?: string
  employee_code?: string
  // Personal
  first_name: string
  last_name: string
  gender?: string
  date_of_birth?: string
  email: string
  phone?: string
  phone_2?: string
  personal_email?: string
  // Joining
  date_joined?: string
  offer_date?: string
  confirmation_date?: string
  contract_end_date?: string
  notice_days?: number
  date_of_retirement?: string
  employment_type?: string
  employment_status: 'active' | 'inactive' | 'terminated'
  // Dept & Grade
  department_id?: string
  department?: string
  designation?: string
  grade?: string
  branch?: string
  reports_to?: string
  // Salary & Banking
  salary_mode?: 'bank' | 'cheque' | 'cash'
  bank_name?: string
  bank_branch?: string
  bank_account_number?: string
  ifsc_code?: string
  joining_salary?: number
  // Contact
  door_no?: string
  street?: string
  village_town?: string
  pin_code?: string
  // IDs
  aadhaar_number?: string
  pan_number?: string
  uan_number?: string
  esi_number?: string
  driving_license_number?: string
  // Emergency
  emergency_contact_name?: string
  emergency_contact_number?: string
  emergency_contact_relation?: string
  // Education
  highest_qualification?: string
  institute_name?: string
  year_of_passing?: string
  percentage?: string
  // Experience
  last_firm_name?: string
  last_designation?: string
  years_of_experience?: string
  last_drawn_salary?: number
  reason_to_quit?: string
  // Exit
  resignation_date?: string
  relieving_date?: string
  // Misc
  project?: string
  role?: string
  staff_photo_url?: string
  referred_by?: string
  health_issues?: string
  allergies?: string
  created_at?: string
  updated_at?: string
  // Account provisioning (read-only)
  account_status?: 'not_registered' | 'invited' | 'active' | 'suspended'
  invite_expires_at?: string | null
}

export interface ListEmployeesParams {
  page?: number
  page_size?: number
  search?: string
  department_id?: string
  employment_status?: string
  account_status?: string
  sort?: string
  order?: 'asc' | 'desc'
}

export interface EmployeeListResult {
  data: Employee[]
  meta: PaginationMeta
}

// Raw shape returned by the backend list endpoint (non-enveloped)
interface RawEmployeeList {
  total: number
  skip: number
  limit: number
  employees: Employee[]
}

// ─── Employee API ─────────────────────────────────────────────────────────────
export async function listEmployees(params: ListEmployeesParams = {}): Promise<EmployeeListResult> {
  const {
    page = 1, page_size = 20,
    search, department_id, employment_status, account_status,
    sort = 'created_at', order = 'desc',   // newest first by default
  } = params

  // Convert page/page_size → skip/limit (backend uses skip/limit)
  const skip = (page - 1) * page_size
  const limit = page_size

  // Build query string — only include params that have real values
  const qs = new URLSearchParams()
  qs.set('skip', String(skip))
  qs.set('limit', String(limit))
  if (search)            qs.set('search', search)
  if (department_id)     qs.set('department_id', department_id)
  if (employment_status) qs.set('employment_status', employment_status)
  if (account_status)    qs.set('account_status', account_status)
  if (sort)              qs.set('sort', sort)
  if (order)             qs.set('order', order)

  const raw = await apiFetchAuth<RawEmployeeList>(`/employees?${qs.toString()}`)
  return {
    data: raw.employees ?? [],
    meta: {
      page: raw.limit > 0 ? Math.floor(raw.skip / raw.limit) + 1 : 1,
      page_size: raw.limit,
      total_items: raw.total,
      total_pages: raw.limit > 0 ? Math.ceil(raw.total / raw.limit) : 1,
    },
  }
}

export async function getEmployee(id: string): Promise<Employee> {
  return apiFetchData<Employee>(`/employees/${id}`)
}

export async function createEmployee(payload: Partial<Employee>): Promise<Employee> {
  const result = await apiFetchData<Employee>('/employees', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
  if (!result?.id) {
    throw new Error('Server accepted the request but did not return a valid employee record')
  }
  return result
}

export async function updateEmployee(id: string, payload: Partial<Employee>): Promise<Employee> {
  return apiFetchData<Employee>(`/employees/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteEmployee(id: string): Promise<void> {
  await apiFetch<null>(`/employees/${id}`, { method: 'DELETE' })
}

// ─── Account Provisioning (Invite Flow) ───────────────────────────────────────

export interface SendInviteResponse {
  employee_id: string
  email: string
  invite_url: string  // full URL for HR to copy and share — raw token is never exposed
  expires_at: string
  account_status: string
}

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

// ─── Bulk Import ──────────────────────────────────────────────────────────────

export interface EmployeeImportResult {
  total: number
  succeeded: number
  skipped: number
  failed: number
  errors: Array<{ row: number; field?: string; error: string; skipped?: boolean }>
}

/** Required columns are listed first; optional follow.
 *  Maps to BulkEmployeeImportItem fields on the backend.
 *  Extra fields (e.g. employment_status) are sent and silently ignored by Pydantic.
 */
const TEMPLATE_HEADERS = [
  // Required
  'first_name', 'last_name', 'email',
  // Personal
  'phone', 'phone_2', 'gender', 'date_of_birth', 'personal_email',
  // Employment (employment_status defaults to "active" on backend; include for info)
  'employee_code', 'date_joined', 'employment_status', 'designation', 'joining_salary', 'role', 'project',
  // Organisation (department string sent as-is; backend resolves via department_id if needed)
  'department',
  // Banking
  'salary_mode', 'bank_name', 'bank_branch', 'bank_account_number', 'ifsc_code',
  // Address
  'door_no', 'street', 'village_town', 'pin_code',
  // IDs
  'aadhaar_number', 'pan_number', 'uan_number', 'esi_number', 'driving_license_number',
  // Emergency
  'emergency_contact_name', 'emergency_contact_number', 'emergency_contact_relation',
  // Education
  'highest_qualification', 'institute_name', 'year_of_passing', 'percentage',
  // Experience
  'last_firm_name', 'last_designation', 'years_of_experience', 'last_drawn_salary', 'reason_to_quit',
  // Health & Other
  'health_issues', 'allergies', 'referred_by',
]

/** Exported so the mapping UI can enumerate all known system fields */
export const EMPLOYEE_SYSTEM_FIELDS = TEMPLATE_HEADERS

// ─── Template example rows ────────────────────────────────────────────────────
// Each inner array must follow the same order as TEMPLATE_HEADERS.
// These are realistic dummy records that cover the most common fields.
const TEMPLATE_EXAMPLE_ROWS: string[][] = [
  // first_name, last_name, email, phone, phone_2, gender, date_of_birth, personal_email,
  // employee_code, date_joined, employment_status, designation, joining_salary, role, project, department,
  // salary_mode, bank_name, bank_branch, bank_account_number, ifsc_code,
  // door_no, street, village_town, pin_code,
  // aadhaar_number, pan_number, uan_number, esi_number, driving_license_number,
  // emergency_contact_name, emergency_contact_number, emergency_contact_relation,
  // highest_qualification, institute_name, year_of_passing, percentage,
  // last_firm_name, last_designation, years_of_experience, last_drawn_salary, reason_to_quit,
  // health_issues, allergies, referred_by
  [
    'Rahul', 'Sharma', 'rahul.sharma@example.com', '9876543210', '', 'male', '1992-05-14', 'rahul.personal@gmail.com',
    'EMP-001', '2024-01-10', 'active', 'Software Engineer', '75000', 'employee', 'Project Alpha', 'Engineering',
    'bank', 'HDFC Bank', 'Koramangala', '50100012345678', 'HDFC0001234',
    '12A', 'MG Road', 'Bangalore', '560001',
    '234567890123', 'ABCDE1234F', '100234567890', '', 'KA01 20240001',
    'Sunita Sharma', '9876500001', 'Mother',
    'B.E. Computer Science', 'VTU Belgaum', '2014', '72.5',
    'Infosys Ltd', 'Junior Developer', '8', '60000', 'Better opportunity',
    '', '', 'Priya Nair',
  ],
  [
    'Priya', 'Nair', 'priya.nair@example.com', '9123456780', '9123456781', 'female', '1995-11-22', '',
    'EMP-002', '2024-02-01', 'active', 'HR Executive', '45000', 'hr', 'HR Operations', 'Human Resources',
    'bank', 'SBI', 'Andheri West', '20099876543210', 'SBIN0001234',
    '45', 'Link Road', 'Mumbai', '400053',
    '345678901234', 'BCDFE5678G', '200345678901', '', '',
    'Rajesh Nair', '9123400001', 'Father',
    'MBA HR', 'Symbiosis Pune', '2017', '68.0',
    'Wipro BPO', 'HR Coordinator', '5', '38000', 'Career growth',
    '', '', '',
  ],
  [
    'Amit', 'Verma', 'amit.verma@example.com', '8800001234', '', 'male', '1988-03-30', 'amit.v@yahoo.com',
    'EMP-003', '2023-11-15', 'active', 'Sales Manager', '90000', 'manager', 'Sales Q1', 'Sales',
    'cheque', 'ICICI Bank', 'Connaught Place', '00110023456789', 'ICIC0000123',
    '7B', 'Sector 15', 'Noida', '201301',
    '456789012345', 'CDEFG6789H', '300456789012', '3001234567', '',
    'Meena Verma', '8800009999', 'Spouse',
    'B.Com', 'Delhi University', '2010', '65.0',
    'Reliance Retail', 'Sales Executive', '12', '72000', 'Better role',
    'Mild asthma', '', 'Deepak Joshi',
  ],
  [
    'Sneha', 'Iyer', 'sneha.iyer@example.com', '7700009876', '', 'female', '1998-07-08', '',
    'EMP-004', '2024-03-20', 'active', 'UI/UX Designer', '55000', 'employee', 'Product Revamp', 'Design',
    'bank', 'Axis Bank', 'Banjara Hills', '91500087654321', 'UTIB0000456',
    '3', 'Film Nagar', 'Hyderabad', '500033',
    '567890123456', 'DEFGH7890I', '', '', '',
    'Arun Iyer', '7700001111', 'Brother',
    'B.Des', 'NID Ahmedabad', '2020', '81.0',
    '', '', '0', '', '',
    '', '', '',
  ],
  [
    'Mohammed', 'Khan', 'mohammed.khan@example.com', '9900112233', '', 'male', '1990-12-01', '',
    'EMP-005', '2024-01-25', 'active', 'Finance Analyst', '65000', 'employee', 'Audit FY24', 'Finance',
    'bank', 'Punjab National Bank', 'Lajpat Nagar', '01290098765432', 'PUNB0012300',
    '22', 'Zakir Nagar', 'New Delhi', '110025',
    '678901234567', 'EFGHI8901J', '400567890123', '', '',
    'Fatima Khan', '9900100000', 'Mother',
    'CA', 'ICAI', '2015', '55.0',
    'Deloitte India', 'Audit Associate', '7', '55000', 'Relocation',
    '', 'Dust allergy', '',
  ],
]

function csvEscape(val: string): string {
  // Wrap in quotes if value contains comma, quote, or newline
  if (val.includes(',') || val.includes('"') || val.includes('\n')) {
    return '"' + val.replace(/"/g, '""') + '"'
  }
  return val
}

export function downloadEmployeeTemplate(): void {
  const lines: string[] = [
    TEMPLATE_HEADERS.join(','),
    ...TEMPLATE_EXAMPLE_ROWS.map(row =>
      TEMPLATE_HEADERS.map((_, i) => csvEscape(row[i] ?? '')).join(',')
    ),
  ]
  const csv = lines.join('\n') + '\n'
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' }) // BOM for Excel
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'employee_import_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}

// ─── CSV parsing helpers ──────────────────────────────────────────────────────

function parseCsvLine(line: string): string[] {
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

function parseCsv(text: string): { headers: string[]; rows: Record<string, string>[] } {
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

const NUMERIC_FIELDS = new Set(['joining_salary', 'last_drawn_salary'])
// Only the fields the backend actually requires on BulkEmployeeImportItem
const REQUIRED_FIELDS = ['first_name', 'last_name', 'email'] as const

// Enum normalisers — makes imports case-insensitive for backend-validated enums
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

function normaliseField(field: string, val: string): string {
  const v = val.trim()
  if (field === 'gender')            return GENDER_MAP[v.toLowerCase()] ?? v
  if (field === 'employment_status') return STATUS_MAP[v.toLowerCase()]  ?? v
  if (field === 'salary_mode')       return SALARY_MODE_MAP[v.toLowerCase()] ?? v
  return v
}


function isAlreadyExistsError(msg: string): boolean {
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

// ─── Backend bulk-import response types ──────────────────────────────────────

interface BulkImportRow {
  index: number
  success: boolean
  employee: Employee | null
  error: string | null
}

interface BulkImportBackendResponse {
  total: number
  succeeded: number
  failed: number
  results: BulkImportRow[]
}

// ─── Bulk CSV import — single batch request to /employees/bulk-import ─────────

export interface ImportProgress {
  done: number
  total: number
}

/**
 * Parses the CSV, auto-generates passwords for rows missing one, then sends the
 * entire batch to POST /employees/bulk-import in a single request.
 *
 * columnMap: maps system field name → CSV column header.
 * If omitted, falls back to exact header match.
 */
export async function uploadEmployeeCsv(
  file: File,
  onProgress?: (progress: ImportProgress) => void,
  columnMap?: Record<string, string>,
): Promise<EmployeeImportResult> {
  const text = await file.text()
  const { rows } = parseCsv(text)

  const result: EmployeeImportResult = {
    total: rows.length, succeeded: 0, skipped: 0, failed: 0, errors: [],
  }
  if (rows.length === 0) return result

  // Helper: read a value from a row, respecting the column map
  const get = (raw: Record<string, string>, field: string): string => {
    const csvCol = columnMap?.[field]
    return (csvCol ? raw[csvCol] : raw[field]) ?? ''
  }

  // ── Phase 1: Client-side validation + payload building ──────────────────
  const payloads: (Record<string, any> | null)[] = []

  for (let i = 0; i < rows.length; i++) {
    const rowNum = i + 2 // row 1 = header

    const missing = REQUIRED_FIELDS.filter(f => !get(rows[i], f))
    if (missing.length > 0) {
      result.failed++
      result.errors.push({ row: rowNum, field: missing[0], error: `Required field "${missing[0]}" is empty` })
      payloads.push(null)
      continue
    }

    const payload: Record<string, any> = {}
    for (const sysField of TEMPLATE_HEADERS) {
      const val = get(rows[i], sysField)
      if (val === '' || val === undefined) continue
      if (NUMERIC_FIELDS.has(sysField)) {
        const n = parseFloat(val)
        if (!isNaN(n)) payload[sysField] = n
      } else {
        payload[sysField] = normaliseField(sysField, val)
      }
    }

    payloads.push(payload)
  }

  // Collect valid rows (client-side failures have null payloads)
  const validIndices: number[] = []
  const validPayloads: Record<string, any>[] = []
  for (let i = 0; i < payloads.length; i++) {
    if (payloads[i] !== null) {
      validIndices.push(i)
      validPayloads.push(payloads[i]!)
    }
  }

  if (validPayloads.length === 0) return result

  onProgress?.({ done: 0, total: rows.length })

  // ── Phase 2: Single batch request ───────────────────────────────────────
  let backendResult: BulkImportBackendResponse
  try {
    backendResult = await apiFetchAuth<BulkImportBackendResponse>('/employees/bulk-import', {
      method: 'POST',
      body: JSON.stringify(validPayloads),
    })
  } catch (err: any) {
    // If the whole request fails (e.g. 429, 500), mark all valid rows as failed
    const msg: string = err.message ?? 'Import request failed'
    for (let j = 0; j < validIndices.length; j++) {
      result.failed++
      result.errors.push({ row: validIndices[j] + 2, field: undefined, error: msg })
    }
    onProgress?.({ done: rows.length, total: rows.length })
    return result
  }

  onProgress?.({ done: rows.length, total: rows.length })

  // ── Phase 3: Map backend per-row results ─────────────────────────────────
  for (const br of backendResult.results) {
    // br.index is 0-based within validPayloads; map back to original row
    const originalIdx = validIndices[br.index]
    const rowNum = originalIdx + 2

    if (br.success) {
      result.succeeded++
    } else {
      const errMsg = br.error ?? 'Unknown error'
      if (isAlreadyExistsError(errMsg)) {
        result.skipped++
        result.errors.push({
          row: rowNum, field: 'email',
          error: 'Skipped — employee with this email already exists',
          skipped: true,
        })
      } else {
        result.failed++
        result.errors.push({ row: rowNum, field: undefined, error: errMsg })
      }
    }
  }

  return result
}

/** Also export a pure CSV-header parser so the mapping UI can read headers without importing */
export async function parseCsvHeaders(file: File): Promise<string[]> {
  const text = await file.text()
  const firstLine = text.split(/\r?\n/)[0] ?? ''
  return parseCsvLine(firstLine).map(h => h.toLowerCase().replace(/\s+/g, '_'))
}

/** Parse first-row headers from an XLSX file using SheetJS */
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

// ─── New Pipeline: Types ──────────────────────────────────────────────────────

export interface AutoCorrection {
  row: number
  field: string
  original: string
  fixed: string
}

export interface RowIssue {
  row: number
  field: string
  error: string
  suggested_fix: string
  original_value: string
  is_warning: boolean
  is_cross_row: boolean
}

export interface PreviewRow {
  index: number
  data: Record<string, string>
  /** 'valid' | 'warning' | 'error' | 'cross_row' */
  status: string
  issues: RowIssue[]
}

export interface PreviewSummary {
  valid: number
  warnings: number
  errors: number
  auto_corrections: number
  cross_row_duplicates: number
}

export interface ImportPreviewResult {
  rows: PreviewRow[]
  summary: PreviewSummary
  auto_corrections: AutoCorrection[]
}

export interface ImportJobUploadResult {
  job_id: string
  total_rows: number
  auto_corrections: AutoCorrection[]
  cross_row_warnings: RowIssue[]
  idempotent: boolean
}

export interface ImportJob {
  id: string
  company_id: string
  uploaded_by: string
  file_name: string
  file_size_bytes?: number
  schema_version: string
  /** 'pending' | 'processing' | 'completed' | 'failed' | 'dry_run' */
  status: string
  duplicate_strategy: string
  total_rows: number
  succeeded_rows: number
  failed_rows: number
  skipped_rows: number
  error_log?: Array<Record<string, string>>
  auto_corrections?: AutoCorrection[]
  created_at: string
  completed_at?: string
}

// ─── New Pipeline: API Functions ──────────────────────────────────────────────

/** Call the preview endpoint — no DB writes, no job created. Returns per-row status. */
export async function previewImportFile(file: File): Promise<ImportPreviewResult> {
  const { API_BASE } = await import('../config')
  const { getToken } = await import('./http')
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/employees/bulk-import/preview`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form,
  })
  const body = await res.json()
  if (!res.ok) {
    throw new Error(body?.detail ?? `Preview failed (${res.status})`)
  }
  return body as ImportPreviewResult
}

/** Upload file to start async Celery import job. Returns job_id to poll. */
export async function uploadImportFile(
  file: File,
  dryRun: boolean,
  duplicateStrategy: 'skip' | 'update' | 'fail',
): Promise<ImportJobUploadResult> {
  const { API_BASE } = await import('../config')
  const { getToken } = await import('./http')
  const form = new FormData()
  form.append('file', file)
  form.append('dry_run', String(dryRun))
  form.append('duplicate_strategy', duplicateStrategy)
  const res = await fetch(`${API_BASE}/employees/bulk-import/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form,
  })
  const body = await res.json()
  if (!res.ok) {
    throw new Error(body?.detail ?? `Upload failed (${res.status})`)
  }
  return body as ImportJobUploadResult
}

/** Poll the status of a running import job. */
export async function pollImportJob(jobId: string): Promise<ImportJob> {
  const { apiFetchAuth } = await import('./http')
  return apiFetchAuth<ImportJob>(`/employees/bulk-import/jobs/${jobId}`)
}

/** Get list of recent import jobs for the company (audit log). */
export async function getImportHistory(limit = 50): Promise<ImportJob[]> {
  const { apiFetchAuth } = await import('./http')
  return apiFetchAuth<ImportJob[]>(`/employees/bulk-import/jobs?limit=${limit}`)
}

// ─── Queue-Import helpers ─────────────────────────────────────────────────────

/** Password characters — no ambiguous 0/O/l/1/I */
const _UP = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
const _LO = 'abcdefghjkmnpqrstuvwxyz'
const _DG = '23456789'
const _SP = '@#$!'
const _ALL = _UP + _LO + _DG + _SP

/** Generate a 10-char password guaranteed to have upper + lower + digit + special. */
export function generateEmployeePassword(): string {
  const pick = (s: string) => s[Math.floor(Math.random() * s.length)]
  const chars = [pick(_UP), pick(_LO), pick(_DG), pick(_SP),
                 ...Array.from({ length: 6 }, () => pick(_ALL))]
  for (let i = chars.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [chars[i], chars[j]] = [chars[j], chars[i]]
  }
  return chars.join('')
}

/** Build a clean payload for POST /employees from the raw string data map. */
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

/** POST /employees — creates a new employee record. */
export async function createEmployeeRecord(payload: Record<string, any>): Promise<Employee> {
  return apiFetchData<Employee>('/employees', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/** Trigger browser download of error CSV for a completed/failed job. */
export function downloadImportErrors(jobId: string): void {
  const { API_BASE } = require('../config')
  const { getToken } = require('./http')
  // Use a hidden <a> with Authorization header via a fetch-then-blob approach
  const { apiFetchAuth: _auth } = require('./http')
  fetch(`${API_BASE}/employees/bulk-import/jobs/${jobId}/errors.csv`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  }).then(res => res.blob()).then(blob => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `import_${jobId}_errors.csv`
    a.click()
    URL.revokeObjectURL(url)
  })
}
