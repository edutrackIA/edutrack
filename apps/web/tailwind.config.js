/** @type {import('tailwindcss').Config} */
const token = (name) => `rgb(var(--color-${name}) / <alpha-value>)`

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        paper: token('paper'),
        surface: token('surface'),
        ink: { DEFAULT: token('ink'), soft: token('ink-soft') },
        rule: token('rule'),
        accent: {
          DEFAULT: token('accent'),
          strong: token('accent-strong'),
          tint: token('accent-tint'),
        },
        'on-accent': token('on-accent'),
        risk: {
          low: token('risk-low'),
          'low-bg': token('risk-low-bg'),
          'low-mark': token('risk-low-mark'),
          medium: token('risk-medium'),
          'medium-bg': token('risk-medium-bg'),
          'medium-mark': token('risk-medium-mark'),
          high: token('risk-high'),
          'high-bg': token('risk-high-bg'),
          'high-mark': token('risk-high-mark'),
        },
      },
      fontFamily: {
        sans: ['"Atkinson Hyperlegible"', 'system-ui', 'sans-serif'],
        figure: ['"Source Serif 4"', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}
