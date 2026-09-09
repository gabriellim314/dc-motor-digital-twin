"""Classical parameter estimation for the Digital Twin (scipy.optimize)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.optimize import least_squares

from models.comparison import ComparisonResult, compare_measurements
from models.digital_twin import DigitalTwin
from models.motor import MotorModel, MotorParameters
from models.parameters import PHYSICAL_MOTOR_PARAMETERS
from simulation.physical_motor import to_measurements
from simulation.simulator import Simulator

DEFAULT_FREE_PARAMS = ("J", "b", "R")


@dataclass(frozen=True)
class AdaptationResult:
    """Before/after comparison produced by parameter adaptation."""

    initial_params: MotorParameters
    estimated_params: MotorParameters
    physical_params: MotorParameters
    before: ComparisonResult
    after: ComparisonResult

    def report(self) -> str:
        return (
            "Before adaptation:\n"
            f"RPM RMSE = {self.before.rpm.rmse:.4f}\n"
            f"Current RMSE = {self.before.current.rmse:.4f}\n\n"
            "After adaptation:\n"
            f"RPM RMSE = {self.after.rpm.rmse:.4f}\n"
            f"Current RMSE = {self.after.current.rmse:.4f}\n\n"
            f"Initial parameters:   {self.initial_params}\n"
            f"Estimated parameters: {self.estimated_params}\n"
            f"Physical parameters:  {self.physical_params}"
        )


class ParameterEstimator:
    """Estimate selected motor parameters by minimizing prediction error."""

    def __init__(self, free_params: Sequence[str] = DEFAULT_FREE_PARAMS) -> None:
        self.free_params = tuple(free_params)

    def simulate_candidate(
        self,
        params: MotorParameters,
        measurements: pd.DataFrame,
    ) -> pd.DataFrame:
        """Run the virtual motor with candidate parameters on the measured inputs."""
        voltage = float(measurements["voltage"].iloc[0])
        load_torque = float(measurements["load_torque"].iloc[0])
        t_start = float(measurements["timestamp"].iloc[0])
        t_end = float(measurements["timestamp"].iloc[-1])
        dt = float(measurements["timestamp"].iloc[1] - measurements["timestamp"].iloc[0])
        results = Simulator(MotorModel(params)).run(
            voltage=voltage,
            load_torque=load_torque,
            t_start=t_start,
            t_end=t_end,
            dt=dt,
        )
        return to_measurements(results)

    def residuals(
        self,
        x: NDArray[np.float64],
        guess: MotorParameters,
        measurements: pd.DataFrame,
    ) -> NDArray[np.float64]:
        """Stacked, scaled RPM and current errors for candidate parameters x."""
        params = replace(guess, **dict(zip(self.free_params, x, strict=True)))
        virtual = self.simulate_candidate(params, measurements)

        rpm_error = measurements["rpm"].to_numpy() - virtual["rpm"].to_numpy()
        current_error = measurements["current"].to_numpy() - virtual["current"].to_numpy()

        rpm_scale = max(float(np.std(measurements["rpm"])), 1e-6)
        current_scale = max(float(np.std(measurements["current"])), 1e-6)
        return np.concatenate([rpm_error / rpm_scale, current_error / current_scale])

    def objective(
        self,
        x: NDArray[np.float64],
        guess: MotorParameters,
        measurements: pd.DataFrame,
    ) -> float:
        """RMSE of the scaled residual vector (the quantity least_squares minimizes)."""
        residual = self.residuals(x, guess, measurements)
        return float(np.sqrt(np.mean(residual**2)))

    def estimate(
        self,
        measurements: pd.DataFrame,
        guess: MotorParameters,
    ) -> MotorParameters:
        """Fit free parameters so the virtual motor tracks the measurements."""
        x0 = np.array([getattr(guess, name) for name in self.free_params], dtype=float)
        result = least_squares(
            fun=lambda x: self.residuals(x, guess, measurements),
            x0=x0,
            bounds=(1e-8, np.inf),
            method="trf",
        )
        fitted = [float(value) for value in result.x]
        return replace(guess, **dict(zip(self.free_params, fitted, strict=True)))

    def adapt(
        self,
        twin: DigitalTwin,
        measurements: pd.DataFrame,
        physical_params: MotorParameters = PHYSICAL_MOTOR_PARAMETERS,
    ) -> AdaptationResult:
        """Estimate parameters, update the twin, and compare before vs after."""
        initial_params = twin.params
        twin.receive_measurements(measurements)
        twin.simulate()
        before = twin.compare()

        estimated = self.estimate(measurements, initial_params)
        twin.update_parameters(estimated)
        twin.receive_measurements(measurements)
        twin.simulate()
        after = twin.compare()

        return AdaptationResult(
            initial_params=initial_params,
            estimated_params=estimated,
            physical_params=physical_params,
            before=before,
            after=after,
        )


def estimate_parameters(
    measurements: pd.DataFrame,
    guess: MotorParameters,
    free_params: Sequence[str] = DEFAULT_FREE_PARAMS,
) -> MotorParameters:
    """Fit selected parameters of the virtual motor to physical measurements."""
    return ParameterEstimator(free_params).estimate(measurements, guess)
