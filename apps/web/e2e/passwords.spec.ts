import { expect, test } from '@playwright/test'
import { clearMailbox, login, PASSWORD, USERS, waitForEmail } from './support'

test('recuperar la contraseña por correo y volver a entrar', async ({ page, request }) => {
  await clearMailbox(request)
  await page.goto('/login')
  await page.getByRole('link', { name: '¿Olvidaste tu contraseña?' }).click()

  await page.getByLabel('Correo').fill(USERS.analyst)
  await page.getByRole('button', { name: 'Enviar enlace' }).click()
  await expect(page.getByText(/te enviamos un enlace/)).toBeVisible()

  const email = await waitForEmail(request, USERS.analyst, 'restablece')
  const link = email.match(/https?:\/\/\S+\/restablecer\/\S+/)?.[0]
  expect(link).toBeTruthy()
  await page.goto(new URL(link!).pathname)

  // Same demo password again, so the other tests keep working.
  await page.getByLabel('Nueva contraseña').fill(PASSWORD)
  await page.getByLabel('Repite la contraseña').fill(PASSWORD)
  await page.getByRole('button', { name: 'Guardar contraseña' }).click()
  await expect(page.getByRole('heading', { name: 'Contraseña actualizada' })).toBeVisible()

  await login(page, USERS.analyst)
  await expect(page.getByRole('heading', { name: 'Evaluaciones de riesgo', level: 1 })).toBeVisible()
})
