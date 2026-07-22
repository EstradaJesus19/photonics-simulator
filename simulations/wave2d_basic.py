"""2D scalar-wave simulation.

Phase 2.1 refactor:
- configuration is stored in dataclasses;
- numerical functions receive their dependencies explicitly;
- mutable simulation state is contained in Wave2DSimulation;
- visualization is separated from the numerical solver;
- importing this module no longer starts a simulation.

The finite-difference equations and default physical parameters are unchanged
from the Phase 1 implementation.
"""

from dataclasses import dataclass, field as dataclass_field

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation


ENERGY_EPSILON = 1e-12
MIN_POINTS_PER_WAVELENGTH = 10.0

VALID_BOUNDARIES = {"fixed", "sponge"}
VALID_INITIAL_CONDITIONS = {"gaussian", "zero"}
VALID_SOURCES = {"none", "point_sine"}


# ============================================================
# 1. Configuration data
# ============================================================

@dataclass(frozen=True)
class GridConfig:
    """Spatial-grid configuration."""

    nx: int = 150
    ny: int = 150
    dx: float = 1.0
    dy: float = 1.0

    @property
    def shape(self) -> tuple[int, int]:
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


# ============================================================
# 2. Configuration validation and reporting
# ============================================================

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
            raise ValueError("Source x-coordinate must be inside the interior domain.")

        if not (1 <= source.y < grid.ny - 1):
            raise ValueError("Source y-coordinate must be inside the interior domain.")

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
    """Print the validated simulation configuration and useful diagnostics."""
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


# ============================================================
# 3. Numerical helper functions
# ============================================================

def apply_fixed_boundaries(field: np.ndarray) -> None:
    """Set the outermost cells to zero in place."""
    field[0, :] = 0.0
    field[-1, :] = 0.0
    field[:, 0] = 0.0
    field[:, -1] = 0.0


def compute_laplacian(field: np.ndarray, grid: GridConfig) -> np.ndarray:
    """Compute the 2D finite-difference Laplacian on interior points."""
    laplacian = np.zeros_like(field)

    laplacian[1:-1, 1:-1] = (
        (
            field[2:, 1:-1]
            - 2.0 * field[1:-1, 1:-1]
            + field[:-2, 1:-1]
        )
        / grid.dx**2
        + (
            field[1:-1, 2:]
            - 2.0 * field[1:-1, 1:-1]
            + field[1:-1, :-2]
        )
        / grid.dy**2
    )

    return laplacian


def create_gaussian_pulse(
    grid: GridConfig,
    initial: InitialConditionConfig,
) -> np.ndarray:
    """Create the initial 2D Gaussian field distribution."""
    x = np.arange(grid.nx)
    y = np.arange(grid.ny)
    x_mesh, y_mesh = np.meshgrid(x, y, indexing="ij")

    pulse = np.exp(
        -(
            (x_mesh - initial.x0) ** 2
            + (y_mesh - initial.y0) ** 2
        )
        / (2.0 * initial.sigma**2)
    )

    apply_fixed_boundaries(pulse)
    return pulse


def create_zero_field(grid: GridConfig) -> np.ndarray:
    """Create a zero field with the configured grid shape."""
    return np.zeros(grid.shape)


def create_damping_profile(
    grid: GridConfig,
    boundary: BoundaryConfig,
) -> np.ndarray:
    """Create the spatial sponge coefficient gamma(x, y)."""
    x_indices = np.arange(grid.nx)
    y_indices = np.arange(grid.ny)

    distance_x = np.minimum(x_indices, grid.nx - 1 - x_indices)
    distance_y = np.minimum(y_indices, grid.ny - 1 - y_indices)

    distance_to_edge = np.minimum(
        distance_x[:, np.newaxis],
        distance_y[np.newaxis, :],
    )

    normalized_depth = np.clip(
        (boundary.damping_width - distance_to_edge)
        / boundary.damping_width,
        0.0,
        1.0,
    )

    return boundary.max_damping * (
        normalized_depth**boundary.damping_exponent
    )


def initialize_fields(
    config: SimulationConfig,
) -> tuple[np.ndarray, np.ndarray]:
    """Construct the fields at t=-dt and t=0."""
    grid = config.grid
    time = config.time
    initial = config.initial_condition

    if initial.kind == "gaussian":
        current = create_gaussian_pulse(grid, initial)
        initial_laplacian = compute_laplacian(current, grid)

        previous = current + 0.5 * (
            time.wave_speed * time.dt
        ) ** 2 * initial_laplacian

    elif initial.kind == "zero":
        current = create_zero_field(grid)
        previous = create_zero_field(grid)

    else:
        raise ValueError(f"Unknown initial condition: {initial.kind!r}.")

    apply_fixed_boundaries(current)
    apply_fixed_boundaries(previous)

    return previous, current


