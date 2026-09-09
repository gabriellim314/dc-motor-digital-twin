import type { LiveFrame } from '../types'
import { useSimulation } from '../useSimulation'
import { AlertsPanel } from './AlertsPanel'
import { ControlPanel } from './ControlPanel'
import { Motor3D, type MotorVisualStatus } from './Motor3D'
import { MotorStatus } from './MotorStatus'
import { ParameterPanel } from './ParameterPanel'
import { PerformanceChart } from './PerformanceChart'
import { TwinStatus } from './TwinStatus'

function visualStatusFromTwin(live: LiveFrame | null, adaptationStatus: string): MotorVisualStatus {
  if (adaptationStatus === 'failed') return 'error'
  if (!live) return 'normal'
  const error = Math.abs(live.rpm_error)
  if (error > 10 || live.twin_accuracy < 0.7) return 'error'
  if (error > 4 || live.twin_accuracy < 0.9) return 'warning'
  return 'normal'
}

export function Dashboard() {
  const sim = useSimulation()
  const twinRpm = sim.live?.twin_rpm ?? 0
  const motorStatus = visualStatusFromTwin(sim.live, sim.adaptationStatus)

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-6">
      <header className="mb-6 flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-cyan-400">MotorTwin</p>
          <h1 className="mt-1 text-2xl font-semibold text-slate-100">DC Motor Digital Twin</h1>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold ${
            sim.running ? 'bg-emerald-500/15 text-emerald-300' : 'bg-slate-800 text-slate-400'
          }`}
        >
          {sim.running ? 'LIVE' : 'IDLE'}
        </span>
      </header>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <Motor3D rpm={twinRpm} status={motorStatus} />
        </div>
        <ControlPanel
          running={sim.running}
          adapting={sim.adapting}
          voltage={sim.voltage}
          loadTorque={sim.loadTorque}
          onVoltage={sim.setVoltage}
          onLoadTorque={sim.setLoadTorque}
          onStart={() => void sim.start()}
          onStop={() => void sim.stop()}
          onApplyControl={(nextVoltage, nextLoadTorque) => void sim.applyControl(nextVoltage, nextLoadTorque)}
          onAdapt={() => void sim.adapt()}
        />
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <MotorStatus live={sim.live} loadTorque={sim.loadTorque} />
        <TwinStatus
          live={sim.live}
          adaptationStatus={sim.adaptationStatus}
          rpmRmse={sim.rpmRmse}
          lastAdapt={sim.lastAdapt}
        />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <PerformanceChart history={sim.history} adaptMarker={sim.adaptMarker} />
        </div>
        <div className="space-y-4">
          <ParameterPanel parameters={sim.parameters} />
          <AlertsPanel alerts={sim.alerts} />
        </div>
      </div>
    </div>
  )
}
