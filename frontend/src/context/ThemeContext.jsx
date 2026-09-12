import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const ThemeContext = createContext(null)

function getInitialTheme() {
  try {
    const savedTheme = localStorage.getItem('skillsync-theme')
    if (['light', 'dark', 'system'].includes(savedTheme)) return savedTheme
  } catch { /* Browser privacy settings may block persistent storage. */ }
  return 'system'
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(getInitialTheme)
  const [systemTheme, setSystemTheme] = useState(() => (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))

  useEffect(() => {
    const query = window.matchMedia('(prefers-color-scheme: dark)')
    const updateSystemTheme = (event) => setSystemTheme(event.matches ? 'dark' : 'light')
    query.addEventListener('change', updateSystemTheme)
    return () => query.removeEventListener('change', updateSystemTheme)
  }, [])

  const resolvedTheme = theme === 'system' ? systemTheme : theme

  useEffect(() => {
    document.documentElement.classList.toggle('dark', resolvedTheme === 'dark')
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('skillsync-theme', theme) } catch { /* The theme still works for this visit. */ }
  }, [resolvedTheme, theme])

  const value = useMemo(
    () => ({ theme, resolvedTheme, setTheme, toggleTheme: () => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark') }),
    [resolvedTheme, theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within ThemeProvider')
  return context
}
