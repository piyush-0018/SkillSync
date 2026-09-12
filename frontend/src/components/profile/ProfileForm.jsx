import { LoaderCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/api'

const experienceOptions = [
  ['student', 'Student'],
  ['fresher', 'Fresher'],
  ['0-1 years', '0–1 years'],
  ['1-3 years', '1–3 years'],
  ['3+ years', '3+ years'],
]

export default function ProfileForm({ setup = false, onComplete }) {
  const { user, updateProfile } = useAuth()
  const [values, setValues] = useState({
    full_name: user.full_name || '',
    target_role: user.target_role || '',
    experience_level: user.experience_level || '',
  })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    setValues({
      full_name: user.full_name || '',
      target_role: user.target_role || '',
      experience_level: user.experience_level || '',
    })
  }, [user])

  function updateField(event) {
    const { name, value } = event.target
    setValues((current) => ({ ...current, [name]: value }))
    setErrors((current) => ({ ...current, [name]: '' }))
    setServerError('')
    setSuccessMessage('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const nextErrors = {}
    if (values.full_name.trim().length < 2) nextErrors.full_name = 'Enter your full name.'
    if (setup && values.target_role.trim().length < 2) nextErrors.target_role = 'Enter the role you are preparing for.'
    if (setup && !values.experience_level) nextErrors.experience_level = 'Select your current experience level.'
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors)
      return
    }

    setIsSubmitting(true)
    try {
      await updateProfile({
        full_name: values.full_name.trim(),
        target_role: values.target_role.trim() || null,
        experience_level: values.experience_level || null,
      })
      if (onComplete) onComplete()
      else setSuccessMessage('Your profile has been updated.')
    } catch (error) {
      setServerError(getApiErrorMessage(error, 'Could not update your profile.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5" noValidate>
      {serverError && <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">{serverError}</div>}
      {successMessage && <div role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 px-3.5 py-3 text-sm text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">{successMessage}</div>}

      <label className="block text-sm font-medium" htmlFor="full_name">Full name
        <input id="full_name" name="full_name" value={values.full_name} onChange={updateField} autoComplete="name" className={`input-field ${errors.full_name ? 'border-rose-500' : ''}`} aria-invalid={Boolean(errors.full_name)} aria-describedby={errors.full_name ? 'profile-name-error' : undefined} />
        {errors.full_name && <span id="profile-name-error" className="mt-1.5 block text-xs font-normal text-rose-600 dark:text-rose-400">{errors.full_name}</span>}
      </label>
      <label className="block text-sm font-medium" htmlFor="email">Email address
        <input id="email" value={user.email} className="input-field cursor-not-allowed bg-slate-100 text-slate-500 dark:bg-slate-800" aria-describedby="profile-email-help" disabled />
        <span id="profile-email-help" className="mt-1.5 block text-xs font-normal text-slate-400">Your sign-in email cannot be changed here.</span>
      </label>
      <label className="block text-sm font-medium" htmlFor="target_role">Target role
        <input id="target_role" name="target_role" value={values.target_role} onChange={updateField} className={`input-field ${errors.target_role ? 'border-rose-500' : ''}`} placeholder="e.g. Backend Developer" aria-invalid={Boolean(errors.target_role)} aria-describedby={errors.target_role ? 'profile-role-error' : undefined} />
        {errors.target_role && <span id="profile-role-error" className="mt-1.5 block text-xs font-normal text-rose-600 dark:text-rose-400">{errors.target_role}</span>}
      </label>
      <label className="block text-sm font-medium" htmlFor="experience_level">Experience level
        <select id="experience_level" name="experience_level" value={values.experience_level} onChange={updateField} className={`input-field ${errors.experience_level ? 'border-rose-500' : ''}`} aria-invalid={Boolean(errors.experience_level)} aria-describedby={errors.experience_level ? 'profile-experience-error' : undefined}>
          <option value="">Select your level</option>
          {experienceOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        {errors.experience_level && <span id="profile-experience-error" className="mt-1.5 block text-xs font-normal text-rose-600 dark:text-rose-400">{errors.experience_level}</span>}
      </label>
      <button type="submit" disabled={isSubmitting} className="button-primary w-full gap-2 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto">
        {isSubmitting && <LoaderCircle size={16} className="animate-spin" />}
        {isSubmitting ? 'Saving…' : setup ? 'Complete setup' : 'Save changes'}
      </button>
    </form>
  )
}
