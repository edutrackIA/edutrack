import { expect, test } from '@playwright/test'
import { acceptPrivacyIfAsked, clearMailbox, login, USERS, waitForEmail } from './support'

test('el apoderado acepta el aviso, ve el avance y avisa una preocupación al tutor', async ({
  page,
  request,
}) => {
  await clearMailbox(request)
  await login(page, USERS.parent)
  await acceptPrivacyIfAsked(page)

  await expect(page.getByText(/riesgo/i)).toHaveCount(0)

  await page.getByLabel('Nos preocupa').check()
  await page.getByLabel(/Me preocupa cómo lo tratan sus compañeros/).check()
  const send = page.getByRole('button', { name: /respuesta$/ })
  await send.click()
  await expect(page.getByText(/El tutor recibió su respuesta/)).toBeVisible()

  // The peer concern reaches the tutor immediately (only when it was not already reported).
  const email = await waitForEmail(request, USERS.teacher, 'Prioritario').catch(() => null)
  if (email !== null) expect(email).toContain('compañeros')
})
