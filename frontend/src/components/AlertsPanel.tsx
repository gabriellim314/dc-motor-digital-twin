import type { AlertItem } from '../types'

const LEVELS: Record<AlertItem['level'], string> = {
  info: 'text-slate-300',
  success: 'text-emerald-300',
  warning: 'text-amber-300',
  error: 'text-rose-300',
}

type AlertsPanelProps = {
  alerts: AlertItem[]
}

export function AlertsPanel({ alerts }: AlertsPanelProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
        Alerts
      </h2>
      <ul className="space-y-2">
        {alerts.length === 0 ? (
          <li className="text-sm text-slate-500">No alerts yet.</li>
        ) : (
          alerts.map((alert) => (
            <li key={alert.id} className="rounded-lg border border-slate-800 px-3 py-2">
              <p className="text-xs text-slate-500">{alert.time}</p>
              <p className={`text-sm ${LEVELS[alert.level]}`}>{alert.message}</p>
            </li>
          ))
        )}
      </ul>
    </section>
  )
}
