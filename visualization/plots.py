"""Matplotlib plots for simulation results (not the 3D frontend)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_rpm_and_current(
    results: pd.DataFrame,
    save_path: str | Path | None = None,
) -> None:
    """Plot RPM and armature current versus time."""
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(8, 6))

    axes[0].plot(results["time"], results["rpm"], color="tab:blue")
    axes[0].set_ylabel("Speed [RPM]")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(results["time"], results["current"], color="tab:orange")
    axes[1].set_ylabel("Current [A]")
    axes[1].set_xlabel("Time [s]")
    axes[1].grid(True, alpha=0.3)

    fig.suptitle("DC Motor Simulation")
    fig.tight_layout()

    if save_path is not None:
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
    else:
        plt.show()


def plot_simulation(results: pd.DataFrame, save_path: str | Path | None = None) -> None:
    """Plot current, speed, and electromagnetic torque versus time."""
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(8, 7))

    axes[0].plot(results["time"], results["current"], color="tab:orange")
    axes[0].set_ylabel("Current [A]")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(results["time"], results["rpm"], color="tab:blue")
    axes[1].set_ylabel("Speed [RPM]")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(results["time"], results["torque_em"], color="tab:red")
    axes[2].set_ylabel("Torque [N·m]")
    axes[2].set_xlabel("Time [s]")
    axes[2].grid(True, alpha=0.3)

    fig.suptitle("DC Motor Simulation")
    fig.tight_layout()

    if save_path is not None:
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
    else:
        plt.show()


def plot_physical_vs_twin(
    physical: pd.DataFrame,
    virtual: pd.DataFrame,
    save_path: str | Path | None = None,
) -> None:
    """Overlay physical motor and Digital Twin RPM and current."""
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(8, 6))

    axes[0].plot(physical["timestamp"], physical["rpm"], label="Physical Motor")
    axes[0].plot(virtual["timestamp"], virtual["rpm"], linestyle="--", label="Digital Twin")
    axes[0].set_ylabel("Speed [RPM]")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(physical["timestamp"], physical["current"], label="Physical Motor")
    axes[1].plot(virtual["timestamp"], virtual["current"], linestyle="--", label="Digital Twin")
    axes[1].set_ylabel("Current [A]")
    axes[1].set_xlabel("Time [s]")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.suptitle("Physical Motor vs Digital Twin")
    fig.tight_layout()

    if save_path is not None:
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
    else:
        plt.show()


def plot_sync_dataset(dataset: pd.DataFrame, save_path: str | Path | None = None) -> None:
    """Plot synchronized physical vs Digital Twin RPM and current."""
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(8, 6))

    axes[0].plot(dataset["timestamp"], dataset["physical_rpm"], label="Physical Motor")
    axes[0].plot(dataset["timestamp"], dataset["twin_rpm"], linestyle="--", label="Digital Twin")
    axes[0].set_ylabel("Speed [RPM]")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(dataset["timestamp"], dataset["physical_current"], label="Physical Motor")
    axes[1].plot(dataset["timestamp"], dataset["twin_current"], linestyle="--", label="Digital Twin")
    axes[1].set_ylabel("Current [A]")
    axes[1].set_xlabel("Time [s]")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.suptitle("Synchronized Physical Motor vs Digital Twin")
    fig.tight_layout()

    if save_path is not None:
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
    else:
        plt.show()


def plot_adaptation(
    physical: pd.DataFrame,
    before: pd.DataFrame,
    after: pd.DataFrame,
    save_path: str | Path | None = None,
) -> None:
    """Compare physical motor with the Digital Twin before and after adaptation."""
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(8, 6))

    axes[0].plot(physical["timestamp"], physical["rpm"], label="Physical Motor")
    axes[0].plot(before["timestamp"], before["rpm"], linestyle="--", label="Twin before")
    axes[0].plot(after["timestamp"], after["rpm"], linestyle=":", label="Twin after")
    axes[0].set_ylabel("Speed [RPM]")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(physical["timestamp"], physical["current"], label="Physical Motor")
    axes[1].plot(before["timestamp"], before["current"], linestyle="--", label="Twin before")
    axes[1].plot(after["timestamp"], after["current"], linestyle=":", label="Twin after")
    axes[1].set_ylabel("Current [A]")
    axes[1].set_xlabel("Time [s]")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.suptitle("Digital Twin Adaptation")
    fig.tight_layout()

    if save_path is not None:
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
    else:
        plt.show()
