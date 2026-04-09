import type { Page, Locator } from '@playwright/test'

export class LoginPage {
  readonly emailInput: Locator
  readonly passwordInput: Locator
  readonly submitButton: Locator

  constructor(private page: Page) {
    this.emailInput    = page.getByLabel('Email')
    this.passwordInput = page.getByLabel('Password')
    this.submitButton  = page.getByRole('button', { name: /sign in/i })
  }

  async goto() {
    await this.page.goto('/')
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    await this.submitButton.click()
  }

  getErrorMessage(): Locator {
    return this.page.locator('[role="alert"], .error-message, [data-testid="error"]')
  }

  getLoadingIndicator(): Locator {
    return this.page.locator('[data-testid="loading"], .loading-spinner')
  }
}
