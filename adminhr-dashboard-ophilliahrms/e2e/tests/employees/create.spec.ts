import { test, expect } from '../../fixtures'
import { mockEmployeeProfile } from '../../support/api-mocks/auth.mocks'
import {
  mockEmployeeList,
  mockCreateEmployee,
} from '../../support/api-mocks/employee.mocks'
import { EmployeeListPanel } from '../../page-objects/EmployeeListPanel'
import { EmployeeDrawer } from '../../page-objects/EmployeeDrawer'
import { uniqueId } from '../../fixtures/seed.factory'

test.describe('Create employee', () => {
  test.beforeEach(async ({ authedPage: page }) => {
    await mockEmployeeProfile(page)
    await mockEmployeeList(page)
    await mockCreateEmployee(page)
  })

  test('opens employee drawer on "New Employee" click', async ({ authedPage: page }) => {
    const panel  = new EmployeeListPanel(page)
    const drawer = new EmployeeDrawer(page)

    await panel.goto()
    await page.waitForLoadState('networkidle')
    await panel.clickNewEmployee()

    await drawer.waitForOpen()
    await expect(drawer.getDrawer()).toBeVisible()
  })

  test('drawer closes on cancel', async ({ authedPage: page }) => {
    const panel  = new EmployeeListPanel(page)
    const drawer = new EmployeeDrawer(page)

    await panel.goto()
    await page.waitForLoadState('networkidle')
    await panel.clickNewEmployee()
    await drawer.waitForOpen()
    await drawer.close()

    await drawer.waitForClose()
    await expect(drawer.getDrawer()).not.toBeVisible()
  })

  test('creates employee and shows success feedback', async ({ authedPage: page }) => {
    const panel  = new EmployeeListPanel(page)
    const drawer = new EmployeeDrawer(page)
    const uid    = uniqueId('test')

    await panel.goto()
    await page.waitForLoadState('networkidle')
    await panel.clickNewEmployee()
    await drawer.waitForOpen()

    // Fill required fields
    await drawer.fillFirstName('TestFirst')
    await drawer.fillLastName(`TestLast-${uid}`)
    await drawer.fillEmail(`${uid}@test.com`)

    await drawer.submit()

    // Success toast or drawer close is the indicator
    const success = drawer.getSuccessToast()
    const isClosed = async () => {
      try {
        await drawer.waitForClose()
        return true
      } catch {
        return false
      }
    }

    const successVisible = await success.isVisible().catch(() => false)
    const drawerClosed   = await isClosed()

    expect(successVisible || drawerClosed, 'Expected success toast or drawer to close').toBeTruthy()
  })
})
