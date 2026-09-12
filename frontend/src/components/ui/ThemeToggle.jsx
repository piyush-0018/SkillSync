import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'

export default function ThemeToggle() {
  const { resolvedTheme, toggleTheme } = useTheme()
  const Icon = resolvedTheme === 'dark' ? Sun : Moon

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="grid h-9 w-9 place-items-center rounded-lg text-slate-500 transition hover:bg-[var(--surface-subtle)] hover:text-[var(--text-primary)]"
      aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
    >
      <Icon size={18} />
    </button>
  )
}
