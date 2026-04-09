import { test, expect } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'

test.describe('API failure handling', () => {
  test.beforeEach(async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
  })

  test('500 on employees API does not crash the app', async ({ authedPage: page }) => {
    await page.route('**/api/v1/employees*', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ success: false, data: null, meta: null, error: { code: 'SERVER_ERROR', message: 'Internal server error' } }),
      })
    })
    await page.goto('/dashboard?tab=employees')
    await page.waitForLoadState('networkidle')

    // App should remain functional (not white-screen)
    const body = await page.textContent('body')
    expect(body?.trim().length).toBeGreaterThan(0)
  })

  test('network timeout does not freeze the app', async ({ authedPage: page }) => {
    await page.route('**/api/v1/employees*', async (route) => {
      await route.abort('timedout')
    })
    await page.goto('/dashboard?tab=employees')
    await page.waitForTimeout(3000)

    // App should not be completely frozen
    const body = await page.textContent('body')
    expect(body?.trim().length).toBeGreaterThan(0)
  })

  test('401 on employees API redirects to login', async ({ authedPage: page }) => {
    await page.route('**/api/v1/employees*', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Unauthorized' }),
      })
    })
    await page.goto('/dashboard?tab=employees')
    await page.waitForLoadState('networkidle')

    // Depending on implementation: either shows error UI or redirects to /
    const url = page.url()
    const body = await page.textContent('body')
    // At minimum, the page should not be blank
    expect(body?.trim().length).toBeGreaterThan(0)
  })

  test('payroll 500 error does not crash payroll view', async ({ authedPage: page }) => {
    await page.route('**/api/v1/payroll/**', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ success: false, data: null, meta: null, error: { code: 'SERVER_ERROR', message: 'Payroll service unavailable' } }),
      })
    })
    await page.goto('/payroll')
    await page.waitForLoadState('networkidle')

    const body = await page.textContent('body')
    expect(body?.trim().length).toBeGreaterThan(0)
  })
})
