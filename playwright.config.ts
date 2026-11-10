import { defineConfig, devices } from '@playwright/test'

const localChannel = process.env.CI ? undefined : 'msedge'

export default defineConfig({
  testDir: './tests/e2e',
  outputDir: './test-results',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: { trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: [
    { name: 'mobile-375', use: { ...devices['iPhone 13'], browserName: 'chromium', channel: localChannel, viewport: { width: 375, height: 812 } } },
    { name: 'desktop', use: { ...devices['Desktop Chrome'], channel: localChannel, viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { ...devices['iPhone 13'], browserName: 'chromium', channel: localChannel, viewport: { width: 390, height: 844 } } },
    { name: 'tablet-768', use: { ...devices['Desktop Chrome'], channel: localChannel, viewport: { width: 768, height: 1024 } } },
    { name: 'laptop-1024', use: { ...devices['Desktop Chrome'], channel: localChannel, viewport: { width: 1024, height: 900 } } },
    { name: 'wide-1920', use: { ...devices['Desktop Chrome'], channel: localChannel, viewport: { width: 1920, height: 1080 } } },
  ],
  webServer: [
    { command: 'npm run dev:public', url: 'http://127.0.0.1:5173', reuseExistingServer: true },
    { command: 'npm run dev:admin', url: 'http://127.0.0.1:5174', reuseExistingServer: true },
  ],
})
