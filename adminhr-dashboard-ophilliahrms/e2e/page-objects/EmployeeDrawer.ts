import type { Page, Locator } from '@playwright/test'

export class EmployeeDrawer {
  constructor(private page: Page) {}

  getDrawer(): Locator {
    return this.page.locator('[data-testid="employee-drawer"], [role="dialog"], .slide-drawer').first()
  }

  async waitForOpen() {
    await this.getDrawer().waitFor({ state: 'visible' })
  }

  async waitForClose() {
    await this.getDrawer().waitFor({ state: 'hidden' })
  }

  async fillFirstName(value: string) {
    await this.page.getByLabel(/first name/i).fill(value)
  }

  async fillLastName(value: string) {
    await this.page.getByLabel(/last name/i).fill(value)
  }

  async fillEmail(value: string) {
    await this.page.getByLabel(/email/i).fill(value)
  }

  async fillEmployeeCode(value: string) {
    await this.page.getByLabel(/employee code/i).fill(value)
  }

  async submit() {
    await this.page.getByRole('button', { name: /save|submit|create/i }).click()
  }

  async close() {
    await this.page.getByRole('button', { name: /close|cancel/i }).first().click()
  }

  getSuccessToast(): Locator {
    return this.page.locator(
      '[data-testid="toast"], .toast, [role="status"], :text("created"), :text("saved")',
    )
  }
}
