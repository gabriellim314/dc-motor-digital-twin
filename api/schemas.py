"""Pydantic request and response models for the MotorTwin API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class TwinParametersModel(BaseModel):
    R: float
    L: float
    J: float
    b: float
    Ke: float
    Kt: float


class TwinErrorModel(BaseModel):
    rpm_error: float
    current_error: float
    rpm_rmse: float
    current_rmse: float


class MotorStateResponse(BaseModel):
    rpm: float
    current: float
    voltage: float
    torque: float
    temperature: float
    load_torque: float


class TwinStateResponse(BaseModel):
    rpm: float
    current: float
    voltage: float
    torque: float
    temperature: float
    error: TwinErrorModel
    parameters: TwinParametersModel
    adaptation_status: str


class SimulationStartRequest(BaseModel):
    t_end: float = Field(default=2.0, gt=0.0)
    dt: float = Field(default=0.01, gt=0.0)
    voltage: float | None = None
    load_torque: float | None = None


class SimulationStatusResponse(BaseModel):
    running: bool
    message: str


class MotorControlRequest(BaseModel):
    voltage: float
    load_torque: float = 0.05


class AdaptRequest(BaseModel):
    free_params: list[str] = Field(default_factory=lambda: ["J", "b", "R"])


class AdaptResponse(BaseModel):
    status: str
    rpm_rmse_before: float
    rpm_rmse_after: float
    current_rmse_before: float
    current_rmse_after: float
    initial_parameters: TwinParametersModel
    estimated_parameters: TwinParametersModel
    physical_parameters: TwinParametersModel


class SimulationSample(BaseModel):
    timestamp: float
    voltage: float
    physical_rpm: float
    twin_rpm: float
    rpm_error: float
    physical_current: float
    twin_current: float
    current_error: float
    torque: float
    temperature: float


class SimulationResultsResponse(BaseModel):
    running: bool
    samples: list[SimulationSample]


class LiveSimulationFrame(BaseModel):
    timestamp: float
    physical_rpm: float
    twin_rpm: float
    physical_current: float
    twin_current: float
    voltage: float
    torque: float
    load_torque: float
    temperature: float
    rpm_error: float
    current_error: float
    twin_accuracy: float
