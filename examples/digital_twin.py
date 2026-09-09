"""Compare the physical motor with a Digital Twin that has incorrect parameters."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.digital_twin import DigitalTwin
from models.motor import MotorState
from simulation.physical_motor import PhysicalMotor
from visualization.plots import plot_physical_vs_twin


def run_twin_comparison() -> Path:
    physical = PhysicalMotor()
    twin = DigitalTwin()

    measurements = physical.measure(
        voltage=12.0,
        load_torque=0.05,
        t_end=5.0,
        initial_state=MotorState(),
    )
    twin.receive_measurements(measurements)
    prediction = twin.simulate()
    comparison = twin.compare()

    output_dir = ROOT / "outputs"
    output_dir.mkdir(exist_ok=True)
    plot_path = output_dir / "physical_vs_twin.png"
    plot_physical_vs_twin(measurements, prediction, save_path=plot_path)

    print("Physical parameters:", physical.params)
    print("Digital Twin parameters:", twin.params)
    print()
    print(comparison.summary())
    print(f"\nComparison plot saved to {plot_path}")
    return plot_path


if __name__ == "__main__":
    run_twin_comparison()
