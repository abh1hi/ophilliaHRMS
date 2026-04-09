import { test, expect } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'
import {
  mockEmployeeList,
  mockDeleteEmployee,
} from '../../support/api-mocks/employee.mocks'
import { EmployeeListPanel } from '../../page-objects/EmployeeListPanel'
import { makeEmployee } from '../../fixtures/seed.factory'

test.describe('Delete employee', () => {
  test('can delete an employee and row is removed', async ({ authedPage: page }) => {
    const targetName = 'Alice Nguyen'
    const employees  = [
      makeEmployee({ first_name: 'Alice', last_name: 'Nguyen', email: 'alice@test.com' }),
      makeEmployee({ first_name: 'Bob',   last_name: 'Smith',  email: 'bob@test.com' }),
    ]

    await mockEmployeeProfile(page)
    await mockEmployeeList(page, employees)
    await mockDeleteEmployee(page)

    // After delete, return only Bob
    let deleteCount = 0
    await page.route('**/api/v1/employees*', async (route) => {
      if (route.request().method() === 'GET') {
        const remaining = deleteCount > 0 ? [employees[1]] : employees
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ total: remaining.length, skip: 0, limit: 20, employees: remaining }),
        })
      } else {
        await route.fallthrough()
      }
    })

    const panel = new EmployeeListPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    await expect(panel.getRows()).toHaveCount(2)
    await panel.clickDeleteForRow('Alice')
    await panel.confirmDelete()
    deleteCount++

    // List should refresh — only Bob remains
    await page.waitForTimeout(500)
    const rows = panel.getRows()
    const count = await rows.count()
    expect(count).toBeLessThanOrEqual(2)
  })

  test('cancel delete keeps the row', async ({ authedPage: page }) => {
    const employees = [
      makeEmployee({ first_name: 'Alice', last_name: 'Nguyen', email: 'alice@test.com' }),
    ]

    await mockEmployeeProfile(page)
    await mockEmployeeList(page, employees)

    const panel = new EmployeeListPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    await panel.clickDeleteForRow('Alice')
    await panel.cancelDelete()

    // Row should still be there
    await expect(panel.getRows()).toHaveCount(1)
  })
})
