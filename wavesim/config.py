"""Configuration models, validation, and reporting for the 2D wave solver."""

from dataclasses import dataclass

import numpy as np


MIN_POINTS_PER_WAVELENGTH = 10.0

VALID_BOUNDARIES = {"fixed", "sponge"}
VALID_INITIAL_CONDITIONS = {"gaussian", "zero"}
VALID_SOURCES = {
    "none",
    "point_sine",
    "line_sine",
}
VALID_MONITORS = {
    "point",
    "vertical_line",
    "horizontal_line",
}

VALID_FLUX_MONITOR_AXES = {"x", "y"}

VALID_MONITOR_REDUCTIONS = {
    "mean",
}


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
    """Time-stepping configuration."""

    dt: float = 0.4
    steps: int = 500


@dataclass(frozen=True)
class MaterialConfig:
    """Configuration for the simulated material."""

    reference_wave_speed: float = 1.0
    background_refractive_index: float = 1.0


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
    y_start: int | None = None
    y_stop: int | None = None
    ramp_cycles: float = 0.0


@dataclass(frozen=True)
class FieldMonitorConfig:
    """Configuration for one scalar-field monitor."""

    name: str
    kind: str
    x: int | None = None
    y: int | None = None
    x_start: int | None = None
    x_stop: int | None = None
    y_start: int | None = None
    y_stop: int | None = None
    reduction: str = "mean"


@dataclass(frozen=True)
class FluxMonitorConfig:
    """Configuration for one face-centered scalar-energy flux monitor."""

    name: str
    axis: str
    face_index: int
    transverse_start: int
    transverse_stop: int


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
    show_material_profile: bool = True
    print_energy_interval: int = 50
    animation_interval_ms: int = 30


@dataclass(frozen=True)
class SimulationConfig:
    """Complete configuration for one simulation."""

    grid: GridConfig
    time: TimeConfig
    material: MaterialConfig
    initial_condition: InitialConditionConfig
    source: SourceConfig
    boundary: BoundaryConfig
    visualization: VisualizationConfig
    monitors: tuple[FieldMonitorConfig, ...] = ()
    flux_monitors: tuple[FluxMonitorConfig, ...] = ()


def create_default_config() -> SimulationConfig:
    """Create the same default configuration used at the end of Phase 1."""
    grid = GridConfig()

    return SimulationConfig(
        grid=grid,
        time=TimeConfig(),
        material=MaterialConfig(),
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
            show_material_profile=True,
            print_energy_interval=50,
            animation_interval_ms=30,
        ),
    )


def compute_courant_number(
    config: SimulationConfig,
    maximum_wave_speed: float,
) -> float:
    """Return the 2D Courant number using the fastest material speed."""
    grid = config.grid
    time = config.time

    return maximum_wave_speed * time.dt * np.sqrt(
        1.0 / grid.dx**2 + 1.0 / grid.dy**2
    )


def validate_courant_number(
    config: SimulationConfig,
    maximum_wave_speed: float,
) -> None:
    """Validate stability using the fastest speed in the domain."""
    courant = compute_courant_number(
        config,
        maximum_wave_speed,
    )

    if courant > 1.0:
        raise ValueError(
            f"Simulation unstable: Courant number = {courant:.3f}. "
            "Reduce dt or increase dx and/or dy."
        )


