"""Shared single-step integrator used by the physical motor and Digital Twin."""

from __future__ import annotations

from models.motor import MotorModel, MotorState


def rk4_step(
    model: MotorModel,
    state: MotorState,
    voltage: float,
    load_torque: float,
    dt: float,
) -> MotorState:
    """Advance one RK4 step of the existing motor ODEs."""

    def deriv(current: MotorState) -> MotorState:
        return model.derivatives(current, voltage, load_torque)

    k1 = deriv(state)
    k2 = deriv(
        MotorState(
            current=state.current + 0.5 * dt * k1.current,
            omega=state.omega + 0.5 * dt * k1.omega,
        )
    )
    k3 = deriv(
        MotorState(
            current=state.current + 0.5 * dt * k2.current,
            omega=state.omega + 0.5 * dt * k2.omega,
        )
    )
    k4 = deriv(
        MotorState(
            current=state.current + dt * k3.current,
            omega=state.omega + dt * k3.omega,
        )
    )
    return MotorState(
        current=state.current + (dt / 6.0) * (k1.current + 2.0 * k2.current + 2.0 * k3.current + k4.current),
        omega=state.omega + (dt / 6.0) * (k1.omega + 2.0 * k2.omega + 2.0 * k3.omega + k4.omega),
    )
