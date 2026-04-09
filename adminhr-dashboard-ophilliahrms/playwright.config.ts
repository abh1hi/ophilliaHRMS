import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e/tests',
  outputDir: './e2e/test-results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'e2e/playwright-report', open: 'never' }],
    ...(process.env.CI ? [['junit', { outputFile: 'e2e/test-results/results.xml' }]] as any : []),
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },
  projects: [
    // Setup project: writes real auth storage states to e2e/.auth/
    { name: 'setup', testMatch: /global-setup\.ts/, testDir: './e2e' },

    // Desktop browsers
    { name: 'chromium', use: { ...devices['Desktop Chrome'] }, dependencies: ['setup'] },
    { name: 'firefox',  use: { ...devices['Desktop Firefox'] }, dependencies: ['setup'] },

    // Mobile viewport (login only)
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
      testMatch: /auth\/login-mocked\.spec\.ts/,
      dependencies: ['setup'],
    },

    // Real-backend integration (only when RUN_INTEGRATION=1)
    ...(process.env.RUN_INTEGRATION ? [{
      name: 'integration',
      testMatch: /login-real\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    }] : []),
  ],
  webServer: process.env.CI ? undefined : {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
    timeout: 60_000,
  },
  timeout: 30_000,
  expect: { timeout: 8_000 },
})
