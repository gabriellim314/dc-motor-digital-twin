export type TwinParameters = {
  R: number
  L: number
  J: number
  b: number
  Ke: number
  Kt: number
}

export type LiveFrame = {
  timestamp: number
  physical_rpm: number
  twin_rpm: number
  physical_current: number
  twin_current: number
  voltage: number
  torque: number
  load_torque?: number
  temperature?: number
  rpm_error: number
  current_error?: number
  twin_accuracy: number
}

export type TwinState = {
  rpm: number
  current: number
  voltage: number
  torque: number
  temperature: number
  error: {
    rpm_error: number
    current_error: number
    rpm_rmse: number
    current_rmse: number
  }
  parameters: TwinParameters
  adaptation_status: string
}

export type AdaptResult = {
  status: string
  rpm_rmse_before: number
  rpm_rmse_after: number
  current_rmse_before: number
  current_rmse_after: number
  estimated_parameters: TwinParameters
}

export type AlertLevel = 'info' | 'success' | 'warning' | 'error'

export type AlertItem = {
  id: number
  level: AlertLevel
  message: string
  time: string
}
