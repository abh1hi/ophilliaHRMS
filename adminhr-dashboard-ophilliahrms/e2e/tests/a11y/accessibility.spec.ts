import { test, expect } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'
import { mockEmployeeList } from '../../support/api-mocks/employee.mocks'
import { checkA11y } from '../../support/helpers/a11y'

test.describe('Accessibility (WCAG 2.0 A + AA)', () => {
  test('login page has no violations', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await checkA11y(page, 'Login page')
  })

  test('dashboard has no violations', async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
    await page.route('**/api/v1/**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, data: [], meta: null, error: null }) })
      } else {
        await route.fallthrough()
      }
    })
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    await checkA11y(page, 'Dashboard')
  })

  test('employee list has no violations', async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
    await mockEmployeeList(page)
    await page.goto('/dashboard?tab=employees')
    await page.waitForLoadState('networkidle')
    await checkA11y(page, 'Employee list')
  })
})
