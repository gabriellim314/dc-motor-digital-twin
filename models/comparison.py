"""Compare physical measurements with Digital Twin predictions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SignalErrors:
    """Error statistics for one signal."""

    error: pd.Series
    absolute_error: pd.Series
    relative_error: pd.Series
    rmse: float
    mae: float


@dataclass(frozen=True)
class ComparisonResult:
    """Physical vs virtual errors for RPM and current."""

    timestamp: pd.Series
    rpm: SignalErrors
    current: SignalErrors
    frame: pd.DataFrame

    def summary(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "rpm": {
                    "rmse": self.rpm.rmse,
                    "mae": self.rpm.mae,
                    "mean_relative_error": float(self.rpm.relative_error.mean()),
                },
                "current": {
                    "rmse": self.current.rmse,
                    "mae": self.current.mae,
                    "mean_relative_error": float(self.current.relative_error.mean()),
                },
            }
        )


def _signal_errors(physical: pd.Series, virtual: pd.Series) -> SignalErrors:
    error = physical.to_numpy(dtype=float) - virtual.to_numpy(dtype=float)
    absolute = np.abs(error)
    relative = np.divide(
        absolute,
        np.abs(physical.to_numpy(dtype=float)),
        out=np.zeros_like(absolute),
        where=np.abs(physical.to_numpy(dtype=float)) > 1e-12,
    )
    return SignalErrors(
        error=pd.Series(error, index=physical.index, name="error"),
        absolute_error=pd.Series(absolute, index=physical.index, name="absolute_error"),
        relative_error=pd.Series(relative, index=physical.index, name="relative_error"),
        rmse=float(np.sqrt(np.mean(error**2))),
        mae=float(np.mean(absolute)),
    )


def compare_measurements(physical: pd.DataFrame, virtual: pd.DataFrame) -> ComparisonResult:
    """Compute RPM and current errors between two aligned time series."""
    if len(physical) != len(virtual):
        raise ValueError("Physical and virtual series must have the same length.")

    rpm = _signal_errors(physical["rpm"], virtual["rpm"])
    current = _signal_errors(physical["current"], virtual["current"])
    timestamp = physical["timestamp"].reset_index(drop=True)

    frame = pd.DataFrame(
        {
            "timestamp": timestamp,
            "rpm_error": rpm.error.to_numpy(),
            "current_error": current.error.to_numpy(),
            "rpm_absolute_error": rpm.absolute_error.to_numpy(),
            "current_absolute_error": current.absolute_error.to_numpy(),
            "rpm_relative_error": rpm.relative_error.to_numpy(),
            "current_relative_error": current.relative_error.to_numpy(),
        }
    )
    return ComparisonResult(timestamp=timestamp, rpm=rpm, current=current, frame=frame)
