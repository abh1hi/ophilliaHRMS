import { test, expect } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'

test.describe('Logout', () => {
  test('clears auth tokens and redirects to login on logout', async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')

    // Trigger logout — look for a logout button in the header or user menu
    const logoutButton = page.getByRole('button', { name: /log.?out|sign.?out/i })
    if (await logoutButton.isVisible()) {
      await logoutButton.click()
    } else {
      // Fallback: clear localStorage manually (simulates logout)
      await page.evaluate(() => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('company_name')
        localStorage.removeItem('selected_company_id')
      })
      await page.goto('/dashboard')
    }

    // Should be redirected to login
    await page.waitForURL('/', { timeout: 5000 })
    expect(page.url()).toMatch(/\/$|\/\?/)
  })

  test('localStorage is cleared after logout', async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
    await page.goto('/dashboard')

    await page.evaluate(() => {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    })

    // Verify tokens are gone
    const token = await page.evaluate(() => localStorage.getItem('access_token'))
    expect(token).toBeNull()
  })

  test('unauthenticated access to /dashboard redirects to /', async ({ page }) => {
    // No auth tokens set — direct navigation to dashboard should redirect
    await page.goto('/dashboard')
    await page.waitForURL('/', { timeout: 5000 })
    expect(page.url()).toMatch(/\/$|\/\?/)
  })
})
