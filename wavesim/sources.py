"""Spatial profiles and application logic for continuous sources."""

import numpy as np

from .config import GridConfig, SimulationConfig


def validate_source_profile(
    source_profile: np.ndarray,
    grid: GridConfig,
    *,
    active: bool,
) -> None:
    """Validate a spatial source profile before simulation."""
    if not isinstance(source_profile, np.ndarray):
        raise TypeError("source_profile must be a NumPy array.")

    if source_profile.shape != grid.shape:
        raise ValueError(
            "source_profile shape must match the configured grid shape."
        )

    if not np.issubdtype(source_profile.dtype, np.floating):
        raise TypeError(
            "source_profile must use a floating-point data type."
        )

    if not np.all(np.isfinite(source_profile)):
        raise ValueError("source_profile values must be finite.")

    if np.any(source_profile[0, :] != 0.0):
        raise ValueError(
            "source_profile must be zero on the domain boundary."
        )

    if np.any(source_profile[-1, :] != 0.0):
        raise ValueError(
            "source_profile must be zero on the domain boundary."
        )

    if np.any(source_profile[:, 0] != 0.0):
        raise ValueError(
            "source_profile must be zero on the domain boundary."
        )

    if np.any(source_profile[:, -1] != 0.0):
        raise ValueError(
            "source_profile must be zero on the domain boundary."
        )

    if active and not np.any(source_profile != 0.0):
        raise ValueError(
            "An active source must have at least one nonzero profile value."
        )


def create_source_profile(
    config: SimulationConfig,
) -> np.ndarray:
    """Create and validate the configured spatial source profile."""
    source = config.source
    profile = np.zeros(config.grid.shape, dtype=float)

    if source.kind == "none":
        pass

    elif source.kind == "point_sine":
        profile[source.x, source.y] = 1.0

    elif source.kind == "line_sine":
        profile[
            source.x,
            source.y_start:source.y_stop,
        ] = 1.0

    else:
        raise ValueError(f"Unknown source type: {source.kind!r}.")

    validate_source_profile(
        profile,
        config.grid,
        active=source.kind != "none",
    )

    profile.setflags(write=False)
    return profile


def compute_source_envelope(
    step_index: int,
    config: SimulationConfig,
) -> float:
    """Return the smooth source turn-on envelope at one time step."""
    source = config.source

    if source.ramp_cycles == 0.0:
        return 1.0

    time_value = step_index * config.time.dt
    ramp_duration = source.ramp_cycles / source.frequency

    if time_value >= ramp_duration:
        return 1.0

    return float(
        np.sin(
            0.5 * np.pi * time_value / ramp_duration
        ) ** 2
    )


def apply_source(
    field: np.ndarray,
    step_index: int,
    config: SimulationConfig,
    source_profile: np.ndarray | None = None,
) -> None:
    """Add the configured continuous source to a field in place."""
    source = config.source

    if source.kind == "none":
        return

    selected_profile = (
        create_source_profile(config)
        if source_profile is None
        else source_profile
    )

    validate_source_profile(
        selected_profile,
        config.grid,
        active=True,
    )

    time_value = step_index * config.time.dt
    source_value = (
        source.amplitude
        * compute_source_envelope(step_index, config)
        * np.sin(
            2.0 * np.pi * source.frequency * time_value
        )
    )

    active_cells = selected_profile != 0.0

    field[active_cells] += (
        source_value * selected_profile[active_cells]
    )
