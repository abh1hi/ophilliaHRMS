/**
 * Visual regression tests using Playwright's built-in screenshot comparison.
 *
 * First run: `npx playwright test e2e/tests/visual --update-snapshots` to generate baselines.
 * Subsequent runs compare against those baselines.
 *
 * Baseline PNGs are stored in e2e/tests/visual/__snapshots__/ and should be committed.
 */
import { test, expect } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'
import { mockEmployeeList } from '../../support/api-mocks/employee.mocks'
import { makeEmployee } from '../../fixtures/seed.factory'

// Use deterministic data so screenshots are stable
const STABLE_EMPLOYEES = [
  makeEmployee({ id: 'emp-a', first_name: 'Alice', last_name: 'Nguyen', email: 'alice@acme.com', employment_status: 'active' }),
  makeEmployee({ id: 'emp-b', first_name: 'Bob',   last_name: 'Smith',  email: 'bob@acme.com',  employment_status: 'active' }),
]

test.describe('Visual regression', () => {
  test('login page', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveScreenshot('login.png', { maxDiffPixels: 100 })
  })

  test('dashboard default view', async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
    // Stub all GET requests to avoid loading spinner states
    await page.route('**/api/v1/**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, data: [], meta: null, error: null }) })
      } else {
        await route.fallthrough()
      }
    })
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveScreenshot('dashboard.png', { maxDiffPixels: 100 })
  })

  test('employee list view', async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
    await mockEmployeeList(page, STABLE_EMPLOYEES)
    await page.goto('/dashboard?tab=employees')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveScreenshot('employee-list.png', { maxDiffPixels: 100 })
  })
})
