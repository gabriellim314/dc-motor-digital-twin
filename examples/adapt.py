"""Estimate J, b, and R, then compare the Digital Twin before and after."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from identification.estimator import ParameterEstimator
from models.digital_twin import DigitalTwin
from models.motor import MotorState
from models.parameters import DIGITAL_TWIN_PARAMETERS, PHYSICAL_MOTOR_PARAMETERS
from simulation.physical_motor import PhysicalMotor
from visualization.plots import plot_adaptation


def run_adaptation() -> Path:
    physical = PhysicalMotor()
    measurements = physical.measure(
        voltage=12.0,
        load_torque=0.05,
        t_end=5.0,
        dt=0.01,
        initial_state=MotorState(),
    )

    twin = DigitalTwin(DIGITAL_TWIN_PARAMETERS)
    twin.receive_measurements(measurements)
    before_prediction = twin.simulate().copy()

    result = ParameterEstimator(free_params=("J", "b", "R")).adapt(
        twin,
        measurements,
        physical_params=PHYSICAL_MOTOR_PARAMETERS,
    )
    after_prediction = twin.prediction
    assert after_prediction is not None

    output_dir = ROOT / "outputs"
    output_dir.mkdir(exist_ok=True)
    plot_path = output_dir / "adaptation.png"
    plot_adaptation(measurements, before_prediction, after_prediction, save_path=plot_path)

    print(result.report())
    print(f"\nAdaptation plot saved to {plot_path}")
    return plot_path


if __name__ == "__main__":
    run_adaptation()
