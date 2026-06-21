type MetricCardProps = {
  label: string
  value: string
  hint?: string
  accent?: 'cyan' | 'amber' | 'rose' | 'zinc'
}

const accentStyles = {
  cyan: 'from-cyan-400/20 to-cyan-400/0 border-cyan-300/20',
  amber: 'from-amber-400/20 to-amber-400/0 border-amber-300/20',
  rose: 'from-rose-400/20 to-rose-400/0 border-rose-300/20',
  zinc: 'from-white/10 to-white/0 border-white/10',
}

export function MetricCard({ label, value, hint, accent = 'zinc' }: MetricCardProps) {
  return (
    <div
      className={`rounded-3xl border bg-gradient-to-br p-5 shadow-[0_20px_80px_rgba(0,0,0,0.22)] ${accentStyles[accent]}`}
    >
      <div className="text-xs tracking-[0.22em] text-zinc-500 uppercase">{label}</div>
      <div className="mt-3 font-serif text-3xl text-white">{value}</div>
      {hint ? <div className="mt-2 text-sm text-zinc-400">{hint}</div> : null}
    </div>
  )
}
