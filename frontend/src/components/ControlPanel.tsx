type ControlPanelProps = {
  running: boolean
  adapting: boolean
  voltage: number
  loadTorque: number
  onVoltage: (value: number) => void
  onLoadTorque: (value: number) => void
  onStart: () => void
  onStop: () => void
  onApplyControl: (voltage?: number, loadTorque?: number) => void
  onAdapt: () => void
}

export function ControlPanel({
  running,
  adapting,
  voltage,
  loadTorque,
  onVoltage,
  onLoadTorque,
  onStart,
  onStop,
  onApplyControl,
  onAdapt,
}: ControlPanelProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
        Control
      </h2>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onStart}
          disabled={running || adapting}
          className="rounded-lg bg-cyan-500 px-3 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40"
        >
          Start simulation
        </button>
        <button
          type="button"
          onClick={onStop}
          disabled={!running}
          className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200 disabled:opacity-40"
        >
          Stop simulation
        </button>
        <button
          type="button"
          onClick={onAdapt}
          disabled={adapting}
          className="rounded-lg bg-amber-400 px-3 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40"
        >
          {adapting ? 'Adapting…' : 'Adapt Digital Twin'}
        </button>
      </div>

      <label className="mt-5 block text-xs uppercase tracking-[0.16em] text-slate-500">
        Voltage {voltage.toFixed(1)} V
        <input
          type="range"
          min={0}
          max={24}
          step={0.5}
          value={voltage}
          onChange={(event) => {
            const value = Number(event.target.value)
            onVoltage(value)
            onApplyControl(value, loadTorque)
          }}
          className="mt-2 w-full accent-cyan-400"
        />
      </label>

      <label className="mt-4 block text-xs uppercase tracking-[0.16em] text-slate-500">
        Load torque {loadTorque.toFixed(3)} N·m
        <input
          type="range"
          min={0}
          max={0.2}
          step={0.005}
          value={loadTorque}
          onChange={(event) => {
            const value = Number(event.target.value)
            onLoadTorque(value)
            onApplyControl(voltage, value)
          }}
          className="mt-2 w-full accent-amber-400"
        />
      </label>
    </section>
  )
}
