export default function AnalysisSkeleton({ processing = false }) {
  return (
    <div aria-live="polite" aria-busy="true" className="space-y-5">
      {processing && (
        <div className="flex items-center gap-3 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-800 dark:border-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-200">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-300 border-t-indigo-600" />
          Reviewing resume evidence and preparing practical feedback. This can take up to a minute.
        </div>
      )}
      <div className="grid gap-5 lg:grid-cols-[.72fr_1.28fr]">
        <div className="h-64 animate-pulse rounded-3xl bg-slate-200/70 dark:bg-slate-800" />
        <div className="h-64 animate-pulse rounded-3xl bg-slate-200/70 dark:bg-slate-800" />
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        <div className="h-48 animate-pulse rounded-2xl bg-slate-200/70 dark:bg-slate-800" />
        <div className="h-48 animate-pulse rounded-2xl bg-slate-200/70 dark:bg-slate-800" />
      </div>
    </div>
  )
}
