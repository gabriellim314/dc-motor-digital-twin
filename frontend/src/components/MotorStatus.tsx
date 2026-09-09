import type { LiveFrame } from '../types'
import { MetricCard } from './MetricCard'

type MotorStatusProps = {
  live: LiveFrame | null
  loadTorque?: number
}

function format(value: number | undefined, digits = 2): string {
  return (value ?? 0).toFixed(digits)
}

export function MotorStatus({ live, loadTorque = 0 }: MotorStatusProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
        Physical motor
      </h2>
      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="RPM" value={format(live?.physical_rpm, 1)} unit="rpm" accent="cyan" />
        <MetricCard label="Current" value={format(live?.physical_current)} unit="A" accent="cyan" />
        <MetricCard label="Voltage" value={format(live?.voltage, 1)} unit="V" />
        <MetricCard label="Load torque" value={format(live?.load_torque ?? loadTorque, 3)} unit="N·m" />
      </div>
    </section>
  )
}
