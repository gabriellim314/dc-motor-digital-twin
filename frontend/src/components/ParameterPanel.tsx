import type { TwinParameters } from '../types'

const LABELS: { key: keyof TwinParameters; label: string; unit: string }[] = [
  { key: 'R', label: 'Resistance R', unit: 'Ω' },
  { key: 'L', label: 'Inductance L', unit: 'H' },
  { key: 'J', label: 'Inertia J', unit: 'kg·m²' },
  { key: 'b', label: 'Friction b', unit: 'N·m·s/rad' },
  { key: 'Ke', label: 'Back-EMF Ke', unit: 'V·s/rad' },
  { key: 'Kt', label: 'Torque Kt', unit: 'N·m/A' },
]

type ParameterPanelProps = {
  parameters: TwinParameters
}

export function ParameterPanel({ parameters }: ParameterPanelProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
        Twin parameters
      </h2>
      <dl className="space-y-2">
        {LABELS.map((item) => (
          <div key={item.key} className="flex items-baseline justify-between border-b border-slate-800 pb-2">
            <dt className="text-sm text-slate-400">{item.label}</dt>
            <dd className="font-mono text-sm text-slate-100">
              {parameters[item.key].toFixed(4)}
              <span className="ml-1 text-slate-500">{item.unit}</span>
            </dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
