"""Headless scalar-field monitor sampling and history storage."""

from dataclasses import dataclass, field as dataclass_field

import numpy as np

from .config import FieldMonitorConfig


@dataclass
class FieldMonitorState:
    """Recorded scalar samples for one configured field monitor."""

    steps: list[int] = dataclass_field(default_factory=list)
    times: list[float] = dataclass_field(default_factory=list)
    values: list[float] = dataclass_field(default_factory=list)


def sample_field_monitor(
    field: np.ndarray,
    monitor: FieldMonitorConfig,
) -> float:
    """Sample one configured monitor from the supplied field."""
    if monitor.kind == "point":
        return float(field[monitor.x, monitor.y])

    if monitor.kind == "vertical_line":
        samples = field[
            monitor.x,
            monitor.y_start:monitor.y_stop,
        ]

        if monitor.reduction == "mean":
            return float(np.mean(samples))

        raise ValueError(
            f"Unknown monitor reduction: {monitor.reduction!r}."
        )

    raise ValueError(f"Unknown monitor type: {monitor.kind!r}.")


def create_monitor_states(
    monitors: tuple[FieldMonitorConfig, ...],
    initial_field: np.ndarray,
) -> dict[str, FieldMonitorState]:
    """Create monitor states containing the initial t=0 samples."""
    states: dict[str, FieldMonitorState] = {}

    for monitor in monitors:
        states[monitor.name] = FieldMonitorState(
            steps=[0],
            times=[0.0],
            values=[
                sample_field_monitor(
                    initial_field,
                    monitor,
                )
            ],
        )

    return states


def record_monitor_samples(
    monitors: tuple[FieldMonitorConfig, ...],
    states: dict[str, FieldMonitorState],
    field: np.ndarray,
    step_index: int,
    dt: float,
) -> None:
    """Record every configured monitor at one completed time step."""
    time_value = step_index * dt

    for monitor in monitors:
        state = states[monitor.name]

        state.steps.append(step_index)
        state.times.append(time_value)
        state.values.append(
            sample_field_monitor(field, monitor)
        )