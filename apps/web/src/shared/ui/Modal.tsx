import { useEffect, useId, useRef, type ReactNode } from 'react'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: ReactNode
}

/**
 * Native <dialog>: traps focus, closes with Escape and makes the page behind inert.
 * The backdrop blurs and dims whatever is behind it.
 */
export function Modal({ open, onClose, title, description, children }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const titleId = useId()

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
      className="m-auto w-[min(44rem,calc(100%-2rem))] rounded-2xl border border-rule bg-surface p-0 text-ink shadow-2xl backdrop:bg-[rgb(7_12_22/0.55)] backdrop:backdrop-blur-sm"
    >
      <div className="flex max-h-[85vh] flex-col">
        <header className="flex shrink-0 items-start justify-between gap-4 border-b border-rule px-6 py-4">
          <div>
            <h2 id={titleId} className="font-figure text-2xl font-semibold text-ink">
              {title}
            </h2>
            {description && <p className="mt-0.5 text-ink-soft">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="rounded-md p-2 text-ink-soft hover:bg-paper hover:text-ink"
          >
            <svg aria-hidden="true" viewBox="0 0 16 16" className="h-4 w-4">
              <path
                d="M3 3 13 13M13 3 3 13"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </header>
        <div className="overflow-y-auto px-6 py-5">{children}</div>
      </div>
    </dialog>
  )
}
