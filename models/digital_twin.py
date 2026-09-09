"""Virtual DC motor Digital Twin."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from models.comparison import ComparisonResult, compare_measurements
from models.motor import MotorModel, MotorParameters, MotorState
from models.parameters import DIGITAL_TWIN_PARAMETERS
from simulation.integrator import rk4_step
from simulation.physical_motor import to_measurements
from simulation.simulator import RAD_PER_SEC_TO_RPM, Simulator


@dataclass(frozen=True)
class TwinMeasurement:
    """One physical-motor sample received by the Digital Twin."""

    timestamp: float
    voltage: float
    current: float
    rpm: float
    load_torque: float

    @classmethod
    def from_row(cls, row: pd.Series) -> TwinMeasurement:
        return cls(
            timestamp=float(row["timestamp"]),
            voltage=float(row["voltage"]),
            current=float(row["current"]),
            rpm=float(row["rpm"]),
            load_torque=float(row["load_torque"]),
        )


@dataclass(frozen=True)
class TwinPrediction:
    """Virtual-motor output at one synchronization step."""

    current: float
    rpm: float
    omega: float


class DigitalTwin:
    """Virtual replica with its own model, state, and parameters."""

    def __init__(self, params: MotorParameters | None = None) -> None:
        self.params = params or DIGITAL_TWIN_PARAMETERS
        self.model = MotorModel(self.params)
        self.state = MotorState()
        self.last_measurement: TwinMeasurement | None = None
        self.measurements: pd.DataFrame | None = None
        self.prediction: pd.DataFrame | None = None
        self._simulator = Simulator(self.model)

    def reset(self) -> None:
        """Return the virtual motor to rest."""
        self.state = MotorState()
        self.last_measurement = None

    def update_parameters(self, params: MotorParameters) -> None:
        """Replace the virtual-model parameters and rebuild the simulator."""
        self.params = params
        self.model = MotorModel(params)
        self._simulator = Simulator(self.model)
        self.reset()

    def receive_measurement(self, measurement: TwinMeasurement) -> None:
        """Receive one physical measurement."""
        self.last_measurement = measurement

    def receive_measurements(self, measurements: pd.DataFrame) -> None:
        """Store a batch of physical-motor measurements for later comparison."""
        self.measurements = measurements.copy()

    def predict(self) -> TwinPrediction:
        """Return the current virtual state as a prediction."""
        return TwinPrediction(
            current=self.state.current,
            rpm=self.state.omega * RAD_PER_SEC_TO_RPM,
            omega=self.state.omega,
        )

    def step(self, voltage: float, load_torque: float, dt: float) -> TwinPrediction:
        """Advance the virtual motor one time step and return the prediction."""
        if dt > 0.0:
            self.state = rk4_step(self.model, self.state, voltage, load_torque, dt)
        return self.predict()

    def simulate(
        self,
        voltage: float | None = None,
        load_torque: float | None = None,
        t_end: float | None = None,
        t_start: float = 0.0,
        dt: float | None = None,
        initial_state: MotorState | None = None,
    ) -> pd.DataFrame:
        """Simulate the virtual motor. Missing inputs are taken from measurements."""
        voltage, load_torque, t_end, t_start, dt = self._resolve_inputs(
            voltage, load_torque, t_end, t_start, dt
        )
        if initial_state is not None:
            state0 = initial_state
        elif self.measurements is not None:
            state0 = MotorState()
        else:
            state0 = self.state

        results = self._simulator.run(
            initial_state=state0,
            voltage=voltage,
            load_torque=load_torque,
            t_end=t_end,
            t_start=t_start,
            dt=dt,
        )
        self.prediction = to_measurements(results)
        last = self.prediction.iloc[-1]
        self.state = MotorState(
            current=float(last["current"]),
            omega=float(last["angular_velocity"]),
        )
        return self.prediction

    def compare(self) -> ComparisonResult:
        """Compare stored physical measurements with the latest virtual prediction."""
        if self.measurements is None:
            raise ValueError("No physical measurements received.")
        if self.prediction is None:
            raise ValueError("No virtual prediction available. Call simulate() first.")
        return compare_measurements(self.measurements, self.prediction)

    def _resolve_inputs(
        self,
        voltage: float | None,
        load_torque: float | None,
        t_end: float | None,
        t_start: float,
        dt: float | None,
    ) -> tuple[float, float, float, float, float]:
        if None in (voltage, load_torque, t_end, dt):
            if self.measurements is None:
                raise ValueError("Provide simulation inputs or receive measurements first.")
            measured = self.measurements
            voltage = float(measured["voltage"].iloc[0]) if voltage is None else voltage
            load_torque = (
                float(measured["load_torque"].iloc[0]) if load_torque is None else load_torque
            )
            t_start = float(measured["timestamp"].iloc[0]) if t_start == 0.0 else t_start
            t_end = float(measured["timestamp"].iloc[-1]) if t_end is None else t_end
            if dt is None:
                dt = float(measured["timestamp"].iloc[1] - measured["timestamp"].iloc[0])
        assert voltage is not None and load_torque is not None
        assert t_end is not None and dt is not None
        return voltage, load_torque, t_end, t_start, dt
