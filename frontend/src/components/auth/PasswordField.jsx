import { Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'

export default function PasswordField({ error, id = 'password', label = 'Password', ...inputProps }) {
  const [visible, setVisible] = useState(false)

  return (
    <label className="block text-sm font-medium" htmlFor={id}>
      {label}
      <span className="relative mt-1.5 block">
        <input
          {...inputProps}
          id={id}
          type={visible ? 'text' : 'password'}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${id}-error` : undefined}
          className={`input-field mt-0 pr-11 ${error ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/15' : ''}`}
        />
        <button
          type="button"
          onClick={() => setVisible((current) => !current)}
          className="absolute inset-y-0 right-0 grid w-11 place-items-center rounded-r-lg text-slate-400 transition hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500 dark:hover:text-slate-200"
          aria-label={`${visible ? 'Hide' : 'Show'} ${label.toLowerCase()}`}
        >
          {visible ? <EyeOff size={17} /> : <Eye size={17} />}
        </button>
      </span>
      {error && <span id={`${id}-error`} className="mt-1.5 block text-xs font-normal text-rose-600 dark:text-rose-400">{error}</span>}
    </label>
  )
}
