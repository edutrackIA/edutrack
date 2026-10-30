import { useId, useState, type FormEvent } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import { periodOptionLabel, usePeriods } from '../../periods/api'
import { downloadTemplate, useImportFile, type ImportJob, type ImportKind } from '../api'

const KINDS: { value: ImportKind; label: string; columns: string; note?: string }[] = [
  {
    value: 'STUDENTS',
    label: 'Estudiantes',
    columns: 'code, first_name, last_name, birth_date, sex, year, grade, section',
    note: 'Cárgalos primero: las notas y la asistencia se vinculan por el código.',
  },
  {
    value: 'GRADES',
    label: 'Notas',
    columns: 'student_code, subject, score',
    note: 'Notas de 0 a 20 del bimestre que elijas.',
  },
  {
    value: 'ATTENDANCE',
    label: 'Asistencia',
    columns: 'student_code, date, status',
    note: 'Estados: PRESENT, ABSENT, LATE o JUSTIFIED.',
  },
  {
    value: 'GUARDIANS',
    label: 'Apoderados',
    columns: 'student_code, full_name, email, kinship',
    note: 'Al confirmar, los correos nuevos reciben una invitación para crear su contraseña.',
  },
]

function rows(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`
}

function summary(job: ImportJob): string {
  if (job.preview) {
    if (job.rows_ok === 0) return 'Ninguna fila se puede importar. Corrige el archivo y vuelve a revisarlo.'
    const ready = rows(job.rows_ok, 'fila lista', 'filas listas')
    return job.rows_failed
      ? `${ready} para importar y ${job.rows_failed} con errores. Las filas con errores no se guardarán.`
      : `${ready} para importar, sin errores.`
  }
  if (job.status === 'FAILED') return 'No se importó ninguna fila. Revisa el problema y vuelve a intentarlo.'
  const done = rows(job.rows_ok, 'fila importada', 'filas importadas')
  return job.rows_failed ? `${done}, ${job.rows_failed} con errores.` : `${done}.`
}

function ImportResult({
  job,
  confirming,
  onConfirm,
  onCancel,
}: {
  job: ImportJob
  confirming: boolean
  onConfirm: () => void
  onCancel: () => void
}) {
  const tone =
    job.rows_ok === 0
      ? 'bg-risk-high-bg text-risk-high'
      : job.rows_failed
        ? 'bg-risk-medium-bg text-risk-medium'
        : 'bg-risk-low-bg text-risk-low'
  return (
    <section aria-labelledby="result-title" className="flex flex-col gap-4 lg:min-h-0">
      <div className="shrink-0">
        <h2 id="result-title" className="font-figure text-xl font-semibold text-ink">
          {job.preview ? `Revisión de ${job.filename}` : `Resultado de ${job.filename}`}
        </h2>
        {job.preview && (
          <p className="mt-1 text-sm text-ink-soft">Todavía no se ha guardado nada.</p>
        )}
        <p className={`mt-2 rounded-md px-3 py-2 ${tone}`}>{summary(job)}</p>
        {job.preview && (
          <div className="mt-4 flex flex-wrap gap-3">
            {job.rows_ok > 0 && (
              <Button pending={confirming} onClick={onConfirm}>
                {!job.rows_failed
                  ? `Importar ${rows(job.rows_ok, 'fila', 'filas')}`
                  : job.rows_ok === 1
                    ? 'Importar la fila válida'
                    : `Importar las ${job.rows_ok} filas válidas`}
              </Button>
            )}
            <Button variant="secondary" disabled={confirming} onClick={onCancel}>
              Cancelar y corregir el archivo
            </Button>
          </div>
        )}
      </div>
      {job.errors.length > 0 && (
        <div className="lg:min-h-0 lg:overflow-y-auto">
          <Table caption="Problemas encontrados en el archivo">
            <TableHead>
              <tr>
                <TableHeaderCell className="text-right">Fila</TableHeaderCell>
                <TableHeaderCell>Columna</TableHeaderCell>
                <TableHeaderCell>Problema</TableHeaderCell>
              </tr>
            </TableHead>
            <TableBody>
              {job.errors.map((error, index) => (
                <TableRow key={index}>
                  <TableCell className="text-right tabular-nums">{error.row ?? '—'}</TableCell>
                  <TableCell className="font-mono text-sm">{error.column ?? '—'}</TableCell>
                  <TableCell>{error.message}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </section>
  )
}

export default function ImportsPage() {
  const periods = usePeriods()
  const preview = useImportFile()
  const upload = useImportFile()
  const [kind, setKind] = useState<ImportKind>('STUDENTS')
  const [periodId, setPeriodId] = useState<number | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [templateError, setTemplateError] = useState<string | null>(null)
  const fileId = useId()
  const periodFieldId = useId()
  const selectedKind = KINDS.find((item) => item.value === kind)!
  const period = periodId ?? periods.data?.[periods.data.length - 1]?.id ?? null

  const request = (preview: boolean) =>
    file && {
      kind,
      file,
      periodId: kind === 'GRADES' && period ? period : undefined,
      preview,
    }

  function reset() {
    preview.reset()
    upload.reset()
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const body = request(true)
    if (!body) return
    upload.reset()
    preview.mutate(body)
  }

  function confirmImport() {
    const body = request(false)
    if (body) upload.mutate(body)
  }

  // After confirming, the stored result replaces the preview.
  const shown = upload.data ?? preview.data
  const error = preview.error ?? upload.error

  return (
    <div className="flex flex-col lg:h-full">
      <PageHeader
        className="mb-5 shrink-0"
        title="Carga de datos"
        description="Importa estudiantes, notas y asistencia desde archivos .csv o .xlsx."
      />
      <div className="grid gap-8 lg:min-h-0 lg:flex-1 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:grid-rows-[minmax(0,1fr)]">
        <form onSubmit={handleSubmit} className="flex flex-col gap-5 lg:min-h-0 lg:overflow-y-auto">
          <fieldset>
            <legend className="font-bold text-ink">Qué vas a importar</legend>
            <div className="mt-2 grid grid-cols-2 gap-2 xl:grid-cols-4">
              {KINDS.map((option) => (
                <label
                  key={option.value}
                  className={`flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2.5 ${
                    kind === option.value ? 'border-accent bg-accent-tint' : 'border-rule bg-surface'
                  }`}
                >
                  <input
                    type="radio"
                    name="kind"
                    value={option.value}
                    checked={kind === option.value}
                    onChange={() => {
                      setKind(option.value)
                      reset()
                    }}
                    className="accent-accent"
                  />
                  {option.label}
                </label>
              ))}
            </div>
            <p className="mt-3 text-sm text-ink-soft">
              Columnas: <span className="font-mono text-ink">{selectedKind.columns}</span>
            </p>
            {selectedKind.note && <p className="mt-1 text-sm text-ink-soft">{selectedKind.note}</p>}
          </fieldset>

          {kind === 'GRADES' && (
            <div className="flex flex-col gap-1.5">
              <label htmlFor={periodFieldId} className="font-bold text-ink">
                Bimestre
              </label>
              <select
                id={periodFieldId}
                value={period ?? ''}
                onChange={(event) => {
                  setPeriodId(Number(event.target.value))
                  reset()
                }}
                className="w-fit rounded-md border border-rule bg-surface px-3 py-2 text-ink"
              >
                {periods.data?.map((item) => (
                  <option key={item.id} value={item.id}>
                    {periodOptionLabel(item)}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setTemplateError(null)
                downloadTemplate(kind).catch((error) => setTemplateError(messageFor(error)))
              }}
            >
              Descargar plantilla de {selectedKind.label.toLowerCase()}
            </Button>
            {templateError && <ErrorMessage>{templateError}</ErrorMessage>}
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor={fileId} className="font-bold text-ink">
              Archivo
            </label>
            <input
              id={fileId}
              type="file"
              accept=".csv,.xlsx"
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null)
                reset()
              }}
              className="rounded-md border border-dashed border-rule bg-surface px-3 py-4 text-ink file:mr-3 file:rounded-md file:border-0 file:bg-accent-tint file:px-3 file:py-1.5 file:font-bold file:text-accent-strong"
            />
            <p className="text-sm text-ink-soft">
              Hasta 2 MB. Primero revisamos el archivo y te mostramos los errores; nada se guarda
              hasta que confirmes.
            </p>
          </div>

          {error && <ErrorMessage>{messageFor(error)}</ErrorMessage>}
          <div>
            <Button
              type="submit"
              pending={preview.isPending}
              disabled={!file || preview.isPending || upload.isPending}
            >
              Revisar archivo
            </Button>
          </div>
        </form>

        <div className="rounded-xl border border-rule bg-surface p-6 lg:flex lg:min-h-0 lg:flex-col">
          {shown ? (
            <ImportResult
              job={shown}
              confirming={upload.isPending}
              onConfirm={confirmImport}
              onCancel={reset}
            />
          ) : (
            <p className="text-ink-soft">Aquí verás cuántas filas se importaron y qué corregir.</p>
          )}
        </div>
      </div>
    </div>
  )
}
