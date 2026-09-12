import { AnimatePresence, motion } from 'framer-motion'
import { AlertCircle, FileText, RefreshCw } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import ResumeDetails from '../components/resume/ResumeDetails'
import ResumeDropzone from '../components/resume/ResumeDropzone'
import PageHeader from '../components/ui/PageHeader'
import { getApiErrorMessage } from '../services/api'
import { deleteResume, getResume, uploadResume } from '../services/resumeService'

const MAX_FILE_SIZE = 5 * 1024 * 1024

function validateFile(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) return 'Choose a file with a .pdf extension.'
  if (file.type && file.type !== 'application/pdf') return 'The selected file is not identified as a PDF.'
  if (file.size === 0) return 'The selected file is empty.'
  if (file.size > MAX_FILE_SIZE) return 'Resume must be 5 MB or smaller.'
  return ''
}

export default function ResumePage() {
  const [resume, setResume] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [loadFailed, setLoadFailed] = useState(false)

  const loadResume = useCallback(async () => {
    setIsLoading(true)
    setError('')
    setLoadFailed(false)
    try {
      setResume(await getResume())
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Could not load your resume.'))
      setLoadFailed(true)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { loadResume() }, [loadResume])

  async function handleFile(file) {
    if (isUploading || isDeleting || isLoading) return
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }
    setError('')
    setLoadFailed(false)
    setProgress(0)
    setIsUploading(true)
    try {
      setResume(await uploadResume(file, setProgress))
      setConfirmDelete(false)
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Could not upload this resume.'))
    } finally {
      setIsUploading(false)
    }
  }

  async function handleDelete() {
    if (isUploading || isDeleting) return
    setIsDeleting(true)
    setError('')
    setLoadFailed(false)
    try {
      await deleteResume()
      setResume(null)
      setConfirmDelete(false)
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Could not delete your resume.'))
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .24 }} className="mx-auto max-w-5xl">
      <PageHeader icon={FileText} kicker="Resume" title="Resume workspace" description="Upload one PDF resume. SkillSync stores it securely and identifies its key sections before any AI analysis runs." />

      {error && <div role="alert" className="mt-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300"><AlertCircle size={18} className="mt-0.5 shrink-0" /><div className="flex-1">{error}</div>{loadFailed && <button type="button" onClick={loadResume} className="inline-flex items-center gap-1 font-semibold"><RefreshCw size={14} />Retry</button>}</div>}

      <div className="mt-8 space-y-6">
        {isLoading ? (
          <div className="space-y-4" aria-label="Loading resume"><div className="h-56 animate-pulse rounded-2xl bg-slate-200/70 dark:bg-slate-800" /><div className="h-32 animate-pulse rounded-2xl bg-slate-200/70 dark:bg-slate-800" /></div>
        ) : (
          <>
            <ResumeDropzone disabled={isDeleting} hasResume={Boolean(resume)} isUploading={isUploading} progress={progress} onFileSelected={handleFile} />
            <AnimatePresence mode="wait">
              {resume ? (
                <motion.div key={resume.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}><ResumeDetails disabled={isUploading} resume={resume} confirmDelete={confirmDelete} isDeleting={isDeleting} onAskDelete={() => setConfirmDelete(true)} onCancelDelete={() => setConfirmDelete(false)} onDelete={handleDelete} /></motion.div>
              ) : (
                <motion.section key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-2xl border border-dashed border-[#d9dbe7] bg-[#f8f7fc] p-8 text-center dark:border-slate-800 dark:bg-slate-900/40"><span className="mx-auto grid h-11 w-11 place-items-center rounded-xl bg-[#ebeafe] text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"><FileText size={19} /></span><h2 className="mt-4 font-semibold">No resume uploaded</h2><p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">Choose your latest text-based PDF above. Extracted information will appear here after parsing.</p></motion.section>
              )}
            </AnimatePresence>
          </>
        )}
      </div>
    </motion.div>
  )
}
