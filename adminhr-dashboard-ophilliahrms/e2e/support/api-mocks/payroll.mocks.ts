import type { Page } from '@playwright/test'
import { uniqueId } from '../../fixtures/seed.factory'

/**
 * Mock GET /api/v1/payroll/runs — enveloped shape.
 */
export async function mockPayrollRuns(page: Page) {
  await page.route('**/api/v1/payroll/runs*', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.fallthrough()
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          total: 2,
          runs: [
            {
              id:         uniqueId('run'),
              period:     'March 2026',
              status:     'completed',
              total_paid: 450000,
              employees:  38,
            },
            {
              id:         uniqueId('run'),
              period:     'February 2026',
              status:     'completed',
              total_paid: 442000,
              employees:  37,
            },
          ],
        },
        meta:  { page: 1, page_size: 20, total_items: 2, total_pages: 1 },
        error: null,
      }),
    })
  })
}

/**
 * Mock GET /api/v1/payroll/payslips — enveloped shape.
 */
export async function mockPayslips(page: Page) {
  await page.route('**/api/v1/payroll/payslips*', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.fallthrough()
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          total:    2,
          payslips: [
            {
              id:            uniqueId('slip'),
              employee_name: 'Alice Nguyen',
              period:        'March 2026',
              net_pay:       72000,
              status:        'paid',
            },
            {
              id:            uniqueId('slip'),
              employee_name: 'Bob Smith',
              period:        'March 2026',
              net_pay:       65000,
              status:        'paid',
            },
          ],
        },
        meta:  { page: 1, page_size: 20, total_items: 2, total_pages: 1 },
        error: null,
      }),
    })
  })
}

/**
 * Mock POST /api/v1/payroll/runs — initiate a new payroll run.
 */
export async function mockCreatePayrollRun(page: Page) {
  await page.route('**/api/v1/payroll/runs', async (route) => {
    if (route.request().method() !== 'POST') {
      await route.fallthrough()
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data:    { id: uniqueId('run'), status: 'processing', period: 'April 2026' },
        meta:    null,
        error:   null,
      }),
    })
  })
}
