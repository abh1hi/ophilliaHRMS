import type { Page, Locator } from '@playwright/test'

export class DashboardPage {
  constructor(private page: Page) {}

  async goto(tab?: string) {
    await this.page.goto(tab ? `/dashboard?tab=${tab}` : '/dashboard')
  }

  async switchTab(tab: string) {
    await this.page.goto(`/dashboard?tab=${tab}`)
  }

  getSidebar(): Locator {
    return this.page.locator('nav, aside, [role="navigation"]').first()
  }

  getMainContent(): Locator {
    return this.page.locator('main, [data-testid="tab-content"]').first()
  }

  getTabPanel(): Locator {
    // DashboardView switches content via currentTab — look for any visible panel
    return this.page.locator('[class*="panel"], [class*="Panel"], main > div').first()
  }

  async waitForTab() {
    await this.page.waitForLoadState('networkidle')
  }
}
