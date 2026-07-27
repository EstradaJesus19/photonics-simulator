"""Configuration models, validation, and reporting for the 2D wave solver."""

from dataclasses import dataclass

import numpy as np


MIN_POINTS_PER_WAVELENGTH = 10.0

VALID_BOUNDARIES = {"fixed", "sponge"}
VALID_INITIAL_CONDITIONS = {"gaussian", "zero"}
VALID_SOURCES = {"none", "point_sine"}


@dataclass(frozen=True)
class GridConfig:
    """Spatial-grid configuration."""

    nx: int = 150
    ny: int = 150
    dx: float = 1.0
    dy: float = 1.0

    @property
    def shape(self) -> tuple[int, int]:
        """Return the NumPy field shape associated with the grid."""
        return self.nx, self.ny


@dataclass(frozen=True)
class TimeConfig:
    """Time-stepping and homogeneous-medium configuration."""

    wave_speed: float = 1.0
    dt: float = 0.4
    steps: int = 500


@dataclass(frozen=True)
class InitialConditionConfig:
    """Initial field configuration."""

    kind: str
    x0: int
    y0: int
    sigma: float = 8.0


@dataclass(frozen=True)
class SourceConfig:
    """Continuous-source configuration."""

    kind: str
    x: int
    y: int
    amplitude: float = 0.5
    frequency: float = 0.075


@dataclass(frozen=True)
class BoundaryConfig:
    """Boundary-condition configuration."""

    kind: str = "sponge"
    damping_width: int = 50
    max_damping: float = 0.02
    damping_exponent: float = 2.0


@dataclass(frozen=True)
class VisualizationConfig:
    """Animation and diagnostic-display configuration."""

    display_limit: float = 0.5
    show_damping_profile: bool = True
    print_energy_interval: int = 50
    animation_interval_ms: int = 30


@dataclass(frozen=True)
class SimulationConfig:
    """Complete configuration for one simulation."""

    grid: GridConfig
    time: TimeConfig
    initial_condition: InitialConditionConfig
    source: SourceConfig
    boundary: BoundaryConfig
    visualization: VisualizationConfig


def create_default_config() -> SimulationConfig:
    """Create the same default configuration used at the end of Phase 1."""
    grid = GridConfig()

    return SimulationConfig(
        grid=grid,
        time=TimeConfig(),
        initial_condition=InitialConditionConfig(
            kind="zero",
            x0=grid.nx // 2,
            y0=grid.ny // 2,
            sigma=8.0,
        ),
        source=SourceConfig(
            kind="point_sine",
            x=grid.nx // 2,
            y=grid.ny // 2,
            amplitude=0.5,
            frequency=0.075,
        ),
        boundary=BoundaryConfig(
            kind="sponge",
            damping_width=50,
            max_damping=0.02,
            damping_exponent=2.0,
        ),
        visualization=VisualizationConfig(
            display_limit=0.5,
            show_damping_profile=True,
            print_energy_interval=50,
            animation_interval_ms=30,
        ),
    )


def compute_courant_number(config: SimulationConfig) -> float:
    """Return the 2D Courant number for the homogeneous medium."""
    grid = config.grid
    time = config.time

    return time.wave_speed * time.dt * np.sqrt(
        1.0 / grid.dx**2 + 1.0 / grid.dy**2
    )


