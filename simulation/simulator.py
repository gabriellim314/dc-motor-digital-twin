"""Time-domain simulation of the DC motor model."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from models.motor import MotorModel, MotorState

RAD_PER_SEC_TO_RPM = 60.0 / (2.0 * np.pi)


@dataclass(frozen=True)
class SimulationConfig:
    """Inputs and time grid for a single simulation run."""

    t_start: float = 0.0
    t_end: float = 5.0
    dt: float = 0.001
    voltage: float = 12.0
    load_torque: float = 0.0
    initial_state: MotorState = field(default_factory=MotorState)


class Simulator:
    """Integrate a MotorModel with SciPy's solve_ivp."""

    def __init__(self, motor: MotorModel) -> None:
        self.motor = motor

    def run(
        self,
        initial_state: MotorState | None = None,
        voltage: float = 12.0,
        load_torque: float = 0.0,
        t_end: float = 5.0,
        t_start: float = 0.0,
        dt: float = 0.001,
    ) -> pd.DataFrame:
        """Simulate the motor and return states plus derived quantities."""
        state0 = initial_state or MotorState()
        t_eval = np.arange(t_start, t_end + dt, dt)

        solution = solve_ivp(
            fun=lambda t, y: self.motor.dynamics(t, y, voltage, load_torque),
            t_span=(t_start, t_end),
            y0=state0.as_array(),
            t_eval=t_eval,
            method="RK45",
        )

        if not solution.success:
            raise RuntimeError(f"Simulation failed: {solution.message}")

        current = solution.y[0]
        omega = solution.y[1]
        return pd.DataFrame(
            {
                "time": solution.t,
                "current": current,
                "omega": omega,
                "rpm": omega * RAD_PER_SEC_TO_RPM,
                "torque_em": self.motor.electromagnetic_torque(current),
                "voltage": np.full_like(solution.t, voltage),
                "load_torque": np.full_like(solution.t, load_torque),
            }
        )


def simulate(motor: MotorModel, config: SimulationConfig) -> pd.DataFrame:
    """Run a simulation from a SimulationConfig."""
    return Simulator(motor).run(
        initial_state=config.initial_state,
        voltage=config.voltage,
        load_torque=config.load_torque,
        t_end=config.t_end,
        t_start=config.t_start,
        dt=config.dt,
    )
