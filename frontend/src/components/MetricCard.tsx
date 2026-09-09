type MetricCardProps = {
  label: string
  value: string
  unit: string
  accent?: 'cyan' | 'amber' | 'slate'
}

const accents = {
  cyan: 'text-cyan-300',
  amber: 'text-amber-300',
  slate: 'text-slate-100',
}

export function MetricCard({ label, value, unit, accent = 'slate' }: MetricCardProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/80 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className={`mt-2 font-mono text-2xl ${accents[accent]}`}>
        {value}
        <span className="ml-1 text-sm text-slate-500">{unit}</span>
      </p>
    </div>
  )
}
