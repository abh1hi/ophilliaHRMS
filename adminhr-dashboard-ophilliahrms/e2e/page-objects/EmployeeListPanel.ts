import type { Page, Locator } from '@playwright/test'

export class EmployeeListPanel {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/dashboard?tab=employees')
  }

  async search(query: string) {
    await this.page.getByPlaceholder(/search/i).fill(query)
    // Wait for debounce
    await this.page.waitForTimeout(300)
  }

  async clickNewEmployee() {
    await this.page.getByRole('button', { name: /new employee/i }).click()
  }

  getRows(): Locator {
    return this.page.locator('table tbody tr')
  }

  getEmptyState(): Locator {
    return this.page.locator(
      '[data-testid="empty-state"], .empty-state, :text("No employees"), :text("No records")',
    )
  }

  async clickDeleteForRow(nameOrEmail: string) {
    const row = this.page.locator('tr', { hasText: nameOrEmail })
    await row.getByRole('button', { name: /delete/i }).click()
  }

  async clickEditForRow(nameOrEmail: string) {
    const row = this.page.locator('tr', { hasText: nameOrEmail })
    await row.getByRole('button', { name: /edit/i }).click()
  }

  async confirmDelete() {
    // ConfirmDialog has a confirm/delete button — pick the last one to avoid accidental cancel
    await this.page
      .getByRole('button', { name: /confirm|delete/i })
      .last()
      .click()
  }

  async cancelDelete() {
    await this.page.getByRole('button', { name: /cancel/i }).click()
  }
}
