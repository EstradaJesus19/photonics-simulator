"""Finite-difference solver and mutable state for the 2D scalar wave model."""

from dataclasses import dataclass, field as dataclass_field

import numpy as np

from .config import (
    BoundaryConfig,
    GridConfig,
    InitialConditionConfig,
    SimulationConfig,
    validate_config,
    validate_courant_number,
)

from .materials import (
    MaterialMap,
    create_uniform_material_map,
    validate_material_map,
)

from .sources import (
    apply_source,
    create_source_profile,
)

from .monitors import (
    FieldMonitorState,
    FluxMonitorState,
    create_flux_monitor_states,
    create_monitor_states,
    record_flux_monitor_samples,
    record_monitor_samples,
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
    material_map: MaterialMap,
) -> tuple[np.ndarray, np.ndarray]:
    """Construct the fields at t=-dt and t=0."""
    grid = config.grid
    time = config.time
    initial = config.initial_condition

    if initial.kind == "gaussian":
        current = create_gaussian_pulse(grid, initial)
        initial_laplacian = compute_laplacian(current, grid)

        previous = (
            current
            + 0.5
            * time.dt**2
            * material_map.wave_speed**2
            * initial_laplacian
        )

    elif initial.kind == "zero":
        current = create_zero_field(grid)
        previous = create_zero_field(grid)

    else:
        raise ValueError(f"Unknown initial condition: {initial.kind!r}.")

    apply_fixed_boundaries(current)
    apply_fixed_boundaries(previous)

    return previous, current


def compute_energy_density(
    previous: np.ndarray,
    current: np.ndarray,
    config: SimulationConfig,
    material_map: MaterialMap,
) -> np.ndarray:
    """Return nodal leapfrog energy density at the intermediate time."""
    grid = config.grid
    time = config.time

    velocity = (current - previous) / time.dt

    previous_gradient_x = (
        previous[1:, :] - previous[:-1, :]
    ) / grid.dx
    current_gradient_x = (
        current[1:, :] - current[:-1, :]
    ) / grid.dx

    previous_gradient_y = (
        previous[:, 1:] - previous[:, :-1]
    ) / grid.dy
    current_gradient_y = (
        current[:, 1:] - current[:, :-1]
    ) / grid.dy

    potential_x = (
        current_gradient_x * previous_gradient_x
    )
    potential_y = (
        current_gradient_y * previous_gradient_y
    )

    energy_density = (
        0.5
        * velocity**2
        / material_map.wave_speed**2
    )

    # Each face contribution is shared equally by its two
    # adjacent nodal control volumes.
    energy_density[:-1, :] += 0.25 * potential_x
    energy_density[1:, :] += 0.25 * potential_x

    energy_density[:, :-1] += 0.25 * potential_y
    energy_density[:, 1:] += 0.25 * potential_y

    return energy_density


def compute_energy(
    previous: np.ndarray,
    current: np.ndarray,
    config: SimulationConfig,
    material_map: MaterialMap,
) -> float:
    """Return the leapfrog energy between two consecutive field levels."""
    energy_density = compute_energy_density(
        previous,
        current,
        config,
        material_map,
    )

    return float(
        np.sum(energy_density)
        * config.grid.dx
        * config.grid.dy
    )


def compute_energy_flux(
    previous: np.ndarray,
    current: np.ndarray,
    next_field: np.ndarray,
    config: SimulationConfig,
) -> tuple[np.ndarray, np.ndarray]:
    """Return scalar-energy fluxes on x- and y-directed faces."""
    grid = config.grid
    time = config.time

    centered_velocity = (
        next_field - previous
    ) / (2.0 * time.dt)

    gradient_x = (
        current[1:, :] - current[:-1, :]
    ) / grid.dx

    velocity_x_faces = 0.5 * (
        centered_velocity[1:, :]
        + centered_velocity[:-1, :]
    )

    flux_x = -velocity_x_faces * gradient_x

    gradient_y = (
        current[:, 1:] - current[:, :-1]
    ) / grid.dy

    velocity_y_faces = 0.5 * (
        centered_velocity[:, 1:]
        + centered_velocity[:, :-1]
    )

    flux_y = -velocity_y_faces * gradient_y

    return flux_x, flux_y


def step_wave(
    previous: np.ndarray,
    current: np.ndarray,
    config: SimulationConfig,
    material_map: MaterialMap,
    damping_profile: np.ndarray,
) -> np.ndarray:
    """Advance the variable-speed scalar wave equation by one time step."""
    time = config.time
    boundary = config.boundary

    laplacian = compute_laplacian(current, config.grid)
    wave_speed = material_map.wave_speed[1:-1, 1:-1]
    next_field = np.zeros_like(current)

    if boundary.kind == "fixed":
        next_field[1:-1, 1:-1] = (
            2.0 * current[1:-1, 1:-1]
            - previous[1:-1, 1:-1]
            + time.dt**2
            * wave_speed**2
            * laplacian[1:-1, 1:-1]
        )

    elif boundary.kind == "sponge":
        gamma = damping_profile[1:-1, 1:-1]

        next_field[1:-1, 1:-1] = (
            2.0 * current[1:-1, 1:-1]
            - (1.0 - gamma * time.dt / 2.0)
            * previous[1:-1, 1:-1]
            + time.dt**2
            * wave_speed**2
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

    def __init__(
        self,
        config: SimulationConfig,
        material_map: MaterialMap | None = None,
    ):
        validate_config(config)
        self.config = config
        self.source_profile = create_source_profile(config)

        selected_material_map = (
            create_uniform_material_map(
                config.grid,
                config.material,
            )
            if material_map is None
            else material_map
        )

        validate_material_map(
            selected_material_map,
            config.grid,
        )

        self.material_map = selected_material_map

        maximum_wave_speed = float(
            np.max(self.material_map.wave_speed)
        )

        validate_courant_number(
            config,
            maximum_wave_speed,
        )

        if config.boundary.kind == "sponge":
            self.damping_profile = create_damping_profile(
                config.grid,
                config.boundary,
            )
        else:
            self.damping_profile = np.zeros(config.grid.shape)

        previous, current = initialize_fields(
            config,
            self.material_map,
        )
        initial_energy = compute_energy(
            previous,
            current,
            config,
            self.material_map,
        )

        self.state = SimulationState(
            previous=previous,
            current=current,
            step_index=0,
            energy_history=[initial_energy],
        )

        self.monitor_states: dict[str, FieldMonitorState] = (
            create_monitor_states(
                config.monitors,
                self.state.current,
            )
        )
        self.flux_monitor_states: dict[str, FluxMonitorState] = (
            create_flux_monitor_states(config.flux_monitors)
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
            self.material_map,
            self.damping_profile,
        )

        # Preserve the Phase 1 source ordering: inject after the wave update.
        apply_source(
            next_field,
            next_step_index,
            self.config,
            self.source_profile,
        )

        if self.config.flux_monitors:
            flux_x, flux_y = compute_energy_flux(
                self.state.previous,
                self.state.current,
                next_field,
                self.config,
            )
            record_flux_monitor_samples(
                self.config.flux_monitors,
                self.flux_monitor_states,
                flux_x,
                flux_y,
                self.state.step_index,
                self.config.time.dt,
            )

        current_energy = compute_energy(
            self.state.current,
            next_field,
            self.config,
            self.material_map,
        )

        self.state.previous = self.state.current
        self.state.current = next_field
        self.state.step_index = next_step_index
        self.state.energy_history.append(current_energy)

        record_monitor_samples(
            self.config.monitors,
            self.monitor_states,
            self.state.current,
            self.state.step_index,
            self.config.time.dt,
        )

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
