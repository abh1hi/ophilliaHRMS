import type { Page } from '@playwright/test'
import { makeAttendanceRecord, type MockAttendanceRecord } from '../../fixtures/seed.factory'

/**
 * Mock GET /api/v1/attendance — raw shape (apiFetchAuth).
 */
export async function mockAttendanceList(page: Page, records?: MockAttendanceRecord[]) {
  const data = records ?? [
    makeAttendanceRecord({ status: 'present' }),
    makeAttendanceRecord({ status: 'absent' }),
  ]

  await page.route('**/api/v1/attendance*', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.fallthrough()
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total:   data.length,
        skip:    0,
        limit:   20,
        records: data,
      }),
    })
  })
}

/**
 * Mock POST /api/v1/attendance/checkin — enveloped shape.
 */
export async function mockCheckin(page: Page) {
  await page.route('**/api/v1/attendance/checkin', async (route) => {
    if (route.request().method() !== 'POST') {
      await route.fallthrough()
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data:    { ...makeAttendanceRecord(), check_in_time: new Date().toISOString() },
        meta:    null,
        error:   null,
      }),
    })
  })
}

/**
 * Mock POST /api/v1/attendance/checkout — enveloped shape.
 */
export async function mockCheckout(page: Page) {
  await page.route('**/api/v1/attendance/checkout', async (route) => {
    if (route.request().method() !== 'POST') {
      await route.fallthrough()
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data:    {
          ...makeAttendanceRecord(),
          check_in_time:  new Date(Date.now() - 8 * 3600_000).toISOString(),
          check_out_time: new Date().toISOString(),
        },
        meta:  null,
        error: null,
      }),
    })
  })
}
