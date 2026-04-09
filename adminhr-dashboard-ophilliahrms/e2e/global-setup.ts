import { chromium, type FullConfig } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

async function globalSetup(config: FullConfig) {
  const baseURL = config.projects[0].use.baseURL ?? 'http://localhost:5173'

  // Ensure .auth directory exists
  fs.mkdirSync(path.join(__dirname, '.auth'), { recursive: true })

  // Skip real auth state generation if backend unavailable (local dev without backend)
  if (!process.env.E2E_REAL_AUTH) return

  const browser = await chromium.launch()
  const credentials = [
    {
      role: 'admin',
      email: process.env.E2E_ADMIN_EMAIL!,
      password: process.env.E2E_ADMIN_PASS!,
    },
    {
      role: 'hr',
      email: process.env.E2E_HR_EMAIL!,
      password: process.env.E2E_HR_PASS!,
    },
    {
      role: 'super-admin',
      email: process.env.E2E_SUPER_ADMIN_EMAIL!,
      password: process.env.E2E_SUPER_ADMIN_PASS!,
    },
  ]

  for (const cred of credentials) {
    const page = await browser.newPage()
    await page.goto(`${baseURL}/`)
    await page.getByLabel('Email').fill(cred.email)
    await page.getByLabel('Password').fill(cred.password)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL(/\/(dashboard|select-company)/)
    await page.context().storageState({
      path: path.join(__dirname, `.auth/${cred.role}.json`),
    })
    await page.close()
  }

  await browser.close()
}

export default globalSetup
