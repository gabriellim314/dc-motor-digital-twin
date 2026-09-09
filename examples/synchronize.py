"""Synchronize the physical motor with the Digital Twin, step by step."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.digital_twin import DigitalTwin
from models.motor import MotorState
from simulation.physical_motor import PhysicalMotor
from simulation.synchronization import Synchronizer
from visualization.plots import plot_sync_dataset


def run_synchronization() -> Path:
    physical = PhysicalMotor()
    measurements = physical.measure(
        voltage=12.0,
        load_torque=0.05,
        t_end=5.0,
        initial_state=MotorState(),
    )

    dataset = Synchronizer(DigitalTwin()).run(measurements)

    output_dir = ROOT / "outputs"
    output_dir.mkdir(exist_ok=True)
    csv_path = output_dir / "sync_dataset.csv"
    plot_path = output_dir / "sync_physical_vs_twin.png"
    dataset.to_csv(csv_path, index=False)
    plot_sync_dataset(dataset, save_path=plot_path)

    print(dataset.head())
    print()
    print(dataset.tail())
    print(f"\nRMSE rpm: {(dataset['rpm_error'] ** 2).mean() ** 0.5:.4f}")
    print(f"RMSE current: {(dataset['current_error'] ** 2).mean() ** 0.5:.4f}")
    print(f"\nSaved dataset to {csv_path}")
    print(f"Saved plot to {plot_path}")
    return csv_path


if __name__ == "__main__":
    run_synchronization()
