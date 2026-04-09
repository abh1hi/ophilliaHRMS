import type { Page } from '@playwright/test'
import { makeEmployee, type MockEmployee } from '../../fixtures/seed.factory'

/**
 * Mock GET /api/v1/employees — raw shape (apiFetchAuth).
 * Supports search query param filtering.
 */
export async function mockEmployeeList(page: Page, employees?: MockEmployee[]) {
  const data = employees ?? [makeEmployee(), makeEmployee()]

  await page.route('**/api/v1/employees*', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.fallthrough()
      return
    }
    const url    = new URL(route.request().url())
    const search = url.searchParams.get('search')?.toLowerCase() ?? ''
    const filtered = search
      ? data.filter(
          (e) =>
            e.first_name.toLowerCase().includes(search) ||
            e.last_name.toLowerCase().includes(search) ||
            e.email.toLowerCase().includes(search),
        )
      : data

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total:     filtered.length,
        skip:      0,
        limit:     20,
        employees: filtered,
      }),
    })
  })
}

/**
 * Mock GET /api/v1/employees with an empty result.
 */
export async function mockEmployeeListEmpty(page: Page) {
  await mockEmployeeList(page, [])
}

/**
 * Mock GET /api/v1/employees with a large dataset (1000 rows).
 */
export async function mockEmployeeListLarge(page: Page) {
  const data = Array.from({ length: 1000 }, () => makeEmployee())
  await page.route('**/api/v1/employees*', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.fallthrough()
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total: 1000, skip: 0, limit: 20, employees: data.slice(0, 20) }),
    })
  })
}

/**
 * Mock POST /api/v1/employees — enveloped shape (apiFetchData).
 */
export async function mockCreateEmployee(page: Page, responseOverride: Partial<MockEmployee> = {}) {
  await page.route('**/api/v1/employees', async (route) => {
    if (route.request().method() !== 'POST') {
      await route.fallthrough()
      return
    }
    const body = JSON.parse(route.request().postData() ?? '{}')
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data:    { ...makeEmployee(), ...body, ...responseOverride },
        meta:    null,
        error:   null,
      }),
    })
  })
}

/**
 * Mock PUT/PATCH /api/v1/employees/:id — enveloped shape.
 */
export async function mockUpdateEmployee(page: Page) {
  await page.route('**/api/v1/employees/*', async (route) => {
    const method = route.request().method()
    if (method !== 'PUT' && method !== 'PATCH') {
      await route.fallthrough()
      return
    }
    const body = JSON.parse(route.request().postData() ?? '{}')
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: body, meta: null, error: null }),
    })
  })
}

/**
 * Mock DELETE /api/v1/employees/:id — enveloped shape.
 */
export async function mockDeleteEmployee(page: Page) {
  await page.route('**/api/v1/employees/*', async (route) => {
    if (route.request().method() !== 'DELETE') {
      await route.fallthrough()
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: null, meta: null, error: null }),
    })
  })
}

/**
 * Mock GET /api/v1/employees returning a server error.
 */
export async function mockEmployeeListError(page: Page, status = 500) {
  await page.route('**/api/v1/employees*', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.fallthrough()
      return
    }
    await route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify({
        success: false,
        data:    null,
        meta:    null,
        error:   { code: 'SERVER_ERROR', message: 'Internal server error' },
      }),
    })
  })
}

/**
 * Mock GET /api/v1/employees with network abort (simulates timeout).
 */
export async function mockEmployeeListAbort(page: Page) {
  await page.route('**/api/v1/employees*', async (route) => {
    await route.abort('timedout')
  })
}

/**
 * Mock GET /api/v1/employees/stats — for DashboardOverview widget.
 */
export async function mockEmployeeStats(page: Page) {
  await page.route('**/api/v1/employees/stats', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data:    { total_employees: 42, active_employees: 38, total_departments: 6 },
        meta:    null,
        error:   null,
      }),
    })
  })
}
