import AxeBuilder from '@axe-core/playwright'
import type { Page } from '@playwright/test'
import { expect } from '@playwright/test'

/**
 * Run axe-core accessibility checks on the current page state.
 * Fails the test if any wcag2a or wcag2aa violations are found.
 */
export async function checkA11y(page: Page, tag?: string) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze()

  if (results.violations.length > 0) {
    const summary = results.violations
      .map((v) => `[${v.impact}] ${v.id}: ${v.description} (${v.nodes.length} nodes)`)
      .join('\n')
    console.error(`Accessibility violations on ${tag ?? 'page'}:\n${summary}`)
  }

  expect(
    results.violations,
    `A11y violations on ${tag ?? 'page'} — run with --headed and check the axe report`,
  ).toEqual([])
}
