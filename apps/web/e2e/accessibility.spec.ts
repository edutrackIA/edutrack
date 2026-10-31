import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'
import { login, USERS } from './support'

async function seriousViolations(page: Page) {
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
  return results.violations
    .filter((violation) => violation.impact === 'serious' || violation.impact === 'critical')
    .map((violation) => `${violation.id}: ${violation.help} (${violation.nodes.length})`)
}

test('el login no tiene problemas graves de accesibilidad', async ({ page }) => {
  await page.goto('/login')

  expect(await seriousViolations(page)).toEqual([])
})

test('el resumen del director no tiene problemas graves de accesibilidad', async ({ page }) => {
  await login(page, USERS.director)
  await expect(page.getByRole('region', { name: 'Semáforo del colegio' })).toBeVisible()

  expect(await seriousViolations(page)).toEqual([])
})
