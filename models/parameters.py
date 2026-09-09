"""Named parameter sets. Physical and Digital Twin values stay independent."""

from __future__ import annotations

from models.motor import MotorParameters

PHYSICAL_MOTOR_PARAMETERS = MotorParameters(
    R=2.2,
    L=0.5,
    J=0.013,
    b=0.12,
    Kt=0.05,
    Ke=0.05,
)

# Nominal / guessed values for the virtual model. Not used by the physical motor.
DIGITAL_TWIN_PARAMETERS = MotorParameters(
    R=2.0,
    L=0.5,
    J=0.010,
    b=0.10,
    Kt=0.05,
    Ke=0.05,
)