def validate_config(config: SimulationConfig) -> None:
    """Validate all simulation settings before allocating fields."""
    grid = config.grid
    time = config.time
    initial = config.initial_condition
    source = config.source
    boundary = config.boundary
    visualization = config.visualization

    if boundary.kind not in VALID_BOUNDARIES:
        raise ValueError(
            f"Unknown boundary type: {boundary.kind!r}. "
            f"Available options: {sorted(VALID_BOUNDARIES)}"
        )

    if initial.kind not in VALID_INITIAL_CONDITIONS:
        raise ValueError(
            f"Unknown initial condition: {initial.kind!r}. "
            f"Available options: {sorted(VALID_INITIAL_CONDITIONS)}"
        )

    if source.kind not in VALID_SOURCES:
        raise ValueError(
            f"Unknown source type: {source.kind!r}. "
            f"Available options: {sorted(VALID_SOURCES)}"
        )

    if grid.nx < 3 or grid.ny < 3:
        raise ValueError(
            "The grid must contain at least 3 points per direction."
        )

    if grid.dx <= 0 or grid.dy <= 0:
        raise ValueError("Grid spacing dx and dy must be positive.")

    if time.wave_speed <= 0:
        raise ValueError("Wave speed must be positive.")

    if time.dt <= 0:
        raise ValueError("Time step dt must be positive.")

    if time.steps <= 0:
        raise ValueError("The number of time steps must be positive.")

    if visualization.display_limit <= 0:
        raise ValueError("display_limit must be positive.")

    if visualization.print_energy_interval <= 0:
        raise ValueError("print_energy_interval must be positive.")

    if visualization.animation_interval_ms <= 0:
        raise ValueError("animation_interval_ms must be positive.")

    if initial.kind == "gaussian":
        if initial.sigma <= 0:
            raise ValueError("Gaussian width sigma must be positive.")

        if not (1 <= initial.x0 < grid.nx - 1):
            raise ValueError("x0 must be inside the interior domain.")

        if not (1 <= initial.y0 < grid.ny - 1):
            raise ValueError("y0 must be inside the interior domain.")

    if source.kind == "point_sine":
        if not (1 <= source.x < grid.nx - 1):
            raise ValueError(
                "Source x-coordinate must be inside the interior domain."
            )

        if not (1 <= source.y < grid.ny - 1):
            raise ValueError(
                "Source y-coordinate must be inside the interior domain."
            )

        if source.frequency <= 0:
            raise ValueError("source_frequency must be positive.")

        if not np.isfinite(source.amplitude):
            raise ValueError("source_amplitude must be finite.")

        nyquist_frequency = 1.0 / (2.0 * time.dt)

        if source.frequency >= nyquist_frequency:
            raise ValueError(
                "source_frequency must be below the temporal Nyquist "
                f"frequency ({nyquist_frequency:.3f})."
            )

    if boundary.kind == "sponge":
        if boundary.damping_width < 1:
            raise ValueError("damping_width must be at least 1.")

        maximum_damping_width = min(grid.nx, grid.ny) // 2

        if boundary.damping_width >= maximum_damping_width:
            raise ValueError(
                "damping_width must be smaller than "
                f"{maximum_damping_width} for the current grid."
            )

        if boundary.max_damping < 0:
            raise ValueError("max_damping cannot be negative.")

        if boundary.damping_exponent <= 0:
            raise ValueError("damping_exponent must be positive.")

    courant = compute_courant_number(config)

    if courant > 1.0:
        raise ValueError(
            f"Simulation unstable: Courant number = {courant:.3f}. "
            "Reduce dt or increase dx and/or dy."
        )


def print_configuration(config: SimulationConfig) -> None:
    """Print the validated configuration and useful diagnostics."""
    grid = config.grid
    time = config.time
    initial = config.initial_condition
    source = config.source
    boundary = config.boundary

    print("Simulation configuration")
    print("------------------------")
    print(f"Grid:               {grid.nx} × {grid.ny}")
    print(f"Courant number:     {compute_courant_number(config):.3f}")
    print(f"Boundary condition: {boundary.kind}")

    if boundary.kind == "sponge":
        print(f"Damping width:      {boundary.damping_width}")
        print(f"Maximum damping:    {boundary.max_damping}")
        print(f"Damping exponent:   {boundary.damping_exponent}")

    print(f"Initial condition:  {initial.kind}")
    print(f"Source type:        {source.kind}")

    if source.kind == "point_sine":
        print(f"Source position:    ({source.x}, {source.y})")
        print(f"Source amplitude:   {source.amplitude}")
        print(f"Source frequency:   {source.frequency}")

        nominal_wavelength = time.wave_speed / source.frequency
        points_per_wavelength_x = nominal_wavelength / grid.dx
        points_per_wavelength_y = nominal_wavelength / grid.dy

        print(f"Source wavelength:  {nominal_wavelength:.3f}")
        print(
            "Points/wavelength: "
            f"x={points_per_wavelength_x:.2f}, "
            f"y={points_per_wavelength_y:.2f}"
        )

        minimum_points_per_wavelength = min(
            points_per_wavelength_x,
            points_per_wavelength_y,
        )

        if minimum_points_per_wavelength < MIN_POINTS_PER_WAVELENGTH:
            print(
                "Warning: the source wavelength has fewer than "
                f"{MIN_POINTS_PER_WAVELENGTH} grid points. "
                "Numerical dispersion may be significant."
            )

    if initial.kind == "zero" and source.kind == "none":
        print(
            "Warning: zero initial field and no source selected. "
            "The field will remain zero."
        )
