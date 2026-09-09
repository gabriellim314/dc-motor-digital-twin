"""Tests for classical Digital Twin parameter estimation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from identification.estimator import ParameterEstimator
from models.digital_twin import DigitalTwin
from models.parameters import DIGITAL_TWIN_PARAMETERS, PHYSICAL_MOTOR_PARAMETERS
from simulation.physical_motor import PhysicalMotor


class ParameterEstimatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.measurements = PhysicalMotor().measure(
            voltage=12.0,
            load_torque=0.05,
            t_end=1.5,
            dt=0.02,
        )
        cls.estimator = ParameterEstimator(free_params=("J", "b", "R"))

    def test_objective_is_small_at_true_parameters(self) -> None:
        x_true = np.array(
            [
                PHYSICAL_MOTOR_PARAMETERS.J,
                PHYSICAL_MOTOR_PARAMETERS.b,
                PHYSICAL_MOTOR_PARAMETERS.R,
            ]
        )
        cost = self.estimator.objective(x_true, PHYSICAL_MOTOR_PARAMETERS, self.measurements)
        self.assertLess(cost, 0.05)

    def test_estimate_moves_towards_physical_values(self) -> None:
        estimated = self.estimator.estimate(self.measurements, DIGITAL_TWIN_PARAMETERS)
        for name in ("J", "b", "R"):
            initial = getattr(DIGITAL_TWIN_PARAMETERS, name)
            true = getattr(PHYSICAL_MOTOR_PARAMETERS, name)
            fitted = getattr(estimated, name)
            self.assertLess(abs(fitted - true), abs(initial - true))

    def test_fixed_parameters_stay_unchanged(self) -> None:
        estimated = self.estimator.estimate(self.measurements, DIGITAL_TWIN_PARAMETERS)
        self.assertAlmostEqual(estimated.Kt, DIGITAL_TWIN_PARAMETERS.Kt)
        self.assertAlmostEqual(estimated.Ke, DIGITAL_TWIN_PARAMETERS.Ke)
        self.assertAlmostEqual(estimated.L, DIGITAL_TWIN_PARAMETERS.L)

    def test_adaptation_reduces_rpm_rmse(self) -> None:
        twin = DigitalTwin(DIGITAL_TWIN_PARAMETERS)
        result = self.estimator.adapt(twin, self.measurements)
        self.assertLess(result.after.rpm.rmse, result.before.rpm.rmse)
        self.assertEqual(twin.params, result.estimated_params)


if __name__ == "__main__":
    unittest.main()
