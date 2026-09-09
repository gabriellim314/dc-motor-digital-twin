"""Physical-motor scenario: rest, 12 V, constant load, measurement DataFrame."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.motor import MotorState
from simulation.physical_motor import PhysicalMotor


def run_physical_scenario() -> pd.DataFrame:
    motor = PhysicalMotor()
    measurements = motor.measure(
        voltage=12.0,
        load_torque=0.05,
        t_end=5.0,
        initial_state=MotorState(current=0.0, omega=0.0),
    )

    output_dir = ROOT / "outputs"
    output_dir.mkdir(exist_ok=True)
    csv_path = output_dir / "physical_measurements.csv"
    measurements.to_csv(csv_path, index=False)

    print(measurements.head())
    print()
    print(measurements.tail())
    print(f"\nSaved {len(measurements)} samples to {csv_path}")
    return measurements


if __name__ == "__main__":
    run_physical_scenario()
