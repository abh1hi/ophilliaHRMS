import { test, expect } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'
import { mockAttendanceList } from '../../support/api-mocks/attendance.mocks'
import { AttendanceCheckinPanel } from '../../page-objects/AttendanceCheckinPanel'
import { makeAttendanceRecord } from '../../fixtures/seed.factory'

test.describe('Attendance check-in panel', () => {
  test.beforeEach(async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
  })

  test('renders attendance records from API', async ({ authedPage: page }) => {
    const records = [
      makeAttendanceRecord({ status: 'present' }),
      makeAttendanceRecord({ status: 'absent' }),
    ]
    await mockAttendanceList(page, records)

    const panel = new AttendanceCheckinPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    const rows = panel.getRows()
    const count = await rows.count()
    expect(count).toBeGreaterThan(0)
  })

  test('attendance panel renders without crashing', async ({ authedPage: page }) => {
    await mockAttendanceList(page)

    const panel = new AttendanceCheckinPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    // Should not show unhandled errors
    const uncaught = page.locator(':text("Uncaught"), :text("TypeError"), :text("ReferenceError")')
    await expect(uncaught).not.toBeVisible()
  })

  test('empty attendance list does not crash', async ({ authedPage: page }) => {
    await mockAttendanceList(page, [])

    const panel = new AttendanceCheckinPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    const body = await page.textContent('body')
    expect(body?.trim().length).toBeGreaterThan(0)
  })
})
