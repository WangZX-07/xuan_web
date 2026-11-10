import { expect, test } from '@playwright/test'

test('public site preserves the approved narrative and responsive bounds', async ({ page }) => {
  await page.goto('http://127.0.0.1:5173')
  await expect(page.getByRole('heading', { name: '让呼吸运动不再成为精准放疗的盲区' })).toBeVisible()
  await expect(page.getByRole('link', { name: '辽ICP备2026005104号-2' })).toHaveAttribute('href', 'https://beian.miit.gov.cn/')
  await expect(page.getByText('不得直接用于患者治疗决策')).toBeVisible()
  await expect(page.getByRole('heading', { name: '把离散时相组织成可追溯的连续表达' })).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)
  expect(overflow).toBe(false)
  for (const image of await page.locator('img').all()) expect(await image.getAttribute('alt')).not.toBeNull()
})

test('public site is keyboard reachable', async ({ page }) => {
  await page.goto('http://127.0.0.1:5173')
  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: '跳至主要内容' })).toBeFocused()
})
