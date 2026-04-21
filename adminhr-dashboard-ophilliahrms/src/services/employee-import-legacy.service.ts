import { apiFetchAuth } from './http'
import type { Employee, EmployeeImportResult, ImportProgress } from './employee.types'
import { 
  TEMPLATE_HEADERS, parseCsv, normaliseField, isAlreadyExistsError 
} from './employee-import-utils'

const NUMERIC_FIELDS = new Set(['joining_salary', 'last_drawn_salary'])
const REQUIRED_FIELDS = ['first_name', 'last_name', 'email'] as const

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

const TEMPLATE_EXAMPLE_ROWS: string[][] = [
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
]

function csvEscape(val: string): string {
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
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'employee_import_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}

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

  const get = (raw: Record<string, string>, field: string): string => {
    const csvCol = columnMap?.[field]
    return (csvCol ? raw[csvCol] : raw[field]) ?? ''
  }

  const payloads: (Record<string, any> | null)[] = []
  for (let i = 0; i < rows.length; i++) {
    const rowNum = i + 2
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

  let backendResult: BulkImportBackendResponse
  try {
    backendResult = await apiFetchAuth<BulkImportBackendResponse>('/employees/bulk-import', {
      method: 'POST',
      body: JSON.stringify(validPayloads),
    })
  } catch (err: any) {
    const msg: string = err.message ?? 'Import request failed'
    for (let j = 0; j < validIndices.length; j++) {
      result.failed++
      result.errors.push({ row: validIndices[j] + 2, field: undefined, error: msg })
    }
    onProgress?.({ done: rows.length, total: rows.length })
    return result
  }

  onProgress?.({ done: rows.length, total: rows.length })

  for (const br of backendResult.results) {
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
