import { defineConfig, devices } from '@playwright/test'

/**
 * End-to-end tests against the whole stack: web (Vite), API, ML service, MySQL and Mailpit.
 * Start the backend with `docker compose up -d`, load the demo data, then `npm run e2e`.
 */
export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/global-setup.ts',
  fullyParallel: false,
  // Tests share the demo database: running them one at a time keeps them predictable.
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  timeout: 30_000,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: 'http://localhost:5173',
    locale: 'es-PE',
    timezoneId: 'America/Lima',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
})
