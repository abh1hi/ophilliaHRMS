import { test, expect, setMockedAuth } from '../../fixtures'
import { mockEmployeeProfile, mockCompanies } from '../../support/api-mocks/auth.mocks'

test.describe('Role-based routing', () => {
  test('admin with valid token reaches /dashboard', async ({ page }) => {
    await setMockedAuth(page, 'admin')
    await mockEmployeeProfile(page)
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/dashboard')
  })

  test('hr with valid token reaches /dashboard', async ({ page }) => {
    await setMockedAuth(page, 'hr')
    await mockEmployeeProfile(page)
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/dashboard')
  })

  test('super_admin is redirected to /select-company or dashboard', async ({ page }) => {
    await setMockedAuth(page, 'superAdmin')
    await mockCompanies(page)
    await page.goto('/dashboard')
    // Super admin may land on select-company or dashboard depending on router logic
    await page.waitForURL(/\/(select-company|dashboard)/, { timeout: 5000 })
    expect(page.url()).toMatch(/select-company|dashboard/)
  })

  test('employee with valid token reaches /dashboard', async ({ page }) => {
    await setMockedAuth(page, 'employee')
    await mockEmployeeProfile(page)
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/dashboard')
  })

  test('unauthenticated user is redirected to / from /dashboard', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForURL('/', { timeout: 5000 })
    expect(page.url()).toMatch(/\/$|\/\?/)
  })

  test('unauthenticated user is redirected to / from /payroll', async ({ page }) => {
    await page.goto('/payroll')
    await page.waitForURL('/', { timeout: 5000 })
    expect(page.url()).toMatch(/\/$|\/\?/)
  })

  test('employee cannot access /payroll (role restricted)', async ({ page }) => {
    await setMockedAuth(page, 'employee')
    await page.goto('/payroll')
    // Should redirect away — either to dashboard or login
    await page.waitForURL(/\/(dashboard|\?)/, { timeout: 5000 })
    expect(page.url()).not.toContain('/payroll')
  })
})
