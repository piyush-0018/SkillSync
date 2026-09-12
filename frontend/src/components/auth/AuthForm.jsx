import { motion } from 'framer-motion'
import { LoaderCircle } from 'lucide-react'
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/api'
import PasswordField from './PasswordField'

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function safeInternalPath(path) {
  if (typeof path !== 'string') return null
  if (!path.startsWith('/') || path.startsWith('//') || path.includes('\\')) return null
  return path
}

function validateForm(values, isRegister) {
  const errors = {}
  if (isRegister && values.full_name.trim().length < 2) errors.full_name = 'Enter your full name.'
  if (!emailPattern.test(values.email.trim())) errors.email = 'Enter a valid email address.'
  if (!values.password) errors.password = 'Enter your password.'

  if (isRegister && values.password) {
    if (values.password.length < 8) errors.password = 'Use at least 8 characters.'
    else if (!/[a-z]/.test(values.password)) errors.password = 'Add at least one lowercase letter.'
    else if (!/[A-Z]/.test(values.password)) errors.password = 'Add at least one uppercase letter.'
    else if (!/\d/.test(values.password)) errors.password = 'Add at least one number.'
    if (values.password !== values.confirm_password) errors.confirm_password = 'Passwords do not match.'
  }
  return errors
}

export default function AuthForm({ mode }) {
  const isRegister = mode === 'register'
  const navigate = useNavigate()
  const location = useLocation()
  const { login, register } = useAuth()
  const [values, setValues] = useState({ full_name: '', email: '', password: '', confirm_password: '' })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  function updateField(event) {
    const { name, value } = event.target
    setValues((current) => ({ ...current, [name]: value }))
    setErrors((current) => ({ ...current, [name]: '' }))
    setServerError('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const validationErrors = validateForm(values, isRegister)
    if (Object.keys(validationErrors).length) {
      setErrors(validationErrors)
      return
    }

    setIsSubmitting(true)
    setServerError('')
    try {
      if (isRegister) {
        await register({ full_name: values.full_name.trim(), email: values.email.trim(), password: values.password })
        navigate('/profile/setup', { replace: true })
      } else {
        const user = await login({ email: values.email.trim(), password: values.password })
        const requestedPath = safeInternalPath(location.state?.from?.pathname)
        navigate(requestedPath || (user.target_role && user.experience_level ? '/dashboard' : '/profile/setup'), { replace: true })
      }
    } catch (error) {
      setServerError(getApiErrorMessage(error, isRegister ? 'Could not create your account.' : 'Could not sign you in.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const formIncomplete = !values.email || !values.password || (isRegister && (!values.full_name || !values.confirm_password))

  return (
    <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.26 }} className="surface-panel p-6 sm:p-8">
      <h1 className="text-2xl font-semibold tracking-tight">{isRegister ? 'Create your account' : 'Welcome back'}</h1>
      <p className="mt-2 text-sm leading-6 text-slate-500">{isRegister ? 'Create your workspace and start with your career profile.' : 'Sign in to continue your preparation.'}</p>

      {serverError && <div role="alert" className="mt-5 rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">{serverError}</div>}

      <form className="mt-7 space-y-4" onSubmit={handleSubmit} noValidate>
        {isRegister && (
          <label className="block text-sm font-medium" htmlFor="full_name">Full name
            <input id="full_name" className={`input-field ${errors.full_name ? 'border-rose-500' : ''}`} name="full_name" value={values.full_name} onChange={updateField} autoComplete="name" placeholder="Your full name" aria-invalid={Boolean(errors.full_name)} aria-describedby={errors.full_name ? 'full-name-error' : undefined} autoFocus />
            {errors.full_name && <span id="full-name-error" className="mt-1.5 block text-xs font-normal text-rose-600 dark:text-rose-400">{errors.full_name}</span>}
          </label>
        )}
        <label className="block text-sm font-medium" htmlFor="email">Email address
          <input id="email" className={`input-field ${errors.email ? 'border-rose-500' : ''}`} type="email" name="email" value={values.email} onChange={updateField} autoComplete="email" placeholder="you@example.com" aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? 'email-error' : undefined} autoFocus={!isRegister} />
          {errors.email && <span id="email-error" className="mt-1.5 block text-xs font-normal text-rose-600 dark:text-rose-400">{errors.email}</span>}
        </label>
        <PasswordField id="password" name="password" value={values.password} onChange={updateField} autoComplete={isRegister ? 'new-password' : 'current-password'} placeholder={isRegister ? '8+ characters, uppercase and number' : 'Your password'} error={errors.password} />
        {isRegister && <PasswordField id="confirm_password" name="confirm_password" label="Confirm password" value={values.confirm_password} onChange={updateField} autoComplete="new-password" placeholder="Enter your password again" error={errors.confirm_password} />}
        <button className="button-primary mt-2 w-full gap-2 disabled:cursor-not-allowed disabled:opacity-60" type="submit" disabled={isSubmitting || formIncomplete}>
          {isSubmitting && <LoaderCircle size={16} className="animate-spin" />}
          {isSubmitting ? (isRegister ? 'Creating account…' : 'Signing in…') : (isRegister ? 'Create account' : 'Sign in')}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">{isRegister ? 'Already have an account?' : 'New to SkillSync?'}{' '}<Link className="font-semibold text-indigo-600 hover:text-indigo-700 dark:text-indigo-400" to={isRegister ? '/login' : '/register'}>{isRegister ? 'Sign in' : 'Create an account'}</Link></p>
    </motion.section>
  )
}
