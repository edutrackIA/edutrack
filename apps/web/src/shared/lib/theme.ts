export type ThemePreference = 'system' | 'light' | 'dark'

const STORAGE_KEY = 'edutrack.theme'
const DARK_QUERY = '(prefers-color-scheme: dark)'

export function getThemePreference(): ThemePreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored === 'light' || stored === 'dark' ? stored : 'system'
  } catch {
    return 'system'
  }
}

export function systemPrefersDark(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia(DARK_QUERY).matches
}

export function applyTheme(preference: ThemePreference): void {
  const dark = preference === 'dark' || (preference === 'system' && systemPrefersDark())
  document.documentElement.classList.toggle('dark', dark)
}

export function saveThemePreference(preference: ThemePreference): void {
  try {
    if (preference === 'system') localStorage.removeItem(STORAGE_KEY)
    else localStorage.setItem(STORAGE_KEY, preference)
  } catch {
    /* storage unavailable: the choice lasts until the page reloads */
  }
  applyTheme(preference)
}

/** Follows changes of the operating system theme while "system" is selected. */
export function watchSystemTheme(onChange: () => void): () => void {
  if (typeof window.matchMedia !== 'function') return () => {}
  const query = window.matchMedia(DARK_QUERY)
  query.addEventListener('change', onChange)
  return () => query.removeEventListener('change', onChange)
}
