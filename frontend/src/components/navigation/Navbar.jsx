import { Menu, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import Brand from '../ui/Brand'
import ThemeToggle from '../ui/ThemeToggle'

const links = [
  ['Features', '#features'],
  ['How it works', '#how-it-works'],
  ['Platform', '#platform'],
]

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="sticky top-0 z-40 border-b bg-[color-mix(in_srgb,var(--surface)_92%,transparent)] backdrop-blur-xl dark:border-[#1b2a3b] dark:bg-[#030914]/94">
      <nav className="container-page flex h-[72px] items-center justify-between" aria-label="Main navigation">
        <Brand />
        <div className="hidden items-center gap-7 md:flex">
          {links.map(([label, href]) => (
            <a key={label} href={href} className="relative text-sm font-medium text-slate-600 transition after:absolute after:-bottom-1 after:left-0 after:h-px after:w-0 after:bg-indigo-600 after:transition-all hover:text-slate-950 hover:after:w-full dark:text-slate-300 dark:hover:text-white">{label}</a>
          ))}
        </div>
        <div className="hidden items-center gap-2 md:flex">
          <ThemeToggle />
          <Link to="/login" className="button-secondary">Log in</Link>
          <Link to="/register" className="button-primary">Get started</Link>
        </div>
        <div className="flex items-center gap-1 md:hidden">
          <ThemeToggle />
          <button type="button" className="grid h-9 w-9 place-items-center rounded-lg" onClick={() => setMenuOpen((open) => !open)} aria-label="Toggle navigation" aria-expanded={menuOpen}>
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </nav>
      {menuOpen && (
        <div className="container-page border-t py-4 md:hidden">
          <div className="flex flex-col gap-1">
            {links.map(([label, href]) => <a key={label} href={href} onClick={() => setMenuOpen(false)} className="rounded-lg px-3 py-2 text-sm font-medium hover:bg-slate-100 dark:hover:bg-slate-900">{label}</a>)}
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 border-t pt-4">
            <Link to="/login" className="button-secondary">Sign in</Link>
            <Link to="/register" className="button-primary">Get started</Link>
          </div>
        </div>
      )}
    </header>
  )
}
