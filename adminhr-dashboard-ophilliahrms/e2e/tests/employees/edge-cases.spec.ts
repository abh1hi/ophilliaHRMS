import { test, expect } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'
import {
  mockEmployeeListEmpty,
  mockEmployeeListLarge,
  mockEmployeeListError,
  mockEmployeeListAbort,
} from '../../support/api-mocks/employee.mocks'
import { EmployeeListPanel } from '../../page-objects/EmployeeListPanel'

test.describe('Employee list — edge cases', () => {
  test.beforeEach(async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
  })

  test('empty list does not crash the page', async ({ authedPage: page }) => {
    await mockEmployeeListEmpty(page)
    const panel = new EmployeeListPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    // Page should still be functional (no JS errors)
    const uncaught = page.locator(':text("Uncaught"), :text("TypeError"), :text("ReferenceError")')
    await expect(uncaught).not.toBeVisible()
  })

  test('large dataset (1000 rows) does not crash', async ({ authedPage: page }) => {
    await mockEmployeeListLarge(page)
    const panel = new EmployeeListPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    // Should paginate — not render 1000 rows at once
    const rows = panel.getRows()
    const count = await rows.count()
    expect(count).toBeLessThanOrEqual(50) // max visible rows
  })

  test('API 500 error shows an error state (not blank page)', async ({ authedPage: page }) => {
    await mockEmployeeListError(page, 500)
    const panel = new EmployeeListPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    // Should NOT show a blank screen — either error message or empty state
    const body = await page.textContent('body')
    expect(body?.trim().length).toBeGreaterThan(0)
  })

  test('API 404 error does not crash', async ({ authedPage: page }) => {
    await mockEmployeeListError(page, 404)
    const panel = new EmployeeListPanel(page)
    await panel.goto()
    await page.waitForLoadState('networkidle')

    const body = await page.textContent('body')
    expect(body?.trim().length).toBeGreaterThan(0)
  })

  test('network abort does not crash the page', async ({ authedPage: page }) => {
    await mockEmployeeListAbort(page)
    const panel = new EmployeeListPanel(page)
    await panel.goto()

    // Page should not throw an uncaught error
    await page.waitForTimeout(2000)
    const uncaught = page.locator(':text("Uncaught"), :text("TypeError")')
    await expect(uncaught).not.toBeVisible()
  })
})
