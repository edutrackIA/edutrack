import { expect, test } from '@playwright/test'
import { login, USERS } from './support'

test('el director ve el semáforo y abre la vista rápida de un estudiante', async ({ page }) => {
  await login(page, USERS.director)

  const trafficLight = page.getByRole('region', { name: 'Semáforo del colegio' })
  await expect(trafficLight).toBeVisible()
  // The low-risk lane starts collapsed; with few students at risk it may be the only one.
  const showList = trafficLight.getByRole('button', { name: 'Ver lista' })
  if (await showList.isVisible()) await showList.click()
  const student = trafficLight
    .getByRole('button')
    .filter({ hasNotText: /^(Ver|Ocultar) lista$/ })
    .first()
  await student.click()

  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('heading').first()).not.toBeEmpty()
  await page.keyboard.press('Escape')
  await expect(dialog).toBeHidden()
})

test('la ficha completa vuelve al aula desde la que se abrió', async ({ page }) => {
  await login(page, USERS.director)
  await page.goto('/aulas')

  await page.getByRole('link', { name: /^Ver ficha de/ }).first().click()
  await expect(page).toHaveURL(/\/estudiantes\/\d+/)
  await page.getByRole('link', { name: /^Volver a/ }).click()

  await expect(page).toHaveURL(/\/aulas/)
})
