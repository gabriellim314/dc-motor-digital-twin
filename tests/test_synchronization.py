"""Tests for physical–Digital Twin synchronization."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.digital_twin import DigitalTwin, TwinMeasurement
from models.parameters import DIGITAL_TWIN_PARAMETERS, PHYSICAL_MOTOR_PARAMETERS
from simulation.physical_motor import PhysicalMotor
from simulation.synchronization import SYNC_COLUMNS, Synchronizer


class SynchronizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.physical = PhysicalMotor()
        self.twin = DigitalTwin()
        self.measurements = self.physical.measure(
            voltage=12.0,
            load_torque=0.05,
            t_end=0.5,
            dt=0.01,
        )
        self.dataset = Synchronizer(self.twin).run(self.measurements)

    def test_dataset_columns_and_length(self) -> None:
        self.assertEqual(tuple(self.dataset.columns), SYNC_COLUMNS)
        self.assertEqual(len(self.dataset), len(self.measurements))

    def test_starts_at_rest_with_zero_error(self) -> None:
        first = self.dataset.iloc[0]
        self.assertAlmostEqual(first["timestamp"], 0.0)
        self.assertAlmostEqual(first["physical_rpm"], 0.0, places=6)
        self.assertAlmostEqual(first["twin_rpm"], 0.0, places=6)
        self.assertAlmostEqual(first["rpm_error"], 0.0, places=6)
        self.assertAlmostEqual(first["current_error"], 0.0, places=6)

    def test_error_is_physical_minus_twin(self) -> None:
        np.testing.assert_allclose(
            self.dataset["rpm_error"],
            self.dataset["physical_rpm"] - self.dataset["twin_rpm"],
        )
        np.testing.assert_allclose(
            self.dataset["current_error"],
            self.dataset["physical_current"] - self.dataset["twin_current"],
        )

    def test_parameter_mismatch_creates_error(self) -> None:
        self.assertNotEqual(PHYSICAL_MOTOR_PARAMETERS, DIGITAL_TWIN_PARAMETERS)
        self.assertGreater(float((self.dataset["rpm_error"] ** 2).mean()), 0.0)
        self.assertGreater(float((self.dataset["current_error"] ** 2).mean()), 0.0)

    def test_single_step_receives_measurement(self) -> None:
        twin = DigitalTwin()
        sync = Synchronizer(twin)
        measurement = TwinMeasurement(
            timestamp=0.01,
            voltage=12.0,
            current=0.1,
            rpm=1.0,
            load_torque=0.05,
        )
        record = sync.step(measurement, dt=0.01)
        self.assertEqual(twin.last_measurement, measurement)
        self.assertEqual(record.timestamp, 0.01)
        self.assertEqual(len(sync.history), 1)


if __name__ == "__main__":
    unittest.main()
