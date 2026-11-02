import { useEffect, useState } from 'react'
import {
  applyTheme,
  getThemePreference,
  saveThemePreference,
  watchSystemTheme,
  type ThemePreference,
} from '../lib/theme'

const OPTIONS: { value: ThemePreference; label: string }[] = [
  { value: 'system', label: 'Sistema' },
  { value: 'light', label: 'Claro' },
  { value: 'dark', label: 'Oscuro' },
]

export function ThemeToggle() {
  const [preference, setPreference] = useState<ThemePreference>(getThemePreference)

  useEffect(() => {
    if (preference !== 'system') return
    return watchSystemTheme(() => applyTheme('system'))
  }, [preference])

  function choose(value: ThemePreference) {
    setPreference(value)
    saveThemePreference(value)
  }

  return (
    <div
      role="group"
      aria-label="Tema de la pantalla"
      className="inline-flex rounded-md border border-rule bg-surface p-0.5 text-sm"
    >
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={preference === option.value}
          onClick={() => choose(option.value)}
          className={`rounded px-2.5 py-1 ${
            preference === option.value
              ? 'bg-accent-tint font-bold text-accent-strong'
              : 'text-ink-soft hover:text-ink'
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
