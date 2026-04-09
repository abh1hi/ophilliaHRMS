import { test, expect, setMockedAuth } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'

test.describe('Role permissions', () => {
  test('admin can access /payroll', async ({ page }) => {
    await setMockedAuth(page, 'admin')
    await mockEmployeeProfile(page)
    await page.route('**/api/v1/payroll/**', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, data: { runs: [], total: 0 }, meta: null, error: null }) })
    })
    await page.goto('/payroll')
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/payroll')
  })

  test('hr can access /payroll', async ({ page }) => {
    await setMockedAuth(page, 'hr')
    await mockEmployeeProfile(page)
    await page.route('**/api/v1/payroll/**', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, data: { runs: [], total: 0 }, meta: null, error: null }) })
    })
    await page.goto('/payroll')
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/payroll')
  })

  test('employee cannot access /payroll', async ({ page }) => {
    await setMockedAuth(page, 'employee')
    await page.goto('/payroll')
    // Should redirect away from /payroll
    await page.waitForURL(/\/(dashboard|\?|$)/, { timeout: 5000 })
    expect(page.url()).not.toContain('/payroll')
  })

  test('employee can access /dashboard', async ({ page }) => {
    await setMockedAuth(page, 'employee')
    await mockEmployeeProfile(page)
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/dashboard')
  })

  test('employee can access /profile', async ({ page }) => {
    await setMockedAuth(page, 'employee')
    await mockEmployeeProfile(page)
    await page.goto('/profile')
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/profile')
  })
})
