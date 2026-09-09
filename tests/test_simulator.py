"""Unit tests for the DC motor numerical simulator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.motor import MotorModel, MotorParameters, MotorState
from simulation.simulator import RAD_PER_SEC_TO_RPM, SimulationConfig, Simulator, simulate


class SimulatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = MotorParameters()
        self.motor = MotorModel(self.params)
        self.simulator = Simulator(self.motor)

    def test_output_columns(self) -> None:
        results = self.simulator.run(t_end=0.2, dt=0.01)
        self.assertEqual(
            list(results.columns),
            ["time", "current", "omega", "rpm", "torque_em", "voltage", "load_torque"],
        )

    def test_starts_at_rest(self) -> None:
        results = self.simulator.run(
            initial_state=MotorState(),
            voltage=12.0,
            load_torque=0.05,
            t_end=0.2,
            dt=0.01,
        )
        self.assertAlmostEqual(results["current"].iloc[0], 0.0, places=6)
        self.assertAlmostEqual(results["omega"].iloc[0], 0.0, places=6)
        self.assertAlmostEqual(results["rpm"].iloc[0], 0.0, places=6)

    def test_time_span(self) -> None:
        results = self.simulator.run(t_start=0.0, t_end=1.0, dt=0.01)
        self.assertAlmostEqual(results["time"].iloc[0], 0.0)
        self.assertAlmostEqual(results["time"].iloc[-1], 1.0)

    def test_rpm_matches_omega(self) -> None:
        results = self.simulator.run(voltage=12.0, t_end=0.5, dt=0.01)
        np.testing.assert_allclose(
            results["rpm"].to_numpy(),
            results["omega"].to_numpy() * RAD_PER_SEC_TO_RPM,
        )

    def test_electromagnetic_torque(self) -> None:
        results = self.simulator.run(voltage=12.0, t_end=0.5, dt=0.01)
        np.testing.assert_allclose(
            results["torque_em"].to_numpy(),
            self.params.Kt * results["current"].to_numpy(),
        )

    def test_voltage_increases_speed(self) -> None:
        results = self.simulator.run(voltage=12.0, load_torque=0.05, t_end=2.0)
        self.assertGreater(results["rpm"].iloc[-1], results["rpm"].iloc[0])

    def test_load_reduces_steady_speed(self) -> None:
        no_load = self.simulator.run(voltage=12.0, load_torque=0.0, t_end=3.0)
        loaded = self.simulator.run(voltage=12.0, load_torque=0.05, t_end=3.0)
        self.assertGreater(no_load["rpm"].iloc[-1], loaded["rpm"].iloc[-1])

    def test_simulate_wrapper_matches_run(self) -> None:
        config = SimulationConfig(voltage=12.0, load_torque=0.05, t_end=0.3, dt=0.01)
        from_wrapper = simulate(self.motor, config)
        from_run = self.simulator.run(
            initial_state=config.initial_state,
            voltage=config.voltage,
            load_torque=config.load_torque,
            t_end=config.t_end,
            dt=config.dt,
        )
        np.testing.assert_allclose(from_wrapper["rpm"], from_run["rpm"])


if __name__ == "__main__":
    unittest.main()
