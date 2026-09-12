function dateLabel(value) {
  return new Date(value).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

export default function ScoreTrendChart({ title, points, emptyText }) {
  const width = 620
  const height = 180
  const padding = { left: 34, right: 18, top: 16, bottom: 30 }
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom
  const coordinates = points.map((point, index) => ({
    ...point,
    x: padding.left + (index / Math.max(1, points.length - 1)) * chartWidth,
    y: padding.top + ((100 - point.score) / 100) * chartHeight,
  }))
  const path = coordinates.map((point, index) => `${index ? 'L' : 'M'} ${point.x} ${point.y}`).join(' ')
  const change = points.length >= 2 ? Math.round((points.at(-1).score - points[0].score) * 10) / 10 : null

  return (
    <section className="rounded-xl border bg-white p-5 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-3"><div><h3 className="text-sm font-semibold">{title}</h3><p className="mt-1 text-xs text-slate-500">Last {Math.min(points.length, 8)} saved results</p></div>{change !== null && <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${change > 0 ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' : change < 0 ? 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'}`}>{change > 0 ? '+' : ''}{change} pts</span>}</div>
      {points.length < 2 ? <div className="mt-5 grid h-44 place-items-center rounded-xl border border-dashed bg-[#fafaff] px-5 text-center dark:bg-slate-950/40"><div><p className="text-sm font-medium">More history is needed</p><p className="mt-1 max-w-xs text-xs leading-5 text-slate-500">{emptyText}</p></div></div> : <div className="mt-4 overflow-x-auto"><svg viewBox={`0 0 ${width} ${height}`} className="min-w-[500px]" role="img" aria-label={`${title}, scores from ${points[0].score} to ${points.at(-1).score} out of 100`}>
        {[0, 25, 50, 75, 100].map((score) => { const y = padding.top + ((100 - score) / 100) * chartHeight; return <g key={score}><line x1={padding.left} x2={width - padding.right} y1={y} y2={y} className="stroke-slate-200 dark:stroke-slate-800" strokeDasharray="3 5" /><text x={padding.left - 8} y={y + 4} textAnchor="end" className="fill-slate-400 text-[10px]">{score}</text></g> })}
        <path d={path} fill="none" className="stroke-indigo-600 dark:stroke-indigo-400" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        {coordinates.map((point) => <circle key={point.id} cx={point.x} cy={point.y} r="4" className="fill-white stroke-indigo-600 dark:fill-slate-900 dark:stroke-indigo-400" strokeWidth="2"><title>{dateLabel(point.recorded_at)}: {point.score}/100</title></circle>)}
        <text x={padding.left} y={height - 6} className="fill-slate-400 text-[10px]">{dateLabel(points[0].recorded_at)}</text><text x={width - padding.right} y={height - 6} textAnchor="end" className="fill-slate-400 text-[10px]">{dateLabel(points.at(-1).recorded_at)}</text>
      </svg></div>}
    </section>
  )
}
