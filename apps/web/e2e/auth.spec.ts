import { expect, test } from '@playwright/test'
import { login, USERS } from './support'

test.describe('Inicio de sesión', () => {
  const landings = [
    { email: USERS.director, heading: 'Resumen del colegio' },
    { email: USERS.teacher, heading: 'Mis aulas' },
    { email: USERS.analyst, heading: 'Evaluaciones de riesgo' },
  ]

  for (const { email, heading } of landings) {
    test(`${email} llega a su inicio`, async ({ page }) => {
      await login(page, email)

      await expect(page.getByRole('heading', { name: heading, level: 1 })).toBeVisible()
    })
  }

  test('una contraseña incorrecta muestra un mensaje claro', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Correo').fill(USERS.teacher)
    await page.getByLabel('Contraseña').fill('NoEsLaClave1')
    await page.getByRole('button', { name: 'Ingresar' }).click()

    await expect(page.getByRole('alert')).toContainText('no son correctos')
  })

  test('la sesión sobrevive a recargas rápidas seguidas', async ({ page }) => {
    await login(page, USERS.teacher)

    // Regression for the token rotation race (ADR-0008): several reloads in a row.
    for (let index = 0; index < 5; index += 1) {
      await page.reload({ waitUntil: 'commit' })
    }
    await page.reload()

    await expect(page.getByRole('heading', { name: 'Mis aulas', level: 1 })).toBeVisible()
  })

  test('cerrar sesión vuelve al login y protege las páginas', async ({ page }) => {
    await login(page, USERS.director)

    await page.getByRole('button', { name: 'Cerrar sesión' }).click()
    await expect(page).toHaveURL(/\/login/)
    await page.goto('/resumen')

    await expect(page).toHaveURL(/\/login/)
    await expect(page.getByLabel('Contraseña')).toBeVisible()
  })
})