def validate_config(config: SimulationConfig) -> None:
    """Validate all simulation settings before allocating fields."""
    grid = config.grid
    time = config.time
    material = config.material
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

    if (
        not np.isfinite(material.reference_wave_speed)
        or material.reference_wave_speed <= 0
    ):
        raise ValueError(
            "reference_wave_speed must be finite and positive."
        )

    if (
        not np.isfinite(material.background_refractive_index)
        or material.background_refractive_index <= 0
    ):
        raise ValueError(
            "background_refractive_index must be finite and positive."
        )

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

    active_sine_sources = {
        "point_sine",
        "line_sine",
    }

    if source.kind in active_sine_sources:
        if not (1 <= source.x < grid.nx - 1):
            raise ValueError(
                "Source x-coordinate must be inside the interior domain."
            )

        if (
            not np.isfinite(source.frequency)
            or source.frequency <= 0
        ):
            raise ValueError(
                "source_frequency must be finite and positive."
            )

        if not np.isfinite(source.amplitude):
            raise ValueError("source_amplitude must be finite.")

        if (
            not np.isfinite(source.ramp_cycles)
            or source.ramp_cycles < 0
        ):
            raise ValueError(
                "source_ramp_cycles must be finite and nonnegative."
            )

        nyquist_frequency = 1.0 / (2.0 * time.dt)

        if source.frequency >= nyquist_frequency:
            raise ValueError(
                "source_frequency must be below the temporal Nyquist "
                f"frequency ({nyquist_frequency:.3f})."
            )

    if source.kind == "point_sine":
        if not (1 <= source.y < grid.ny - 1):
            raise ValueError(
                "Source y-coordinate must be inside the interior domain."
            )

    if source.kind == "line_sine":
        if source.y_start is None or source.y_stop is None:
            raise ValueError(
                "Line sources require y_start and y_stop."
            )

        if (
            not isinstance(source.y_start, (int, np.integer))
            or isinstance(source.y_start, (bool, np.bool_))
        ):
            raise TypeError("source_y_start must be an integer.")

        if (
            not isinstance(source.y_stop, (int, np.integer))
            or isinstance(source.y_stop, (bool, np.bool_))
        ):
            raise TypeError("source_y_stop must be an integer.")

        if not (
            1
            <= source.y_start
            < source.y_stop
            <= grid.ny - 1
        ):
            raise ValueError(
                "Line-source bounds must define a nonempty "
                "half-open interval inside the interior domain."
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

    monitor_names: set[str] = set()

    for monitor in config.monitors:
        if not isinstance(monitor, FieldMonitorConfig):
            raise TypeError(
                "Each monitor must be a FieldMonitorConfig."
            )

        if not monitor.name or not monitor.name.strip():
            raise ValueError(
                "Monitor names must contain non-whitespace characters."
            )

        if monitor.name in monitor_names:
            raise ValueError(
                f"Duplicate monitor name: {monitor.name!r}."
            )

        monitor_names.add(monitor.name)

        if monitor.kind not in VALID_MONITORS:
            raise ValueError(
                f"Unknown monitor type: {monitor.kind!r}. "
                f"Available options: {sorted(VALID_MONITORS)}"
            )

        if monitor.kind == "point":
            if not (
                isinstance(monitor.x, (int, np.integer))
                and not isinstance(monitor.x, (bool, np.bool_))
            ):
                raise TypeError(
                    "Point-monitor x-coordinate must be an integer."
                )

            if not (1 <= monitor.x < grid.nx - 1):
                raise ValueError(
                    "Point-monitor x-coordinate must be inside "
                    "the interior domain."
                )

            if not (
                isinstance(monitor.y, (int, np.integer))
                and not isinstance(monitor.y, (bool, np.bool_))
            ):
                raise TypeError(
                    "Point-monitor y-coordinate must be an integer."
                )

            if not (1 <= monitor.y < grid.ny - 1):
                raise ValueError(
                    "Point-monitor y-coordinate must be inside "
                    "the interior domain."
                )

        if monitor.kind == "vertical_line":
            if not (
                isinstance(monitor.x, (int, np.integer))
                and not isinstance(monitor.x, (bool, np.bool_))
            ):
                raise TypeError(
                    "Vertical-line monitor x-coordinate "
                    "must be an integer."
                )

            if not (1 <= monitor.x < grid.nx - 1):
                raise ValueError(
                    "Vertical-line monitor x-coordinate must be "
                    "inside the interior domain."
                )

            if (
                monitor.y_start is None
                or monitor.y_stop is None
            ):
                raise ValueError(
                    "Vertical-line monitors require "
                    "y_start and y_stop."
                )

            if not (
                isinstance(
                    monitor.y_start,
                    (int, np.integer),
                )
                and not isinstance(
                    monitor.y_start,
                    (bool, np.bool_),
                )
            ):
                raise TypeError(
                    "Monitor y_start must be an integer."
                )

            if not (
                isinstance(
                    monitor.y_stop,
                    (int, np.integer),
                )
                and not isinstance(
                    monitor.y_stop,
                    (bool, np.bool_),
                )
            ):
                raise TypeError(
                    "Monitor y_stop must be an integer."
                )

            if not (
                1
                <= monitor.y_start
                < monitor.y_stop
                <= grid.ny - 1
            ):
                raise ValueError(
                    "Vertical-line monitor bounds must define "
                    "a nonempty half-open interval inside "
                    "the interior domain."
                )

            if monitor.reduction not in VALID_MONITOR_REDUCTIONS:
                raise ValueError(
                    f"Unknown monitor reduction: "
                    f"{monitor.reduction!r}. "
                    "Available options: "
                    f"{sorted(VALID_MONITOR_REDUCTIONS)}"
                )

        if monitor.kind == "horizontal_line":
            if not (
                isinstance(monitor.y, (int, np.integer))
                and not isinstance(monitor.y, (bool, np.bool_))
            ):
                raise TypeError(
                    "Horizontal-line monitor y-coordinate "
                    "must be an integer."
                )

            if not (1 <= monitor.y < grid.ny - 1):
                raise ValueError(
                    "Horizontal-line monitor y-coordinate must be "
                    "inside the interior domain."
                )

            if (
                monitor.x_start is None
                or monitor.x_stop is None
            ):
                raise ValueError(
                    "Horizontal-line monitors require "
                    "x_start and x_stop."
                )

            if not (
                isinstance(monitor.x_start, (int, np.integer))
                and not isinstance(monitor.x_start, (bool, np.bool_))
            ):
                raise TypeError(
                    "Monitor x_start must be an integer."
                )

            if not (
                isinstance(monitor.x_stop, (int, np.integer))
                and not isinstance(monitor.x_stop, (bool, np.bool_))
            ):
                raise TypeError(
                    "Monitor x_stop must be an integer."
                )

            if not (
                1
                <= monitor.x_start
                < monitor.x_stop
                <= grid.nx - 1
            ):
                raise ValueError(
                    "Horizontal-line monitor bounds must define "
                    "a nonempty half-open interval inside "
                    "the interior domain."
                )

            if monitor.reduction not in VALID_MONITOR_REDUCTIONS:
                raise ValueError(
                    f"Unknown monitor reduction: "
                    f"{monitor.reduction!r}. "
                    "Available options: "
                    f"{sorted(VALID_MONITOR_REDUCTIONS)}"
                )

    for monitor in config.flux_monitors:
        if not isinstance(monitor, FluxMonitorConfig):
            raise TypeError(
                "Each flux monitor must be a FluxMonitorConfig."
            )

        if not monitor.name or not monitor.name.strip():
            raise ValueError(
                "Monitor names must contain non-whitespace characters."
            )

        if monitor.name in monitor_names:
            raise ValueError(
                f"Duplicate monitor name: {monitor.name!r}."
            )

        monitor_names.add(monitor.name)

        if monitor.axis not in VALID_FLUX_MONITOR_AXES:
            raise ValueError(
                f"Unknown flux-monitor axis: {monitor.axis!r}. "
                "Available options: "
                f"{sorted(VALID_FLUX_MONITOR_AXES)}"
            )

        for value, label in (
            (monitor.face_index, "face_index"),
            (monitor.transverse_start, "transverse_start"),
            (monitor.transverse_stop, "transverse_stop"),
        ):
            if not (
                isinstance(value, (int, np.integer))
                and not isinstance(value, (bool, np.bool_))
            ):
                raise TypeError(
                    f"Flux-monitor {label} must be an integer."
                )

        if monitor.axis == "x":
            if not (0 <= monitor.face_index < grid.nx - 1):
                raise ValueError(
                    "x-flux face_index must satisfy "
                    "0 <= face_index < nx - 1."
                )

            if not (
                0
                <= monitor.transverse_start
                < monitor.transverse_stop
                <= grid.ny
            ):
                raise ValueError(
                    "x-flux transverse bounds must define a "
                    "nonempty half-open interval inside the y grid."
                )

        if monitor.axis == "y":
            if not (0 <= monitor.face_index < grid.ny - 1):
                raise ValueError(
                    "y-flux face_index must satisfy "
                    "0 <= face_index < ny - 1."
                )

            if not (
                0
                <= monitor.transverse_start
                < monitor.transverse_stop
                <= grid.nx
            ):
                raise ValueError(
                    "y-flux transverse bounds must define a "
                    "nonempty half-open interval inside the x grid."
                )

        if source.kind == "point_sine":
            if monitor.axis == "x":
                source_overlaps = (
                    source.x in {
                        monitor.face_index,
                        monitor.face_index + 1,
                    }
                    and monitor.transverse_start
                    <= source.y
                    < monitor.transverse_stop
                )
            else:
                source_overlaps = (
                    source.y in {
                        monitor.face_index,
                        monitor.face_index + 1,
                    }
                    and monitor.transverse_start
                    <= source.x
                    < monitor.transverse_stop
                )

        elif source.kind == "line_sine":
            if monitor.axis == "x":
                source_overlaps = (
                    source.x in {
                        monitor.face_index,
                        monitor.face_index + 1,
                    }
                    and max(
                        monitor.transverse_start,
                        source.y_start,
                    )
                    < min(
                        monitor.transverse_stop,
                        source.y_stop,
                    )
                )
            else:
                source_overlaps = (
                    monitor.transverse_start
                    <= source.x
                    < monitor.transverse_stop
                    and (
                        monitor.face_index
                        in range(source.y_start, source.y_stop)
                        or monitor.face_index + 1
                        in range(source.y_start, source.y_stop)
                    )
                )

        else:
            source_overlaps = False

        if source_overlaps:
            raise ValueError(
                f"Flux monitor {monitor.name!r} overlaps the active "
                "source profile."
            )


def print_configuration(
    config: SimulationConfig,
    maximum_wave_speed: float,
    source_wave_speed: float,
) -> None:
    """Print the validated configuration and useful diagnostics."""
    grid = config.grid
    time = config.time
    initial = config.initial_condition
    source = config.source
    boundary = config.boundary

    print("Simulation configuration")
    print("------------------------")
    print(f"Grid:               {grid.nx} × {grid.ny}")
    print(
        f"Courant number:     "
        f"{compute_courant_number(config, maximum_wave_speed):.3f}"
    )
    print(f"Boundary condition: {boundary.kind}")

    if boundary.kind == "sponge":
        print(f"Damping width:      {boundary.damping_width}")
        print(f"Maximum damping:    {boundary.max_damping}")
        print(f"Damping exponent:   {boundary.damping_exponent}")

    print(f"Initial condition:  {initial.kind}")
    print(f"Source type:        {source.kind}")

    if source.kind in {"point_sine", "line_sine"}:
        if source.kind == "point_sine":
            print(f"Source position:    ({source.x}, {source.y})")
        else:
            print(
                "Source aperture:    "
                f"x={source.x}, "
                f"y=[{source.y_start}, {source.y_stop})"
            )

        print(f"Source amplitude:   {source.amplitude}")
        print(f"Source frequency:   {source.frequency}")
        print(f"Source ramp:        {source.ramp_cycles} cycles")

        nominal_wavelength = source_wave_speed / source.frequency
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
