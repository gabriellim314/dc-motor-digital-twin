"""Unit tests for the DC motor electrical and mechanical equations."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.motor import MotorModel, MotorParameters, MotorState
from simulation.simulator import SimulationConfig, simulate


class MotorEquationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = MotorParameters(R=2.0, L=0.5, J=0.02, b=0.1, Ke=0.5, Kt=0.2)
        self.motor = MotorModel(self.params)

    def test_electrical_derivative(self) -> None:
        # di/dt = (V - R*i - Ke*ω) / L = (10 - 2*1 - 0.5*4) / 0.5 = 12
        derivatives = self.motor.derivatives(
            MotorState(current=1.0, omega=4.0),
            voltage=10.0,
        )
        self.assertAlmostEqual(derivatives.current, 12.0)

    def test_mechanical_derivative(self) -> None:
        # dω/dt = (Kt*i - b*ω - T_load) / J = (0.2*3 - 0.1*5 - 0.1) / 0.02 = 0
        derivatives = self.motor.derivatives(
            MotorState(current=3.0, omega=5.0),
            voltage=0.0,
            load_torque=0.1,
        )
        self.assertAlmostEqual(derivatives.omega, 0.0)

    def test_rest_and_zero_input_gives_zero_derivatives(self) -> None:
        derivatives = self.motor.derivatives(MotorState(), voltage=0.0)
        self.assertAlmostEqual(derivatives.current, 0.0)
        self.assertAlmostEqual(derivatives.omega, 0.0)

    def test_voltage_at_rest_charges_inductance(self) -> None:
        # At i = 0, ω = 0: di/dt = V / L, dω/dt = 0
        derivatives = self.motor.derivatives(MotorState(), voltage=12.0)
        self.assertAlmostEqual(derivatives.current, 12.0 / self.params.L)
        self.assertAlmostEqual(derivatives.omega, 0.0)

    def test_load_torque_decelerates_rotor(self) -> None:
        derivatives = self.motor.derivatives(
            MotorState(),
            voltage=0.0,
            load_torque=0.1,
        )
        self.assertAlmostEqual(derivatives.omega, -0.1 / self.params.J)


class MotorSimulationInterfaceTests(unittest.TestCase):
    def test_dynamics_matches_derivatives(self) -> None:
        motor = MotorModel()
        state = MotorState(current=0.5, omega=1.0)
        expected = motor.derivatives(state, voltage=6.0, load_torque=0.02)
        actual = motor.dynamics(0.0, state.as_array(), voltage=6.0, load_torque=0.02)
        np.testing.assert_allclose(actual, expected.as_array())

    def test_state_roundtrip(self) -> None:
        state = MotorState(current=1.5, omega=-0.3)
        restored = MotorState.from_array(state.as_array())
        self.assertEqual(restored, state)

    def test_simulation_step_increases_speed(self) -> None:
        results = simulate(MotorModel(), SimulationConfig(voltage=12.0, t_end=1.0))
        self.assertGreater(results["omega"].iloc[-1], results["omega"].iloc[0])
        self.assertTrue(np.isfinite(results[["current", "omega"]].to_numpy()).all())


if __name__ == "__main__":
    unittest.main()
