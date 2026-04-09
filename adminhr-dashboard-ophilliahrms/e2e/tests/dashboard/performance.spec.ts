import { test, expect } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'
import { measureNavigation } from '../../support/helpers/perf'

test.describe('Dashboard performance', () => {
  test.beforeEach(async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
    await page.route('**/api/v1/**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, data: [], meta: null, error: null }),
        })
      } else {
        await route.fallthrough()
      }
    })
  })

  test('dashboard loads within 2000ms', async ({ authedPage: page }) => {
    const elapsed = await measureNavigation(page, '/dashboard', 2000)
    console.log(`Dashboard load time: ${elapsed}ms`)
  })

  test('switching tabs is fast (< 1500ms)', async ({ authedPage: page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')

    const start = Date.now()
    await page.goto('/dashboard?tab=employees')
    await page.waitForLoadState('networkidle')
    const elapsed = Date.now() - start

    expect(elapsed, `Tab switch took ${elapsed}ms (max 1500ms)`).toBeLessThan(1500)
  })
})
