import { useId, useState, type FormEvent } from 'react'
import { Button } from '../../../shared/ui/Button'
import { useCreateSubject, useRenameSubject, useSubjects, type Subject } from '../api'
import { Field, inputClass, MutationError, SetupSection } from './SetupParts'

function SubjectItem({ subject }: { subject: Subject }) {
  const rename = useRenameSubject()
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(subject.name)

  return (
    <li className="flex flex-wrap items-center justify-between gap-3 border-b border-rule py-2.5 last:border-b-0">
      {editing ? (
        <>
          <input
            aria-label={`Nuevo nombre de ${subject.name}`}
            value={name}
            onChange={(event) => setName(event.target.value)}
            className={`${inputClass} flex-1`}
          />
          <div className="flex gap-2">
            <Button
              pending={rename.isPending}
              onClick={() =>
                rename.mutate({ id: subject.id, name }, { onSuccess: () => setEditing(false) })
              }
            >
              Guardar
            </Button>
            <Button variant="ghost" onClick={() => setEditing(false)}>
              Cancelar
            </Button>
          </div>
          <div className="basis-full">
            <MutationError error={rename.error} />
          </div>
        </>
      ) : (
        <>
          <span className="text-ink">{subject.name}</span>
          <Button variant="ghost" onClick={() => setEditing(true)}>
            Renombrar<span className="sr-only"> {subject.name}</span>
          </Button>
        </>
      )}
    </li>
  )
}

export function SubjectsSection() {
  const subjects = useSubjects()
  const create = useCreateSubject()
  const [name, setName] = useState('')
  const nameId = useId()

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    create.mutate(name, { onSuccess: () => setName('') })
  }

  return (
    <SetupSection
      title="Cursos"
      description="Los nombres deben coincidir con los de los archivos de notas que importes."
      form={
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
          <Field label="Nombre del curso" htmlFor={nameId}>
            <input
              id={nameId}
              value={name}
              onChange={(event) => setName(event.target.value)}
              className={`${inputClass} w-72`}
            />
          </Field>
          <Button type="submit" pending={create.isPending} disabled={name.trim().length < 2}>
            Agregar curso
          </Button>
          <div className="basis-full">
            <MutationError error={create.error} />
          </div>
        </form>
      }
    >
      {subjects.data && (
        <ul aria-label="Cursos del colegio" className="max-w-2xl">
          {subjects.data.map((subject) => (
            <SubjectItem key={subject.id} subject={subject} />
          ))}
        </ul>
      )}
    </SetupSection>
  )
}
