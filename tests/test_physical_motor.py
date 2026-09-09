"""Tests for the simulated physical motor."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.parameters import DIGITAL_TWIN_PARAMETERS, PHYSICAL_MOTOR_PARAMETERS
from models.motor import MotorState
from simulation.physical_motor import MEASUREMENT_COLUMNS, PhysicalMotor


class PhysicalMotorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.motor = PhysicalMotor()

    def test_uses_physical_parameter_set(self) -> None:
        self.assertEqual(self.motor.params, PHYSICAL_MOTOR_PARAMETERS)
        self.assertNotEqual(self.motor.params, DIGITAL_TWIN_PARAMETERS)

    def test_parameter_sets_are_independent(self) -> None:
        self.assertEqual(PHYSICAL_MOTOR_PARAMETERS.R, 2.2)
        self.assertEqual(DIGITAL_TWIN_PARAMETERS.R, 2.0)

    def test_measurement_columns(self) -> None:
        measurements = self.motor.measure(t_end=0.2, dt=0.01)
        self.assertEqual(tuple(measurements.columns), MEASUREMENT_COLUMNS)

    def test_starts_from_rest_with_12v_and_constant_load(self) -> None:
        measurements = self.motor.measure(
            voltage=12.0,
            load_torque=0.05,
            t_end=0.5,
            dt=0.01,
            initial_state=MotorState(),
        )
        self.assertAlmostEqual(measurements["timestamp"].iloc[0], 0.0)
        self.assertAlmostEqual(measurements["current"].iloc[0], 0.0, places=6)
        self.assertAlmostEqual(measurements["angular_velocity"].iloc[0], 0.0, places=6)
        self.assertTrue(np.allclose(measurements["voltage"], 12.0))
        self.assertTrue(np.allclose(measurements["load_torque"], 0.05))

    def test_torque_is_electromagnetic(self) -> None:
        measurements = self.motor.measure(voltage=12.0, t_end=0.3, dt=0.01)
        np.testing.assert_allclose(
            measurements["torque"].to_numpy(),
            PHYSICAL_MOTOR_PARAMETERS.Kt * measurements["current"].to_numpy(),
        )


if __name__ == "__main__":
    unittest.main()
