"""Simulated physical motor: the reference plant that produces measurements."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from models.motor import MotorModel, MotorParameters, MotorState
from models.parameters import PHYSICAL_MOTOR_PARAMETERS
from simulation.integrator import rk4_step
from simulation.simulator import RAD_PER_SEC_TO_RPM, Simulator

MEASUREMENT_COLUMNS = (
    "timestamp",
    "voltage",
    "current",
    "rpm",
    "angular_velocity",
    "torque",
    "load_torque",
)


def to_measurements(results: pd.DataFrame) -> pd.DataFrame:
    """Map simulator output to the physical-measurement schema."""
    return pd.DataFrame(
        {
            "timestamp": results["time"],
            "voltage": results["voltage"],
            "current": results["current"],
            "rpm": results["rpm"],
            "angular_velocity": results["omega"],
            "torque": results["torque_em"],
            "load_torque": results["load_torque"],
        }
    )


@dataclass(frozen=True)
class PhysicalSample:
    """One incremental physical-motor sample."""

    current: float
    rpm: float
    omega: float
    torque: float


class PhysicalMotor:
    """Reference DC motor with its own parameters, used as a simulated plant."""

    def __init__(self, params: MotorParameters | None = None) -> None:
        self.params = params or PHYSICAL_MOTOR_PARAMETERS
        self.model = MotorModel(self.params)
        self.state = MotorState()
        self._simulator = Simulator(self.model)

    def reset(self) -> None:
        self.state = MotorState()

    def step(self, voltage: float, load_torque: float, dt: float) -> PhysicalSample:
        """Advance the physical motor one RK4 step."""
        if dt > 0.0:
            self.state = rk4_step(self.model, self.state, voltage, load_torque, dt)
        return PhysicalSample(
            current=self.state.current,
            rpm=self.state.omega * RAD_PER_SEC_TO_RPM,
            omega=self.state.omega,
            torque=float(self.model.electromagnetic_torque(self.state.current)),
        )

    def measure(
        self,
        voltage: float = 12.0,
        load_torque: float = 0.05,
        t_end: float = 5.0,
        t_start: float = 0.0,
        dt: float = 0.001,
        initial_state: MotorState | None = None,
    ) -> pd.DataFrame:
        """Run the physical motor and return a measurement DataFrame."""
        results = self._simulator.run(
            initial_state=initial_state or MotorState(),
            voltage=voltage,
            load_torque=load_torque,
            t_end=t_end,
            t_start=t_start,
            dt=dt,
        )
        measured = to_measurements(results)
        last = measured.iloc[-1]
        self.state = MotorState(current=float(last["current"]), omega=float(last["angular_velocity"]))
        return measured
