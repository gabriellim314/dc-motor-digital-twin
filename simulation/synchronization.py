"""Lockstep synchronization: physical measurement → twin prediction → error."""

from __future__ import annotations

from dataclasses import dataclass, fields

import pandas as pd

from models.digital_twin import DigitalTwin, TwinMeasurement, TwinPrediction

SYNC_COLUMNS = (
    "timestamp",
    "physical_rpm",
    "twin_rpm",
    "rpm_error",
    "physical_current",
    "twin_current",
    "current_error",
)


@dataclass(frozen=True)
class SyncRecord:
    """One synchronized comparison between physical and virtual states."""

    timestamp: float
    physical_rpm: float
    twin_rpm: float
    rpm_error: float
    physical_current: float
    twin_current: float
    current_error: float

    @classmethod
    def from_pair(cls, measurement: TwinMeasurement, prediction: TwinPrediction) -> SyncRecord:
        return cls(
            timestamp=measurement.timestamp,
            physical_rpm=measurement.rpm,
            twin_rpm=prediction.rpm,
            rpm_error=measurement.rpm - prediction.rpm,
            physical_current=measurement.current,
            twin_current=prediction.current,
            current_error=measurement.current - prediction.current,
        )


class Synchronizer:
    """Run the physical motor and Digital Twin in lockstep and store errors."""

    def __init__(self, twin: DigitalTwin) -> None:
        self.twin = twin
        self.history: list[SyncRecord] = []

    def step(self, measurement: TwinMeasurement, dt: float) -> SyncRecord:
        """Receive one measurement, predict, compare, and store the error."""
        self.twin.receive_measurement(measurement)
        prediction = self.twin.step(
            voltage=measurement.voltage,
            load_torque=measurement.load_torque,
            dt=dt,
        )
        record = SyncRecord.from_pair(measurement, prediction)
        self.history.append(record)
        return record

    def run(self, measurements: pd.DataFrame) -> pd.DataFrame:
        """Synchronize the twin against a full physical measurement series."""
        self.twin.reset()
        self.history.clear()

        previous_time: float | None = None
        for _, row in measurements.iterrows():
            measurement = TwinMeasurement.from_row(row)
            dt = 0.0 if previous_time is None else measurement.timestamp - previous_time
            self.step(measurement, dt)
            previous_time = measurement.timestamp

        return self.to_dataframe()

    def to_dataframe(self) -> pd.DataFrame:
        if not self.history:
            return pd.DataFrame(columns=list(SYNC_COLUMNS))
        return pd.DataFrame(
            [{field.name: getattr(record, field.name) for field in fields(SyncRecord)} for record in self.history]
        )
