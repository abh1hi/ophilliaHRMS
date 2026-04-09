/**
 * Real-backend login tests.
 * Only runs when RUN_INTEGRATION=1 and E2E_REAL_AUTH=1 are set.
 * Requires a running backend with test credentials in environment variables.
 *
 * These tests are included in the `integration` Playwright project.
 */
import { test, expect } from '@playwright/test'
import { LoginPage } from '../../page-objects/LoginPage'
import { validateEnvelope } from '../../support/contracts/employee.contract'

const SKIP = !process.env.RUN_INTEGRATION || !process.env.E2E_REAL_AUTH

test.describe('Login — real backend', () => {
  test.skip(SKIP, 'Set RUN_INTEGRATION=1 and E2E_REAL_AUTH=1 to run real-backend tests')

  test('admin can login and reaches /dashboard', async ({ page }) => {
    const login = new LoginPage(page)
    await login.goto()
    await login.login(
      process.env.E2E_ADMIN_EMAIL!,
      process.env.E2E_ADMIN_PASS!,
    )
    await page.waitForURL(/\/dashboard/, { timeout: 10_000 })
    expect(page.url()).toContain('/dashboard')
  })

  test('hr can login and reaches /dashboard', async ({ page }) => {
    const login = new LoginPage(page)
    await login.goto()
    await login.login(
      process.env.E2E_HR_EMAIL!,
      process.env.E2E_HR_PASS!,
    )
    await page.waitForURL(/\/dashboard/, { timeout: 10_000 })
    expect(page.url()).toContain('/dashboard')
  })

  test('super_admin can login and reaches /select-company', async ({ page }) => {
    const login = new LoginPage(page)
    await login.goto()
    await login.login(
      process.env.E2E_SUPER_ADMIN_EMAIL!,
      process.env.E2E_SUPER_ADMIN_PASS!,
    )
    await page.waitForURL(/\/(select-company|dashboard)/, { timeout: 10_000 })
    expect(page.url()).toMatch(/select-company|dashboard/)
  })

  test('employee list API returns expected contract shape after real login', async ({
    page,
    request,
  }) => {
    // Login via the form to get real tokens in localStorage
    const login = new LoginPage(page)
    await login.goto()
    await login.login(
      process.env.E2E_ADMIN_EMAIL!,
      process.env.E2E_ADMIN_PASS!,
    )
    await page.waitForURL(/\/dashboard/, { timeout: 10_000 })

    // Extract the real access token and hit the employees endpoint directly
    const token = await page.evaluate(() => localStorage.getItem('access_token'))
    const response = await request.get(
      `${process.env.VITE_API_GATEWAY_URL ?? 'http://localhost'}/api/v1/employees`,
      { headers: { Authorization: `Bearer ${token}` } },
    )
    expect(response.status()).toBe(200)
    const body = await response.json()
    // Validate contract shape
    expect(body).toMatchObject({ total: expect.any(Number) })
  })
})
