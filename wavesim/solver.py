"""Finite-difference solver and mutable state for the 2D scalar wave model."""

from dataclasses import dataclass, field as dataclass_field

import numpy as np

from .config import (
    BoundaryConfig,
    GridConfig,
    InitialConditionConfig,
    SimulationConfig,
    validate_config,
)


ENERGY_EPSILON = 1e-12


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
