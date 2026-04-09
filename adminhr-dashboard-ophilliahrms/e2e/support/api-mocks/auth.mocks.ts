import type { Page } from '@playwright/test'

/**
 * Mock GET /api/v1/employees/me — called by DashboardView on mount.
 * Uses enveloped shape: { success, data, meta, error }
 */
export async function mockEmployeeProfile(page: Page) {
  await page.route('**/api/v1/employees/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          id: 'emp-profile-1',
          first_name: 'Alice',
          last_name: 'Admin',
          email: 'admin@acme.com',
          department:  { id: 'dept-1', name: 'Engineering' },
          designation: { id: 'des-1',  name: 'Senior Engineer' },
          employment_status: 'active',
          employee_code: 'EMP001',
        },
        meta:  null,
        error: null,
      }),
    })
  })
}

/**
 * Mock POST /api/v1/auth/login — returns access + refresh tokens.
 * The router guard will decode the payload of access_token via atob().
 */
export async function mockLoginSuccess(
  page: Page,
  role: 'admin' | 'hr' | 'super_admin' | 'employee' = 'admin',
) {
  // Build a minimal fake JWT payload the router guard will accept
  const payload = btoa(
    JSON.stringify({
      sub: `user-${role}-1`,
      role,
      email: `${role}@test.com`,
      company_id: 'co-1',
      exp: Math.floor(Date.now() / 1000) + 3600,
    }),
  )
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')

  const fakeJwt = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${payload}.fakesig`

  await page.route('**/api/v1/auth/login', async (route) => {
    if (route.request().method() !== 'POST') {
      await route.fallthrough()
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token:  fakeJwt,
        refresh_token: 'mock-refresh-token',
        token_type:    'bearer',
      }),
    })
  })
}

/**
 * Mock POST /api/v1/auth/login — returns 401 Unauthorized.
 */
export async function mockLoginFailure(page: Page) {
  await page.route('**/api/v1/auth/login', async (route) => {
    if (route.request().method() !== 'POST') {
      await route.fallthrough()
      return
    }
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: 'Invalid credentials',
      }),
    })
  })
}

/**
 * Mock GET /api/v1/auth/companies — for CompanySelectionView (super_admin).
 */
export async function mockCompanies(page: Page) {
  await page.route('**/api/v1/auth/companies', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          companies: [
            { id: 'co-1', name: 'Acme Corp',  employee_count: 42 },
            { id: 'co-2', name: 'Beta LLC',   employee_count: 15 },
          ],
        },
        meta:  null,
        error: null,
      }),
    })
  })
}
