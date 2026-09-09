"""Tests for the Digital Twin and comparison metrics."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.comparison import compare_measurements
from models.digital_twin import DigitalTwin
from models.parameters import DIGITAL_TWIN_PARAMETERS, PHYSICAL_MOTOR_PARAMETERS
from simulation.physical_motor import PhysicalMotor


class DigitalTwinTests(unittest.TestCase):
    def test_parameters_are_independent(self) -> None:
        twin = DigitalTwin()
        physical = PhysicalMotor()
        self.assertEqual(twin.params, DIGITAL_TWIN_PARAMETERS)
        self.assertEqual(physical.params, PHYSICAL_MOTOR_PARAMETERS)
        self.assertNotEqual(twin.params, physical.params)
        self.assertIsNot(twin.model, physical.model)

    def test_receive_and_simulate_then_compare(self) -> None:
        physical = PhysicalMotor()
        twin = DigitalTwin()
        measurements = physical.measure(voltage=12.0, load_torque=0.05, t_end=0.5, dt=0.01)
        twin.receive_measurements(measurements)
        prediction = twin.simulate()

        self.assertEqual(list(prediction.columns), list(measurements.columns))
        self.assertEqual(len(prediction), len(measurements))
        comparison = twin.compare()
        self.assertGreater(comparison.rpm.rmse, 0.0)
        self.assertGreater(comparison.current.rmse, 0.0)

    def test_compare_requires_measurements_and_prediction(self) -> None:
        twin = DigitalTwin()
        with self.assertRaises(ValueError):
            twin.compare()
        twin.receive_measurements(
            PhysicalMotor().measure(t_end=0.2, dt=0.01)
        )
        with self.assertRaises(ValueError):
            twin.compare()


class ComparisonTests(unittest.TestCase):
    def test_identical_series_have_zero_error(self) -> None:
        frame = pd.DataFrame(
            {
                "timestamp": [0.0, 0.1, 0.2],
                "rpm": [0.0, 10.0, 20.0],
                "current": [0.0, 1.0, 2.0],
            }
        )
        result = compare_measurements(frame, frame)
        self.assertAlmostEqual(result.rpm.rmse, 0.0)
        self.assertAlmostEqual(result.current.rmse, 0.0)
        np.testing.assert_allclose(result.rpm.absolute_error, 0.0)
        np.testing.assert_allclose(result.current.relative_error, 0.0)

    def test_known_rmse(self) -> None:
        physical = pd.DataFrame({"timestamp": [0.0, 1.0], "rpm": [0.0, 4.0], "current": [1.0, 1.0]})
        virtual = pd.DataFrame({"timestamp": [0.0, 1.0], "rpm": [0.0, 1.0], "current": [1.0, 3.0]})
        result = compare_measurements(physical, virtual)
        self.assertAlmostEqual(result.rpm.rmse, np.sqrt((0.0**2 + 3.0**2) / 2))
        self.assertAlmostEqual(result.current.rmse, np.sqrt((0.0**2 + (-2.0) ** 2) / 2))


if __name__ == "__main__":
    unittest.main()
