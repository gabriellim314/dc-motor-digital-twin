"""Mathematical model of a brushed DC motor.

Electrical:
    V = R * i + L * di/dt + Ke * ω
    ⇒  di/dt = (V - R * i - Ke * ω) / L

Mechanical:
    J * dω/dt = Kt * i - b * ω - T_load
    ⇒  dω/dt = (Kt * i - b * ω - T_load) / J
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class MotorParameters:
    """Physical parameters of a DC motor."""

    R: float = 1.0  # armature resistance [Ohm]
    L: float = 0.5  # armature inductance [H]
    J: float = 0.01  # rotor inertia [kg·m²]
    b: float = 0.1  # viscous friction [N·m·s/rad]
    Ke: float = 0.01  # back-EMF constant [V·s/rad]
    Kt: float = 0.01  # torque constant [N·m/A]


@dataclass(frozen=True)
class MotorState:
    """Motor state: armature current and angular velocity."""

    current: float = 0.0  # [A]
    omega: float = 0.0  # [rad/s]

    def as_array(self) -> NDArray[np.float64]:
        return np.array([self.current, self.omega], dtype=float)

    @classmethod
    def from_array(cls, state: NDArray[np.floating]) -> MotorState:
        return cls(current=float(state[0]), omega=float(state[1]))


class MotorModel:
    """First-principles DC motor used as the simulation plant."""

    def __init__(self, params: MotorParameters | None = None) -> None:
        self.params = params or MotorParameters()

    def derivatives(
        self,
        state: MotorState,
        voltage: float,
        load_torque: float = 0.0,
    ) -> MotorState:
        """Return [di/dt, dω/dt] for the given state and inputs."""
        p = self.params
        di_dt = (voltage - p.R * state.current - p.Ke * state.omega) / p.L
        domega_dt = (p.Kt * state.current - p.b * state.omega - load_torque) / p.J
        return MotorState(current=di_dt, omega=domega_dt)

    def electromagnetic_torque(self, current: NDArray[np.float64] | float) -> NDArray[np.float64] | float:
        """Electromagnetic torque Te = Kt * i."""
        return self.params.Kt * current

    def dynamics(
        self,
        _t: float,
        state: NDArray[np.float64],
        voltage: float,
        load_torque: float = 0.0,
    ) -> NDArray[np.float64]:
        """SciPy-compatible right-hand side: dy/dt = f(t, y, u)."""
        return self.derivatives(
            MotorState.from_array(state),
            voltage=voltage,
            load_torque=load_torque,
        ).as_array()
