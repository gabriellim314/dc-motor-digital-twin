import type { ReactNode } from 'react'
import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { LiveFrame } from '../types'

type PerformanceChartProps = {
  history: LiveFrame[]
  adaptMarker?: number | null
}

function ChartFrame({
  title,
  children,
}: {
  title: string
  children: ReactNode
}) {
  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{title}</h3>
      <div className="h-56">{children}</div>
    </div>
  )
}

export function PerformanceChart({ history, adaptMarker = null }: PerformanceChartProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
        Physical vs Twin
      </h2>
      <div className="grid gap-6">
        <ChartFrame title="RPM">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value: number) => value.toFixed(1)}
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 12 }}
              />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155', color: '#e2e8f0' }}
                labelFormatter={(value) => `t = ${Number(value).toFixed(2)} s`}
              />
              {adaptMarker != null ? (
                <ReferenceLine
                  x={adaptMarker}
                  stroke="#34d399"
                  strokeDasharray="4 4"
                  label={{ value: 'Adapt', fill: '#34d399', fontSize: 11 }}
                />
              ) : null}
              <Line type="monotone" dataKey="physical_rpm" name="Physical RPM" stroke="#22d3ee" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="twin_rpm" name="Twin RPM" stroke="#fbbf24" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </ChartFrame>
        <ChartFrame title="Model error (RPM)">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value: number) => value.toFixed(1)}
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 12 }}
              />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155', color: '#e2e8f0' }}
                labelFormatter={(value) => `t = ${Number(value).toFixed(2)} s`}
              />
              {adaptMarker != null ? (
                <ReferenceLine x={adaptMarker} stroke="#34d399" strokeDasharray="4 4" />
              ) : null}
              <Line type="monotone" dataKey="rpm_error" name="RPM error" stroke="#f87171" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </ChartFrame>
      </div>
    </section>
  )
}
