import { test, expect } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'

// All tab names that DashboardView supports via ?tab= query param
const TABS = [
  'dashboard',
  'employees',
  'payroll',
  'hr-setup',
  'attendance',
  'shifts',
  'leaves',
  'workspace',
]

test.describe('Dashboard navigation', () => {
  test.beforeEach(async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
    // Stub all API calls so tabs don't crash waiting for data
    await page.route('**/api/v1/**', async (route) => {
      const method = route.request().method()
      if (method === 'GET') {
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

  test('navigates to default dashboard tab', async ({ authedPage: page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/dashboard')
  })

  for (const tab of TABS) {
    test(`renders ${tab} tab without crashing`, async ({ authedPage: page }) => {
      await page.goto(`/dashboard?tab=${tab}`)
      await page.waitForLoadState('networkidle')
      expect(page.url()).toContain(`tab=${tab}`)
      // Page should not show an unhandled error
      const errorText = page.locator(':text("TypeError"), :text("ReferenceError"), :text("Uncaught")')
      await expect(errorText).not.toBeVisible()
    })
  }

  test('sidebar is visible on dashboard', async ({ authedPage: page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    // AppSidebar should be in the DOM
    const sidebar = page.locator('nav, aside, [class*="sidebar"], [class*="Sidebar"]').first()
    await expect(sidebar).toBeVisible()
  })

  test('header is visible on dashboard', async ({ authedPage: page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    const header = page.locator('header, [class*="header"], [class*="Header"]').first()
    await expect(header).toBeVisible()
  })
})
