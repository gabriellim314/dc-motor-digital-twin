"""Example: start at rest, apply 12 V and a constant load, simulate 5 s."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.motor import MotorModel, MotorParameters, MotorState
from simulation.simulator import Simulator
from visualization.plots import plot_rpm_and_current


def run_example() -> Path:
    motor = MotorModel(MotorParameters())
    results = Simulator(motor).run(
        initial_state=MotorState(current=0.0, omega=0.0),
        voltage=12.0,
        load_torque=0.05,
        t_end=5.0,
    )

    output_dir = ROOT / "outputs"
    output_dir.mkdir(exist_ok=True)
    plot_path = output_dir / "step_response.png"
    plot_rpm_and_current(results, save_path=plot_path)

    print(results[["time", "current", "rpm", "torque_em"]].tail())
    print(f"\nPlot saved to {plot_path}")
    return plot_path


if __name__ == "__main__":
    run_example()
