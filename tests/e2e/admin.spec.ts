import { expect, test } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.route('**/auth/session', (route) => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({ id: 'owner', display_name: '审核用户', avatar_url: null, role: 'owner', expires_at: new Date(Date.now() + 3600000).toISOString(), csrf_token: 'csrf' }),
  }))
  await page.route('**/api/admin/dashboard', (route) => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({
      current_release: { id: 'r1', version: '0.3.0', platform: 'Windows x64' },
      preview_release: null, cms_dirty: true, content_version: 3, download_starts: 128,
      jobs: [{ id: 'j1', version: '0.4.0-beta.1', status: 'scanning', progress: 98, updated_at: new Date().toISOString() }],
      disk: { free: 21474836480, total: 53687091200, used: 32212254720 },
      backup: { status: 'ok', last_file: '20260921T032000Z' },
      services: { api: 'healthy', database: 'healthy' },
    }),
  }))
  await page.route('**/api/admin/download-trends', (route) => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify([{ day: '2026-09-20', count: 12 }, { day: '2026-09-21', count: 19 }]),
  }))
})

test('admin overview exposes release, content and operational health', async ({ page }) => {
  await page.goto('http://127.0.0.1:5174')
  await expect(page.getByRole('heading', { name: '早上好，版本与内容都在这里。' })).toBeVisible()
  await expect(page.getByText('v0.3.0')).toBeVisible()
  await expect(page.getByText('127.0.0.1:9100', { exact: true })).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)
  expect(overflow).toBe(false)
  if (['desktop', 'mobile'].includes(test.info().project.name)) {
    await page.screenshot({
      path: 'design-review/renders/implementation/admin-' + test.info().project.name + '.png',
      fullPage: true,
    })
  }
})
