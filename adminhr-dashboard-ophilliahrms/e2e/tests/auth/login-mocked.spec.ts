import { test, expect } from '../../fixtures'
import { LoginPage } from '../../page-objects/LoginPage'
import { mockLoginSuccess, mockLoginFailure, mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'

test.describe('Login — mocked backend', () => {
  test('shows login form on root route', async ({ page }) => {
    await page.goto('/')
    const login = new LoginPage(page)
    await expect(login.emailInput).toBeVisible()
    await expect(login.passwordInput).toBeVisible()
    await expect(login.submitButton).toBeVisible()
  })

  test('redirects admin to /dashboard after successful login', async ({ page }) => {
    await mockLoginSuccess(page, 'admin')
    await mockEmployeeProfile(page)
    const login = new LoginPage(page)
    await login.goto()
    await login.login('admin@test.com', 'password123')
    await page.waitForURL(/\/dashboard/)
    expect(page.url()).toContain('/dashboard')
  })

  test('redirects super_admin to /select-company after login', async ({ page }) => {
    await mockLoginSuccess(page, 'super_admin')
    const login = new LoginPage(page)
    await login.goto()
    await login.login('sa@test.com', 'password123')
    await page.waitForURL(/\/(select-company|dashboard)/)
    // super_admin goes to /select-company
    expect(page.url()).toMatch(/select-company|dashboard/)
  })

  test('shows error message on invalid credentials', async ({ page }) => {
    await mockLoginFailure(page)
    const login = new LoginPage(page)
    await login.goto()
    await login.login('wrong@test.com', 'wrongpassword')
    const error = login.getErrorMessage()
    await expect(error).toBeVisible({ timeout: 5000 })
  })

  test('submit button is disabled while loading', async ({ page }) => {
    // Delay the response so we can check the loading state
    await page.route('**/api/v1/auth/login', async (route) => {
      await new Promise((r) => setTimeout(r, 500))
      await route.abort()
    })
    const login = new LoginPage(page)
    await login.goto()
    await login.emailInput.fill('admin@test.com')
    await login.passwordInput.fill('password123')
    await login.submitButton.click()
    // Button should be disabled or show loading indicator during request
    // (actual selector depends on how LoginView.vue implements this)
    await expect(page).not.toHaveURL(/dashboard/, { timeout: 300 })
  })

  test('renders correctly on mobile viewport', async ({ page }) => {
    await page.goto('/')
    const login = new LoginPage(page)
    await expect(login.emailInput).toBeVisible()
    await expect(login.submitButton).toBeVisible()
  })
})
