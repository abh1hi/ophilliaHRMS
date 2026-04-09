import { test, expect } from '@playwright/test'
import { buildMockJwt } from '../../fixtures/jwt.factory'

test.describe('Token expiry', () => {
  test('expired token is rejected and redirects to login', async ({ page }) => {
    const expiredToken = buildMockJwt({
      sub:        'u-exp-1',
      role:       'admin',
      email:      'exp@test.com',
      company_id: 'co-1',
      exp:        Math.floor(Date.now() / 1000) - 60, // expired 1 min ago
    })

    // Write the expired token to localStorage
    await page.goto('/')
    await page.evaluate(({ token }) => {
      localStorage.setItem('access_token', token)
      localStorage.setItem('refresh_token', 'mock-refresh')
      localStorage.setItem('company_name', 'Acme Corp')
      localStorage.setItem('selected_company_id', 'co-1')
    }, { token: expiredToken })

    // Try to navigate to a protected route
    await page.goto('/dashboard')

    // Router guard should detect expiry and redirect to /
    await page.waitForURL('/', { timeout: 5000 })
    expect(page.url()).toMatch(/\/$|\/\?/)
  })

  test('token expiring in the future grants access', async ({ page }) => {
    const validToken = buildMockJwt({
      sub:        'u-valid-1',
      role:       'admin',
      email:      'valid@test.com',
      company_id: 'co-1',
      exp:        Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
    })

    await page.goto('/')
    await page.evaluate(({ token }) => {
      localStorage.setItem('access_token', token)
      localStorage.setItem('refresh_token', 'mock-refresh')
      localStorage.setItem('company_name', 'Acme Corp')
      localStorage.setItem('selected_company_id', 'co-1')
    }, { token: validToken })

    // Mock any profile call so the dashboard renders
    await page.route('**/api/v1/employees/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: { id: 'u-valid-1', first_name: 'Valid', last_name: 'User', email: 'valid@test.com', employment_status: 'active' }, meta: null, error: null }),
      })
    })

    await page.goto('/dashboard')
    // Should stay on dashboard — NOT redirect to login
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/dashboard')
  })
})
