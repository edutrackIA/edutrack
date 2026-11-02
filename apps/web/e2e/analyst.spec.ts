import { expect, test } from '@playwright/test'
import { login, USERS } from './support'

test('el analista revisa un archivo antes de importarlo y nada se guarda al cancelar', async ({
  page,
}) => {
  await login(page, USERS.analyst)
  await page.getByRole('link', { name: 'Carga de datos' }).click()

  await page.getByRole('radio', { name: /^Notas/ }).check()
  await page.getByLabel('Archivo').setInputFiles({
    name: 'notas-e2e.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('student_code,subject,score\n20260001,Matemática,15\n20260001,Física,12\n'),
  })
  await page.getByRole('button', { name: 'Revisar archivo' }).click()

  await expect(page.getByText('Todavía no se ha guardado nada.')).toBeVisible()
  await expect(page.getByText('El curso Física no existe')).toBeVisible()
  await page.getByRole('button', { name: 'Cancelar y corregir el archivo' }).click()

  await expect(page.getByText('Aquí verás cuántas filas se importaron y qué corregir.')).toBeVisible()
})