def compute_energy(
    previous: np.ndarray,
    current: np.ndarray,
    config: SimulationConfig,
) -> float:
    """Estimate the total scalar-wave energy in the domain."""
    grid = config.grid
    time = config.time

    velocity = (current - previous) / time.dt

    gradient_x = np.zeros_like(current)
    gradient_y = np.zeros_like(current)

    gradient_x[1:-1, 1:-1] = (
        current[2:, 1:-1] - current[:-2, 1:-1]
    ) / (2.0 * grid.dx)

    gradient_y[1:-1, 1:-1] = (
        current[1:-1, 2:] - current[1:-1, :-2]
    ) / (2.0 * grid.dy)

    energy_density = 0.5 * velocity**2 + 0.5 * time.wave_speed**2 * (
        gradient_x**2 + gradient_y**2
    )

    return float(np.sum(energy_density) * grid.dx * grid.dy)


def apply_source(
    field: np.ndarray,
    step_index: int,
    config: SimulationConfig,
) -> None:
    """Apply the configured continuous source to a field in place."""
    source = config.source

    if source.kind == "none":
        return

    if source.kind == "point_sine":
        time_value = step_index * config.time.dt
        source_value = source.amplitude * np.sin(
            2.0 * np.pi * source.frequency * time_value
        )

        field[source.x, source.y] += source_value
        return

    raise ValueError(f"Unknown source type: {source.kind!r}.")


def step_wave(
    previous: np.ndarray,
    current: np.ndarray,
    config: SimulationConfig,
    damping_profile: np.ndarray,
) -> np.ndarray:
    """Advance the homogeneous scalar wave equation by one time step."""
    time = config.time
    boundary = config.boundary

    laplacian = compute_laplacian(current, config.grid)
    next_field = np.zeros_like(current)

    if boundary.kind == "fixed":
        next_field[1:-1, 1:-1] = (
            2.0 * current[1:-1, 1:-1]
            - previous[1:-1, 1:-1]
            + (time.wave_speed * time.dt) ** 2
            * laplacian[1:-1, 1:-1]
        )

    elif boundary.kind == "sponge":
        gamma = damping_profile[1:-1, 1:-1]

        next_field[1:-1, 1:-1] = (
            2.0 * current[1:-1, 1:-1]
            - (1.0 - gamma * time.dt / 2.0)
            * previous[1:-1, 1:-1]
            + (time.wave_speed * time.dt) ** 2
            * laplacian[1:-1, 1:-1]
        ) / (1.0 + gamma * time.dt / 2.0)

    else:
        raise ValueError(f"Unknown boundary type: {boundary.kind!r}.")

    apply_fixed_boundaries(next_field)
    return next_field


# ============================================================
# 4. Simulation state and orchestration
# ============================================================

@dataclass
class SimulationState:
    """Mutable fields and diagnostics for an active simulation."""

    previous: np.ndarray
    current: np.ndarray
    step_index: int = 0
    energy_history: list[float] = dataclass_field(default_factory=list)


class Wave2DSimulation:
    """Own the configuration, precomputed data, and evolving wave state."""

    def __init__(self, config: SimulationConfig):
        validate_config(config)
        self.config = config

        if config.boundary.kind == "sponge":
            self.damping_profile = create_damping_profile(
                config.grid,
                config.boundary,
            )
        else:
            self.damping_profile = np.zeros(config.grid.shape)

        previous, current = initialize_fields(config)
        initial_energy = compute_energy(previous, current, config)

        self.state = SimulationState(
            previous=previous,
            current=current,
            step_index=0,
            energy_history=[initial_energy],
        )

        self.initial_energy = initial_energy
        self.normalize_energy = (
            config.source.kind == "none"
            and initial_energy > ENERGY_EPSILON
        )

    @property
    def current_energy(self) -> float:
        """Return the most recently computed energy."""
        return self.state.energy_history[-1]

    def advance(self) -> float:
        """Advance one step, inject the source, and record the energy."""
        next_step_index = self.state.step_index + 1

        next_field = step_wave(
            self.state.previous,
            self.state.current,
            self.config,
            self.damping_profile,
        )

        # Preserve the Phase 1 source ordering: inject after the wave update.
        apply_source(next_field, next_step_index, self.config)

        current_energy = compute_energy(
            self.state.current,
            next_field,
            self.config,
        )

        self.state.previous = self.state.current
        self.state.current = next_field
        self.state.step_index = next_step_index
        self.state.energy_history.append(current_energy)

        return current_energy

    def energy_status_text(self) -> str:
        """Return the energy text displayed in the animation title."""
        if self.normalize_energy:
            relative_energy = self.current_energy / self.initial_energy
            return f"Remaining energy: {100.0 * relative_energy:.2f}%"

        return f"Total energy: {self.current_energy:.4f}"

    def print_progress_if_needed(self) -> None:
        """Print energy diagnostics at the configured interval."""
        step = self.state.step_index
        total_steps = self.config.time.steps
        interval = self.config.visualization.print_energy_interval

        should_print = (
            step == 1
            or step % interval == 0
            or step == total_steps
        )

        if not should_print:
            return

        if self.normalize_energy:
            relative_energy = self.current_energy / self.initial_energy
            print(
                f"Step {step:4d}: "
                f"energy = {self.current_energy:.6f}, "
                f"remaining = {100.0 * relative_energy:.2f}%"
            )
        else:
            print(
                f"Step {step:4d}: "
                f"total energy = {self.current_energy:.6f}"
            )


