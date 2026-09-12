import { motion } from 'framer-motion'
import { FileUp, LoaderCircle, Upload } from 'lucide-react'
import { useRef, useState } from 'react'

export default function ResumeDropzone({ hasResume, isUploading, progress, onFileSelected, disabled = false }) {
  const inputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)

  function handleDrop(event) {
    event.preventDefault()
    setIsDragging(false)
    if (!disabled && !isUploading && event.dataTransfer.files[0]) onFileSelected(event.dataTransfer.files[0])
  }

  function handleInput(event) {
    const file = event.target.files[0]
    if (file) onFileSelected(file)
    event.target.value = ''
  }

  return (
    <motion.section layout className="rounded-2xl border border-[#e1e3ed] bg-[#fdfdff] p-5 dark:border-slate-800 dark:bg-slate-900 sm:p-6">
      <div className="mb-4"><h2 className="font-semibold">{hasResume ? 'Replace resume' : 'Upload your resume'}</h2><p className="mt-1 text-xs leading-5 text-slate-500">PDF only · Maximum 5 MB · Text-based files work best</p></div>
      <div
        onDragEnter={(event) => { event.preventDefault(); if (!isUploading) setIsDragging(true) }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setIsDragging(false) }}
        onDrop={handleDrop}
        className={`relative flex min-h-48 flex-col items-center justify-center rounded-xl border border-dashed px-5 py-8 text-center transition ${isDragging ? 'border-indigo-500 bg-indigo-50/70 dark:bg-indigo-950/30' : 'border-slate-300 bg-[#f8f7fc] dark:border-slate-700 dark:bg-slate-950/40'} ${isUploading ? 'cursor-wait' : ''}`}
        aria-busy={isUploading}
      >
        {isUploading ? (
          <div className="w-full max-w-sm">
            <span className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-indigo-100 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"><LoaderCircle size={22} className="animate-spin" /></span>
            <p className="mt-4 text-sm font-semibold">{progress < 100 ? `Uploading resume… ${progress}%` : 'Upload complete. Parsing resume…'}</p>
            <p className="mt-1 text-xs text-slate-500">Keep this page open while SkillSync extracts your information.</p>
            <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><motion.div className="h-full rounded-full bg-indigo-600" animate={{ width: `${progress}%` }} transition={{ duration: 0.2 }} /></div>
          </div>
        ) : (
          <>
            <span className="grid h-12 w-12 place-items-center rounded-xl border bg-[#fdfdff] text-indigo-600 shadow-sm dark:bg-slate-900 dark:text-indigo-300"><FileUp size={21} /></span>
            <p className="mt-4 text-sm font-semibold">Drop your PDF here</p>
            <p className="mt-1 text-xs text-slate-500">or choose a file from your device</p>
            <button type="button" disabled={disabled} onClick={() => inputRef.current?.click()} className="button-secondary mt-5 gap-2"><Upload size={15} />Browse PDF</button>
          </>
        )}
        <input ref={inputRef} type="file" accept=".pdf,application/pdf" onChange={handleInput} className="sr-only" disabled={disabled || isUploading} aria-label={hasResume ? 'Choose replacement resume PDF' : 'Choose resume PDF'} />
      </div>
    </motion.section>
  )
}
