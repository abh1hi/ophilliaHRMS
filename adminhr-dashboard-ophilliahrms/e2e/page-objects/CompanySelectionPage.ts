import type { Page, Locator } from '@playwright/test'

export class CompanySelectionPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/select-company')
  }

  getCompanyCards(): Locator {
    return this.page.locator('[data-testid="company-card"], .company-card, [class*="company"]')
  }

  async selectCompany(name: string) {
    await this.page.locator(':text("' + name + '")').click()
  }

  getHeading(): Locator {
    return this.page.getByRole('heading', { name: /select company|choose company/i })
  }
}
