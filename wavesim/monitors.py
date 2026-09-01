"""Headless field and scalar-energy flux monitor sampling."""

from dataclasses import dataclass, field as dataclass_field

import numpy as np

from .config import (
    FieldMonitorConfig,
    FluxMonitorConfig,
    GridConfig,
)


@dataclass
class FieldMonitorState:
    """Recorded scalar samples for one configured field monitor."""

    steps: list[int] = dataclass_field(default_factory=list)
    times: list[float] = dataclass_field(default_factory=list)
    values: list[float] = dataclass_field(default_factory=list)


@dataclass
class FluxMonitorState:
    """Recorded face-flux profiles for one configured monitor."""

    steps: list[int] = dataclass_field(default_factory=list)
    times: list[float] = dataclass_field(default_factory=list)
    profiles: list[np.ndarray] = dataclass_field(default_factory=list)


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

    if monitor.kind == "horizontal_line":
        samples = field[
            monitor.x_start:monitor.x_stop,
            monitor.y,
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


def sample_flux_monitor(
    flux_x: np.ndarray,
    flux_y: np.ndarray,
    monitor: FluxMonitorConfig,
) -> np.ndarray:
    """Return an immutable copy of one aperture's face-flux profile."""
    if monitor.axis == "x":
        profile = flux_x[
            monitor.face_index,
            monitor.transverse_start:monitor.transverse_stop,
        ]
    elif monitor.axis == "y":
        profile = flux_y[
            monitor.transverse_start:monitor.transverse_stop,
            monitor.face_index,
        ]
    else:
        raise ValueError(
            f"Unknown flux-monitor axis: {monitor.axis!r}."
        )

    stored_profile = np.array(profile, dtype=float, copy=True)
    stored_profile.setflags(write=False)
    return stored_profile


def integrate_flux_profile(
    profile: np.ndarray,
    monitor: FluxMonitorConfig,
    grid: GridConfig,
) -> float:
    """Integrate one signed face-flux profile across its aperture."""
    if monitor.axis == "x":
        transverse_spacing = grid.dy
    elif monitor.axis == "y":
        transverse_spacing = grid.dx
    else:
        raise ValueError(
            f"Unknown flux-monitor axis: {monitor.axis!r}."
        )

    return float(np.sum(profile) * transverse_spacing)


def create_flux_monitor_states(
    monitors: tuple[FluxMonitorConfig, ...],
) -> dict[str, FluxMonitorState]:
    """Create empty states for integer-time face-flux samples."""
    return {
        monitor.name: FluxMonitorState()
        for monitor in monitors
    }


def record_flux_monitor_samples(
    monitors: tuple[FluxMonitorConfig, ...],
    states: dict[str, FluxMonitorState],
    flux_x: np.ndarray,
    flux_y: np.ndarray,
    step_index: int,
    dt: float,
) -> None:
    """Record every configured flux profile at one integer time."""
    time_value = step_index * dt

    for monitor in monitors:
        state = states[monitor.name]

        state.steps.append(step_index)
        state.times.append(time_value)
        state.profiles.append(
            sample_flux_monitor(
                flux_x,
                flux_y,
                monitor,
            )
        )


def compute_flux_power_history(
    state: FluxMonitorState,
    monitor: FluxMonitorConfig,
    grid: GridConfig,
) -> np.ndarray:
    """Integrate every stored flux profile into signed aperture power."""
    history_length = len(state.profiles)

    if not (
        len(state.steps)
        == len(state.times)
        == history_length
    ):
        raise ValueError(
            "Flux-monitor steps, times, and profiles "
            "must have matching lengths."
        )

    expected_profile_length = (
        monitor.transverse_stop
        - monitor.transverse_start
    )

    powers = np.empty(history_length, dtype=float)

    for index, profile in enumerate(state.profiles):
        profile_array = np.asarray(profile, dtype=float)

        if profile_array.ndim != 1:
            raise ValueError(
                "Stored flux profiles must be one-dimensional."
            )

        if profile_array.size != expected_profile_length:
            raise ValueError(
                "Stored flux-profile length must match "
                "the configured aperture."
            )

        if not np.all(np.isfinite(profile_array)):
            raise ValueError(
                "Stored flux profiles must contain only finite values."
            )

        powers[index] = integrate_flux_profile(
            profile_array,
            monitor,
            grid,
        )

    return powers