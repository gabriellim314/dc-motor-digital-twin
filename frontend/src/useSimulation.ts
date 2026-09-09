import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, simulationSocketUrl } from './api'
import type { AdaptResult, AlertItem, AlertLevel, LiveFrame, TwinParameters } from './types'

const HISTORY_LIMIT = 180
const RMSE_WINDOW = 40
const DEFAULT_PARAMETERS: TwinParameters = {
  R: 2.0,
  L: 0.5,
  J: 0.01,
  b: 0.1,
  Ke: 0.05,
  Kt: 0.05,
}

function windowRmse(history: LiveFrame[], key: 'rpm_error' | 'current_error', window = RMSE_WINDOW): number {
  const slice = history.slice(-window)
  if (slice.length === 0) return 0
  const mse =
    slice.reduce((sum, frame) => {
      const value = key === 'current_error' ? (frame.current_error ?? 0) : frame.rpm_error
      return sum + value * value
    }, 0) / slice.length
  return Math.sqrt(mse)
}

export function useSimulation() {
  const [live, setLive] = useState<LiveFrame | null>(null)
  const [history, setHistory] = useState<LiveFrame[]>([])
  const [parameters, setParameters] = useState<TwinParameters>(DEFAULT_PARAMETERS)
  const [adaptationStatus, setAdaptationStatus] = useState('idle')
  const [lastAdapt, setLastAdapt] = useState<AdaptResult | null>(null)
  const [adaptMarker, setAdaptMarker] = useState<number | null>(null)
  const [running, setRunning] = useState(false)
  const [adapting, setAdapting] = useState(false)
  const [voltage, setVoltage] = useState(12)
  const [loadTorque, setLoadTorque] = useState(0.05)
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const socketRef = useRef<WebSocket | null>(null)
  const liveRef = useRef<LiveFrame | null>(null)
  const alertId = useRef(1)
  const warnedHighError = useRef(false)

  const pushAlert = useCallback((level: AlertLevel, message: string) => {
    const item: AlertItem = {
      id: alertId.current,
      level,
      message,
      time: new Date().toLocaleTimeString(),
    }
    alertId.current += 1
    setAlerts((current) => [item, ...current].slice(0, 12))
  }, [])

  const refreshTwin = useCallback(async () => {
    const twin = await api.getTwinState()
    setParameters(twin.parameters)
    setAdaptationStatus(twin.adaptation_status)
  }, [])

  useEffect(() => {
    refreshTwin().catch(() => {
      pushAlert('error', 'Backend unavailable. Start the FastAPI server on port 8000.')
    })
    return () => {
      socketRef.current?.close()
    }
  }, [pushAlert, refreshTwin])

  const stop = useCallback(async () => {
    socketRef.current?.close()
    socketRef.current = null
    try {
      await api.stopSimulation()
    } catch {
      // The socket close already stops the live loop.
    }
    setRunning(false)
    pushAlert('info', 'Simulation stopped.')
  }, [pushAlert])

  const start = useCallback(async () => {
    if (socketRef.current) {
      await stop()
    }
    try {
      await api.setControl(voltage, loadTorque)
    } catch {
      pushAlert('error', 'Could not apply motor control before start.')
      return
    }

    const socket = new WebSocket(simulationSocketUrl())
    socketRef.current = socket
    socket.onopen = () => {
      setRunning(true)
      setHistory([])
      setAdaptMarker(null)
      warnedHighError.current = false
      pushAlert('success', 'Live simulation connected.')
    }
    socket.onmessage = (event: MessageEvent<string>) => {
      const payload = JSON.parse(event.data) as LiveFrame & { status?: string; detail?: string }
      if (payload.status === 'stopped') {
        setRunning(false)
        return
      }
      if (payload.status === 'error') {
        setRunning(false)
        pushAlert('error', payload.detail ?? 'Invalid simulation state.')
        return
      }
      liveRef.current = payload
      setLive(payload)
      setHistory((current) => [...current, payload].slice(-HISTORY_LIMIT))
      if (!warnedHighError.current && payload.timestamp > 0.4 && Math.abs(payload.rpm_error) > 4) {
        warnedHighError.current = true
        pushAlert('warning', `RPM error is ${payload.rpm_error.toFixed(2)}. Consider adapting the twin.`)
      }
    }
    socket.onerror = () => {
      pushAlert('error', 'WebSocket error. Is the API running?')
    }
    socket.onclose = () => {
      setRunning(false)
      socketRef.current = null
    }
  }, [loadTorque, pushAlert, stop, voltage])

  const applyControl = useCallback(
    async (nextVoltage?: number, nextLoadTorque?: number) => {
      const appliedVoltage = nextVoltage ?? voltage
      const appliedTorque = nextLoadTorque ?? loadTorque
      try {
        await api.setControl(appliedVoltage, appliedTorque)
      } catch {
        pushAlert('error', 'Failed to update motor control.')
      }
    },
    [loadTorque, pushAlert, voltage],
  )

  const adapt = useCallback(async () => {
    setAdapting(true)
    setAdaptationStatus('running')
    try {
      const result = await api.adaptTwin()
      setParameters(result.estimated_parameters)
      setAdaptationStatus(result.status)
      setLastAdapt(result)
      if (liveRef.current) {
        setAdaptMarker(liveRef.current.timestamp)
      }
      warnedHighError.current = false
      pushAlert(
        'success',
        `Twin adapted. RPM RMSE ${result.rpm_rmse_before.toFixed(3)} → ${result.rpm_rmse_after.toFixed(3)}.`,
      )
    } catch {
      setAdaptationStatus('failed')
      pushAlert('error', 'Parameter adaptation failed.')
    } finally {
      setAdapting(false)
    }
  }, [pushAlert])

  const rpmRmse = useMemo(() => windowRmse(history, 'rpm_error'), [history])

  return {
    live,
    history,
    parameters,
    adaptationStatus,
    lastAdapt,
    adaptMarker,
    rpmRmse,
    running,
    adapting,
    voltage,
    loadTorque,
    setVoltage,
    setLoadTorque,
    alerts,
    start,
    stop,
    applyControl,
    adapt,
  }
}
