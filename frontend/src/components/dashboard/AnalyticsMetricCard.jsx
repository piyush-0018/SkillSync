export default function AnalyticsMetricCard({ label, value, suffix, description, accent = false }) {
  const hasValue = value !== null && value !== undefined
  return (
    <article className={`metric-card rounded-xl border p-4 ${accent ? 'accent' : ''}`}>
      <p className="text-[11px] font-semibold uppercase tracking-[.09em] text-slate-500">{label}</p>
      <div className="mt-3 flex items-baseline gap-1"><strong className="data-value text-2xl font-semibold tracking-[-.04em] sm:text-3xl">{hasValue ? Math.round(value * 10) / 10 : '—'}</strong>{hasValue && suffix && <span className="text-xs font-medium text-slate-400">{suffix}</span>}</div>
      <p className="mt-2 text-xs leading-5 text-slate-500">{description}</p>
    </article>
  )
}
