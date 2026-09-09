"""In-memory MotorTwin session. Uses existing simulation modules only."""

from __future__ import annotations

import math
import threading
from collections.abc import Iterable
from dataclasses import asdict, dataclass, replace

import pandas as pd

from identification.estimator import AdaptationResult, ParameterEstimator
from models.digital_twin import DigitalTwin, TwinMeasurement
from models.motor import MotorParameters, MotorState
from models.parameters import DIGITAL_TWIN_PARAMETERS, PHYSICAL_MOTOR_PARAMETERS
from simulation.physical_motor import PhysicalMotor
from simulation.synchronization import Synchronizer

PLACEHOLDER_TEMPERATURE_C = 25.0
LIVE_HISTORY_LIMIT = 2000
IDENTIFICATION_T_END = 2.0
IDENTIFICATION_DT = 0.02


@dataclass(frozen=True)
class MotorSnapshot:
    rpm: float
    current: float
    voltage: float
    torque: float
    temperature: float
    load_torque: float


@dataclass(frozen=True)
class TwinErrorSnapshot:
    rpm_error: float
    current_error: float
    rpm_rmse: float
    current_rmse: float


class MotorTwinService:
    """Orchestrates the physical motor and Digital Twin for the API."""

    def __init__(self) -> None:
        self.physical = PhysicalMotor(PHYSICAL_MOTOR_PARAMETERS)
        self.twin = DigitalTwin(DIGITAL_TWIN_PARAMETERS)
        self.voltage = 12.0
        self.load_torque = 0.05
        self.running = False
        self.live = False
        self.adaptation_status = "idle"
        self.measurements: pd.DataFrame | None = None
        self.sync_dataset: pd.DataFrame | None = None
        self.last_adaptation: AdaptationResult | None = None
        self.time = 0.0
        self.live_frame: dict[str, float] | None = None
        self.live_history: list[dict[str, float]] = []
        self._lock = threading.RLock()

    def motor_state(self) -> MotorSnapshot:
        with self._lock:
            if self.live_frame is not None:
                return MotorSnapshot(
                    rpm=self.live_frame["physical_rpm"],
                    current=self.live_frame["physical_current"],
                    voltage=self.voltage,
                    torque=self.live_frame["torque"],
                    temperature=PLACEHOLDER_TEMPERATURE_C,
                    load_torque=self.load_torque,
                )
            row = self._last_measurement()
            return MotorSnapshot(
                rpm=float(row["rpm"]) if row is not None else 0.0,
                current=float(row["current"]) if row is not None else 0.0,
                voltage=self.voltage,
                torque=float(row["torque"]) if row is not None else 0.0,
                temperature=PLACEHOLDER_TEMPERATURE_C,
                load_torque=self.load_torque,
            )

    def twin_state(self) -> dict[str, object]:
        with self._lock:
            if self.live_frame is not None:
                rpm = self.live_frame["twin_rpm"]
                current = self.live_frame["twin_current"]
            else:
                prediction = self.twin.predict()
                rpm = prediction.rpm
                current = prediction.current
            error = self._error_snapshot()
            return {
                "rpm": rpm,
                "current": current,
                "voltage": self.voltage,
                "torque": float(self.twin.model.electromagnetic_torque(current)),
                "temperature": PLACEHOLDER_TEMPERATURE_C,
                "error": asdict(error),
                "parameters": asdict(self.twin.params),
                "adaptation_status": self.adaptation_status,
            }

    def start(
        self,
        t_end: float = 2.0,
        dt: float = 0.01,
        voltage: float | None = None,
        load_torque: float | None = None,
    ) -> None:
        with self._lock:
            if voltage is not None:
                self.voltage = voltage
            if load_torque is not None:
                self.load_torque = load_torque

            self.live = False
            self.live_frame = None
            self.live_history = []
            self.running = True
            self.measurements = self.physical.measure(
                voltage=self.voltage,
                load_torque=self.load_torque,
                t_end=t_end,
                dt=dt,
            )
            self.twin.receive_measurements(self.measurements)
            self.twin.simulate()
            self.sync_dataset = Synchronizer(self.twin).run(self.measurements)

    def stop(self) -> None:
        with self._lock:
            self.running = False
            self.live = False

    def begin_live(self) -> None:
        """Reset both plants and start a continuous live session."""
        with self._lock:
            self.physical.reset()
            self.twin.reset()
            self.time = 0.0
            self.live_frame = None
            self.live_history = []
            self.running = True
            self.live = True

    def step_live(self, dt: float) -> dict[str, float] | None:
        """Advance one real-time step. Returns None if the state is invalid."""
        with self._lock:
            if dt <= 0.0 or not math.isfinite(dt):
                return None
            if not math.isfinite(self.voltage) or not math.isfinite(self.load_torque):
                return None

            self.time += dt
            physical = self.physical.step(self.voltage, self.load_torque, dt)
            measurement = TwinMeasurement(
                timestamp=self.time,
                voltage=self.voltage,
                current=physical.current,
                rpm=physical.rpm,
                load_torque=self.load_torque,
            )
            self.twin.receive_measurement(measurement)
            prediction = self.twin.step(self.voltage, self.load_torque, dt)

            values = (
                self.time,
                physical.rpm,
                prediction.rpm,
                physical.current,
                prediction.current,
                physical.torque,
            )
            if not all(math.isfinite(value) for value in values):
                return None

            rpm_error = physical.rpm - prediction.rpm
            current_error = physical.current - prediction.current
            scale = max(abs(physical.rpm), 1.0)
            twin_accuracy = max(0.0, min(1.0, 1.0 - abs(rpm_error) / scale))
            frame = {
                "timestamp": self.time,
                "physical_rpm": physical.rpm,
                "twin_rpm": prediction.rpm,
                "physical_current": physical.current,
                "twin_current": prediction.current,
                "voltage": self.voltage,
                "torque": physical.torque,
                "load_torque": self.load_torque,
                "temperature": PLACEHOLDER_TEMPERATURE_C,
                "rpm_error": rpm_error,
                "current_error": current_error,
                "twin_accuracy": twin_accuracy,
            }
            self.live_frame = frame
            self.live_history.append(frame)
            if len(self.live_history) > LIVE_HISTORY_LIMIT:
                self.live_history = self.live_history[-LIVE_HISTORY_LIMIT:]
            return frame

    def set_control(self, voltage: float, load_torque: float) -> None:
        with self._lock:
            self.voltage = voltage
            self.load_torque = load_torque

    def results(self) -> pd.DataFrame:
        with self._lock:
            if self.live_history:
                return pd.DataFrame(self.live_history)
            if self.sync_dataset is None or self.measurements is None:
                return pd.DataFrame()
            frame = self.sync_dataset.copy()
            frame["voltage"] = self.measurements["voltage"].to_numpy()
            frame["torque"] = self.measurements["torque"].to_numpy()
            frame["temperature"] = PLACEHOLDER_TEMPERATURE_C
            return frame

    def adapt(self, free_params: list[str] | None = None) -> AdaptationResult:
        with self._lock:
            restore_live = self.live
            live_twin_state = replace(self.twin.state) if restore_live else None

            if self.measurements is None:
                self.measurements = self._probe_measurements()

            self.adaptation_status = "running"
            try:
                estimator = ParameterEstimator(free_params or ("J", "b", "R"))
                result = estimator.adapt(self.twin, self.measurements)
                self.twin.receive_measurements(self.measurements)
                self.twin.simulate()
                self.sync_dataset = Synchronizer(self.twin).run(self.measurements)
                if restore_live and live_twin_state is not None:
                    self._restore_live_twin(live_twin_state)
                self.last_adaptation = result
                self.adaptation_status = "completed"
                return result
            except Exception:
                if restore_live and live_twin_state is not None:
                    self._restore_live_twin(live_twin_state)
                self.adaptation_status = "failed"
                raise

    def _probe_measurements(self) -> pd.DataFrame:
        """Collect identification data without moving the live plants."""
        probe = PhysicalMotor(PHYSICAL_MOTOR_PARAMETERS)
        return probe.measure(
            voltage=self.voltage,
            load_torque=self.load_torque,
            t_end=IDENTIFICATION_T_END,
            dt=IDENTIFICATION_DT,
        )

    def _restore_live_twin(self, state: MotorState) -> None:
        """Keep the live session running after batch identification mutates the twin."""
        self.twin.state = state
        self.running = True
        self.live = True

    def _last_measurement(self) -> pd.Series | None:
        if self.measurements is None or self.measurements.empty:
            return None
        return self.measurements.iloc[-1]

    def _error_snapshot(self) -> TwinErrorSnapshot:
        if self.live_history:
            last = self.live_history[-1]
            rpm_rmse = _rmse(row["rpm_error"] for row in self.live_history)
            current_rmse = _rmse(row["current_error"] for row in self.live_history)
            return TwinErrorSnapshot(
                rpm_error=float(last["rpm_error"]),
                current_error=float(last["current_error"]),
                rpm_rmse=rpm_rmse,
                current_rmse=current_rmse,
            )
        if self.sync_dataset is None or self.sync_dataset.empty:
            return TwinErrorSnapshot(0.0, 0.0, 0.0, 0.0)
        last = self.sync_dataset.iloc[-1]
        return TwinErrorSnapshot(
            rpm_error=float(last["rpm_error"]),
            current_error=float(last["current_error"]),
            rpm_rmse=float((self.sync_dataset["rpm_error"] ** 2).mean() ** 0.5),
            current_rmse=float((self.sync_dataset["current_error"] ** 2).mean() ** 0.5),
        )


def _rmse(values: Iterable[float]) -> float:
    errors = list(values)
    if not errors:
        return 0.0
    return float((sum(error * error for error in errors) / len(errors)) ** 0.5)


def parameters_to_dict(params: MotorParameters) -> dict[str, float]:
    return asdict(params)