# ============================================================
# 5. Visualization
# ============================================================

def add_damping_profile_figure(simulation: Wave2DSimulation) -> None:
    """Create the optional sponge-profile figure."""
    config = simulation.config
    boundary = config.boundary

    if (
        boundary.kind != "sponge"
        or not config.visualization.show_damping_profile
    ):
        return

    profile_figure, profile_axis = plt.subplots()

    profile_image = profile_axis.imshow(
        simulation.damping_profile.T,
        origin="lower",
        cmap="viridis",
    )

    profile_axis.set_title(
        "Sponge damping profile\n"
        f"width={boundary.damping_width}, "
        f"max={boundary.max_damping}, "
        f"exponent={boundary.damping_exponent:g}"
    )
    profile_axis.set_xlabel("x grid index")
    profile_axis.set_ylabel("y grid index")

    profile_figure.colorbar(
        profile_image,
        ax=profile_axis,
        label=r"Damping coefficient $\gamma(x,y)$",
    )


def create_wave_animation(
    simulation: Wave2DSimulation,
) -> FuncAnimation:
    """Create an animation whose callback advances the simulation."""
    config = simulation.config
    visualization = config.visualization

    figure, axis = plt.subplots()

    field_image = axis.imshow(
        simulation.state.current.T,
        cmap="RdBu",
        vmin=-visualization.display_limit,
        vmax=visualization.display_limit,
        origin="lower",
        animated=True,
    )

    axis.set_xlabel("x grid index")
    axis.set_ylabel("y grid index")

    figure.colorbar(
        field_image,
        ax=axis,
        label="Wave amplitude",
    )

    def update(_frame: int) -> list:
        simulation.advance()
        simulation.print_progress_if_needed()

        field_image.set_array(simulation.state.current.T)
        axis.set_title(
            "2D Scalar Wave Equation — "
            f"{config.boundary.kind.capitalize()} Boundary\n"
            f"Step {simulation.state.step_index} | "
            f"{simulation.energy_status_text()} | "
            f"Source: {config.source.kind}"
        )

        return [field_image]

    return FuncAnimation(
        figure,
        update,
        frames=config.time.steps,
        interval=visualization.animation_interval_ms,
        blit=False,
        repeat=False,
    )


def plot_energy_history(simulation: Wave2DSimulation) -> None:
    """Plot the energy recorded during the completed simulation."""
    config = simulation.config
    energy_array = np.asarray(simulation.state.energy_history)

    energy_figure, energy_axis = plt.subplots()

    if simulation.normalize_energy:
        plotted_energy = energy_array / simulation.initial_energy
        energy_axis.set_title(
            "Normalized Wave Energy — "
            f"{config.boundary.kind.capitalize()} Boundary"
        )
        energy_axis.set_ylabel("Energy / initial energy")
    else:
        plotted_energy = energy_array
        energy_axis.set_title(
            "Total Wave Energy — "
            f"{config.boundary.kind.capitalize()} Boundary, "
            f"Source: {config.source.kind}"
        )
        energy_axis.set_ylabel("Total wave energy")

    energy_axis.plot(
        np.arange(len(plotted_energy)),
        plotted_energy,
    )
    energy_axis.set_xlabel("Time step")
    energy_axis.grid(True)

    plt.show()


# ============================================================
# 6. Program entry point
# ============================================================

def run_interactive_simulation(
    config: SimulationConfig,
) -> Wave2DSimulation:
    """Validate, report, animate, and plot one simulation."""
    simulation = Wave2DSimulation(config)

    print_configuration(config)

    if config.boundary.kind == "sponge":
        print(
            f"Profile minimum:    "
            f"{simulation.damping_profile.min():.6f}"
        )
        print(
            f"Profile maximum:    "
            f"{simulation.damping_profile.max():.6f}"
        )

    print(f"Initial energy:     {simulation.initial_energy:.6f}")

    add_damping_profile_figure(simulation)
    animation = create_wave_animation(simulation)

    # Keep a live reference to the animation until the window closes.
    _ = animation
    plt.show()

    plot_energy_history(simulation)
    return simulation


def main() -> None:
    """Run the default Phase 2.1 simulation."""
    config = create_default_config()
    run_interactive_simulation(config)


if __name__ == "__main__":
    main()
