/**
 * Seed factory for e2e tests.
 *
 * All generated IDs include Date.now() + a random number so parallel test
 * workers never collide on shared data (localStorage keys, employee IDs, etc).
 */

export function uniqueId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 100_000)}`
}

export interface MockEmployee {
  id: string
  first_name: string
  last_name: string
  email: string
  employee_code: string
  employment_status: 'active' | 'inactive'
  department: string
  designation: string
}

export function makeEmployee(overrides: Partial<MockEmployee> = {}): MockEmployee {
  const id = uniqueId('emp')
  return {
    id,
    first_name:        `TestFirst`,
    last_name:         `TestLast-${id}`,
    email:             `${id}@test.com`,
    employee_code:     `CODE-${id}`,
    employment_status: 'active',
    department:        'Engineering',
    designation:       'Engineer',
    ...overrides,
  }
}

export interface MockDepartment {
  id: string
  name: string
  employee_count: number
}

export function makeDepartment(overrides: Partial<MockDepartment> = {}): MockDepartment {
  const id = uniqueId('dept')
  return {
    id,
    name:           `Dept-${id}`,
    employee_count: 5,
    ...overrides,
  }
}

export interface MockAttendanceRecord {
  id: string
  employee_id: string
  check_in_time: string
  check_out_time: string | null
  status: 'present' | 'absent' | 'half_day'
}

export function makeAttendanceRecord(
  overrides: Partial<MockAttendanceRecord> = {},
): MockAttendanceRecord {
  const id = uniqueId('att')
  return {
    id,
    employee_id:    uniqueId('emp'),
    check_in_time:  new Date().toISOString(),
    check_out_time: null,
    status:         'present',
    ...overrides,
  }
}
