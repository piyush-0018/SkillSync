import { AlertCircle, ArrowRight, Award, BriefcaseBusiness, CheckCircle2, FileText, FolderKanban, GraduationCap, Mail, Phone, ShieldCheck, Sparkles, Trash2, Wrench } from 'lucide-react'
import { Link } from 'react-router-dom'

function formatFileSize(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function ExtractedSection({ icon: Icon, title, items }) {
  return (
    <section className="rounded-2xl border border-[#e1e3ed] bg-[#fdfdff] p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-2.5"><Icon size={17} className="text-indigo-600 dark:text-indigo-400" /><h3 className="text-sm font-semibold">{title}</h3></div>
      {items.length ? <ul className="mt-4 space-y-2.5">{items.slice(0, 8).map((item, index) => <li key={`${item}-${index}`} className="text-sm leading-6 text-slate-600 dark:text-slate-300">{item}</li>)}</ul> : <p className="mt-4 text-sm text-slate-400">Not identified in this resume.</p>}
    </section>
  )
}

export default function ResumeDetails({ resume, confirmDelete, isDeleting, disabled = false, onAskDelete, onCancelDelete, onDelete }) {
  const data = resume.structured_data
  const parsed = resume.parsing_status === 'parsed'

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-[#e1e3ed] bg-[#fdfdff] p-5 dark:border-slate-800 dark:bg-slate-900 sm:p-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 items-start gap-4"><span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#ebeafe] text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"><FileText size={19} /></span><div className="min-w-0"><p className="truncate font-semibold">{resume.original_filename}</p><p className="mt-1 text-xs text-slate-500">{formatFileSize(resume.file_size)} · Uploaded {new Date(resume.uploaded_at).toLocaleDateString()}</p><span className={`mt-3 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${parsed ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'}`}>{parsed ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}{parsed ? 'Parsed successfully' : 'Parsing needs attention'}</span></div></div>
          {!confirmDelete && <button type="button" onClick={onAskDelete} disabled={disabled} className="inline-flex items-center gap-2 self-start rounded-lg px-3 py-2 text-sm font-medium text-slate-500 transition hover:bg-rose-50 hover:text-rose-700 dark:hover:bg-rose-950/30 dark:hover:text-rose-300"><Trash2 size={16} />Delete</button>}
        </div>

        {confirmDelete && <div className="mt-5 flex flex-col gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-900 dark:bg-rose-950/30 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-sm font-semibold text-rose-800 dark:text-rose-200">Delete this resume?</p><p className="mt-1 text-xs text-rose-700 dark:text-rose-300">The PDF, extracted information, and saved analyses will be removed.</p></div><div className="flex gap-2"><button type="button" onClick={onCancelDelete} disabled={isDeleting || disabled} className="button-secondary px-3 py-2">Cancel</button><button type="button" onClick={onDelete} disabled={isDeleting || disabled} className="inline-flex items-center justify-center rounded-lg bg-rose-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:opacity-60">{isDeleting ? 'Deleting…' : 'Delete resume'}</button></div></div>}

        {!parsed && <div role="status" className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200"><strong>Text could not be extracted.</strong> {resume.parsing_error} Replace this file with a text-based PDF to try again.</div>}
      </section>

      {parsed && (
        <>
          <section className="flex flex-col gap-4 rounded-2xl border border-indigo-200 bg-indigo-50/70 p-5 dark:border-indigo-900 dark:bg-indigo-950/30 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-start gap-3"><span className="mt-0.5 text-indigo-600 dark:text-indigo-400"><Sparkles size={18} /></span><div><h2 className="text-sm font-semibold">Ready for AI analysis</h2><p className="mt-1 text-xs leading-5 text-slate-500">Get a fixed rubric score and practical feedback for your target role.</p></div></div><Link to="/resume/analysis" className="button-primary shrink-0 gap-2">Analyze resume <ArrowRight size={15} /></Link></section>
          <section><div className="mb-4"><h2 className="font-semibold">Extracted information</h2><p className="mt-1 text-xs text-slate-500">Review what SkillSync identified using deterministic parsing.</p></div><div className="grid gap-4 md:grid-cols-2"><div className="rounded-2xl border border-[#e1e3ed] bg-[#fdfdff] p-5 dark:border-slate-800 dark:bg-slate-900"><p className="text-xs font-medium uppercase tracking-wide text-slate-400">Candidate</p><p className="mt-3 text-lg font-semibold">{data.name || 'Name not identified'}</p><div className="mt-4 space-y-2 text-sm text-slate-500">{data.contact.email && <p className="flex items-center gap-2"><Mail size={14} />{data.contact.email}</p>}{data.contact.phone && <p className="flex items-center gap-2"><Phone size={14} />{data.contact.phone}</p>}{!data.contact.email && !data.contact.phone && <p>No contact details identified.</p>}</div></div><div className="rounded-2xl border border-[#e1e3ed] bg-[#fdfdff] p-5 dark:border-slate-800 dark:bg-slate-900"><div className="flex items-center gap-2.5"><Wrench size={17} className="text-indigo-600 dark:text-indigo-400" /><h3 className="text-sm font-semibold">Technical skills</h3></div>{data.technical_skills.length ? <div className="mt-4 flex flex-wrap gap-2">{data.technical_skills.slice(0, 20).map((skill) => <span key={skill} className="rounded-full bg-[#efeff8] px-2.5 py-1 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-200">{skill}</span>)}</div> : <p className="mt-4 text-sm text-slate-400">Not identified in this resume.</p>}</div></div></section>
          <div className="grid gap-4 md:grid-cols-2"><ExtractedSection icon={GraduationCap} title="Education" items={data.education} /><ExtractedSection icon={BriefcaseBusiness} title="Experience" items={data.experience} /><ExtractedSection icon={FolderKanban} title="Projects" items={data.projects} /><ExtractedSection icon={ShieldCheck} title="Certifications" items={data.certifications} /><ExtractedSection icon={Award} title="Achievements" items={data.achievements} /></div>
        </>
      )}
    </div>
  )
}
