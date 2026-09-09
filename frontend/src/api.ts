import type { AdaptResult, TwinState } from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!response.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${path} failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const api = {
  getTwinState: () => request<TwinState>('/twin/state'),
  stopSimulation: () => request('/simulation/stop', { method: 'POST' }),
  setControl: (voltage: number, loadTorque: number) =>
    request('/motor/control', {
      method: 'POST',
      body: JSON.stringify({ voltage, load_torque: loadTorque }),
    }),
  adaptTwin: () =>
    request<AdaptResult>('/twin/adapt', {
      method: 'POST',
      body: JSON.stringify({ free_params: ['J', 'b', 'R'] }),
    }),
}

export function simulationSocketUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/simulation?dt=0.01&interval=0.05`
}
