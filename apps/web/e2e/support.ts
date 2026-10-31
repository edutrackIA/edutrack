import { expect, type APIRequestContext, type Page } from '@playwright/test'

// 127.0.0.1 rather than localhost: Node may try IPv6 (::1) first and miss the containers.
export const API = 'http://127.0.0.1:8000/api/v1'
export const MAILPIT = 'http://127.0.0.1:8025/api/v1'
export const PASSWORD = 'Edutrack123!'

export const USERS = {
  director: 'director@edutrack.dev',
  teacher: 'docente@edutrack.dev',
  analyst: 'analista@edutrack.dev',
  parent: 'padre@edutrack.dev',
} as const

export async function login(page: Page, email: string, password = PASSWORD): Promise<void> {
  await page.goto('/login')
  await page.getByLabel('Correo').fill(email)
  await page.getByLabel('Contraseña').fill(password)
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await expect(page).not.toHaveURL(/\/login/)
}

/** Guardians see the consent screen until they accept the current notice. */
export async function acceptPrivacyIfAsked(page: Page): Promise<void> {
  const consent = page.getByRole('heading', { name: 'Antes de empezar' })
  const portal = page.getByRole('heading', { name: /^Avance de/ })
  await expect(consent.or(portal)).toBeVisible()
  if (await consent.isVisible()) {
    await page.getByRole('checkbox').check()
    // exact: "No acepto, salir" also contains "acepto".
    await page.getByRole('button', { name: 'Acepto', exact: true }).click()
  }
  await expect(portal).toBeVisible()
}

interface MailSummary {
  ID: string
  Subject: string
  To: { Address: string }[]
}

/** Waits for an email to `to` whose subject contains `subject`, and returns its text. */
export async function waitForEmail(
  request: APIRequestContext,
  to: string,
  subject: string,
): Promise<string> {
  let text = ''
  await expect
    .poll(
      async () => {
        const response = await request.get(`${MAILPIT}/search`, {
          params: { query: `to:${to}` },
        })
        const { messages } = (await response.json()) as { messages: MailSummary[] }
        const match = messages.find((message) => message.Subject.includes(subject))
        if (!match) return false
        const detail = await request.get(`${MAILPIT}/message/${match.ID}`)
        text = ((await detail.json()) as { Text: string }).Text
        return true
      },
      { timeout: 15_000 },
    )
    .toBe(true)
  return text
}

export async function clearMailbox(request: APIRequestContext): Promise<void> {
  await request.delete(`${MAILPIT}/messages`)
}
