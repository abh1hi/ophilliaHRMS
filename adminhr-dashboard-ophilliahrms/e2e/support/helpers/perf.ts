import type { Page } from '@playwright/test'
import { expect } from '@playwright/test'

/**
 * Navigate to a URL and assert the navigation completes within maxMs.
 * Returns the elapsed time in milliseconds.
 */
export async function measureNavigation(
  page: Page,
  url: string,
  maxMs = 2000,
): Promise<number> {
  const start = Date.now()
  await page.goto(url)
  const elapsed = Date.now() - start
  expect(
    elapsed,
    `Navigation to ${url} took ${elapsed}ms — exceeds ${maxMs}ms threshold`,
  ).toBeLessThan(maxMs)
  return elapsed
}

/**
 * Assert a page action (e.g., tab switch) completes within maxMs.
 */
export async function measureAction(
  label: string,
  action: () => Promise<void>,
  maxMs = 1000,
): Promise<number> {
  const start = Date.now()
  await action()
  const elapsed = Date.now() - start
  expect(
    elapsed,
    `Action "${label}" took ${elapsed}ms — exceeds ${maxMs}ms threshold`,
  ).toBeLessThan(maxMs)
  return elapsed
}
