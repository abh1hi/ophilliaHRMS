import type { ShiftAssignment } from '../services/shift-assignment.service'

export function getShiftAssignmentWarnings(
  assignments: ShiftAssignment[],
  shiftTypeIds: Set<string>,
  locationIds: Set<string>,
): string[] {
  const active = assignments.filter(item => Number(item.is_active) === 1)
  const warnings: string[] = []
  const byEmployee = new Map<string, ShiftAssignment[]>()

  for (const item of active) {
    if (!byEmployee.has(item.employee_id)) byEmployee.set(item.employee_id, [])
    byEmployee.get(item.employee_id)!.push(item)

    if (item.shift_type_id && !shiftTypeIds.has(item.shift_type_id)) {
      warnings.push(`${shortEmployeeId(item.employee_id)} has a missing shift type reference`)
    }
    if (item.shift_location_id && !locationIds.has(item.shift_location_id)) {
      warnings.push(`${shortEmployeeId(item.employee_id)} has a missing location reference`)
    }
    if (!item.shift_type_id || !item.shift_location_id) {
      warnings.push(`${shortEmployeeId(item.employee_id)} is missing a shift type or location`)
    }
  }

  for (const [employeeId, rows] of byEmployee.entries()) {
    const sorted = [...rows].sort((a, b) => a.effective_from.localeCompare(b.effective_from))
    for (let i = 0; i < sorted.length; i++) {
      for (let j = i + 1; j < sorted.length; j++) {
        if (dateRangesOverlap(sorted[i], sorted[j])) {
          warnings.push(`${shortEmployeeId(employeeId)} has overlapping shift assignments`)
        }
      }
    }
  }

  return [...new Set(warnings)]
}

function dateRangesOverlap(a: ShiftAssignment, b: ShiftAssignment) {
  const aEnd = a.effective_to || '9999-12-31'
  const bEnd = b.effective_to || '9999-12-31'
  return a.effective_from <= bEnd && b.effective_from <= aEnd
}

function shortEmployeeId(id?: string) {
  return id ? `${id.slice(0, 8)}...` : 'Employee'
}
