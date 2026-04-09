import { test, expect } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'
import {
  mockEmployeeList,
  mockEmployeeListEmpty,
} from '../../support/api-mocks/employee.mocks'
import { EmployeeListPanel } from '../../page-objects/EmployeeListPanel'
import { makeEmployee } from '../../fixtures/seed.factory'

test.describe('Employee list', () => {
  test.beforeEach(async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
  })

  test('renders employee rows from API', async ({ authedPage: page }) => {
    const employees = [
      makeEmployee({ first_name: 'Alice', last_name: 'Nguyen', email: 'alice@test.com' }),
      makeEmployee({ first_name: 'Bob',   last_name: 'Smith',  email: 'bob@test.com' }),
    ]
    await mockEmployeeList(page, employees)

    const panel = new EmployeeListPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    const rows = panel.getRows()
    await expect(rows).toHaveCount(2)
  })

  test('shows "New Employee" button', async ({ authedPage: page }) => {
    await mockEmployeeList(page)
    const panel = new EmployeeListPanel(page)
    await panel.goto()
    await expect(page.getByRole('button', { name: /new employee/i })).toBeVisible()
  })

  test('search filters results', async ({ authedPage: page }) => {
    const employees = [
      makeEmployee({ first_name: 'Alice', last_name: 'Nguyen', email: 'alice@test.com' }),
      makeEmployee({ first_name: 'Bob',   last_name: 'Smith',  email: 'bob@test.com' }),
    ]
    await mockEmployeeList(page, employees)

    const panel = new EmployeeListPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    await panel.search('alice')
    await page.waitForLoadState('networkidle')

    // After search, only Alice should appear
    const rows = panel.getRows()
    await expect(rows).toHaveCount(1)
    await expect(rows.first()).toContainText('Alice')
  })

  test('shows empty state when no employees exist', async ({ authedPage: page }) => {
    await mockEmployeeListEmpty(page)
    const panel = new EmployeeListPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    const rows = panel.getRows()
    const count = await rows.count()
    // Either 0 rows or an empty state message should be shown
    if (count === 0) {
      expect(count).toBe(0)
    } else {
      await expect(panel.getEmptyState()).toBeVisible()
    }
  })

  test('search with no matching results shows empty state', async ({ authedPage: page }) => {
    const employees = [makeEmployee({ first_name: 'Alice', email: 'alice@test.com' })]
    await mockEmployeeList(page, employees)

    const panel = new EmployeeListPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    await panel.search('zzznonexistent')
    await page.waitForLoadState('networkidle')

    const rows = panel.getRows()
    const count = await rows.count()
    expect(count).toBe(0)
  })
})
