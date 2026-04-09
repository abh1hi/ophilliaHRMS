import type { Page, Locator } from '@playwright/test'

export class AttendanceCheckinPanel {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/dashboard?tab=attendance')
  }

  getCheckinButton(): Locator {
    return this.page.getByRole('button', { name: /check.?in|punch.?in/i })
  }

  getCheckoutButton(): Locator {
    return this.page.getByRole('button', { name: /check.?out|punch.?out/i })
  }

  getAttendanceTable(): Locator {
    return this.page.locator('table').first()
  }

  getRows(): Locator {
    return this.page.locator('table tbody tr')
  }

  getStatusBadge(status: string): Locator {
    return this.page.locator(`[class*="badge"], [class*="chip"], [class*="status"]`, {
      hasText: status,
    })
  }
}
