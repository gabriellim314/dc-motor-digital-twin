import type { AdaptResult, LiveFrame } from '../types'
import { MetricCard } from './MetricCard'

type TwinStatusProps = {
  live: LiveFrame | null
  adaptationStatus: string
  rpmRmse?: number
  lastAdapt?: AdaptResult | null
}

export function TwinStatus({ live, adaptationStatus, rpmRmse = 0, lastAdapt = null }: TwinStatusProps) {
  const accuracy = (live?.twin_accuracy ?? 0) * 100
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
          Digital Twin
        </h2>
        <span className="rounded-full border border-slate-700 px-2 py-0.5 text-xs text-slate-400">
          {adaptationStatus}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="Twin RPM" value={(live?.twin_rpm ?? 0).toFixed(1)} unit="rpm" accent="amber" />
        <MetricCard label="RPM error" value={(live?.rpm_error ?? 0).toFixed(2)} unit="rpm" accent="amber" />
        <MetricCard label="Current error" value={(live?.current_error ?? 0).toFixed(3)} unit="A" />
        <MetricCard label="Live RMSE" value={rpmRmse.toFixed(2)} unit="rpm" />
      </div>
      {lastAdapt ? (
        <p className="mt-3 font-mono text-xs text-emerald-300">
          Adaptation RMSE {lastAdapt.rpm_rmse_before.toFixed(3)} → {lastAdapt.rpm_rmse_after.toFixed(3)}
        </p>
      ) : null}
      <div className="mt-4">
        <div className="mb-1 flex justify-between text-xs text-slate-500">
          <span>TWIN ACCURACY</span>
          <span className="font-mono text-amber-300">{accuracy.toFixed(1)}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-800">
          <div
            className="h-full rounded-full bg-amber-400"
            style={{ width: `${Math.max(0, Math.min(100, accuracy))}%` }}
          />
        </div>
      </div>
    </section>
  )
}
