"""Matplotlib visualization and interactive execution for the wave solver."""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from .config import SimulationConfig, print_configuration
from .materials import MaterialMap
from .solver import Wave2DSimulation


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

    refractive_index = (
        simulation.material_map.refractive_index
    )
    unique_refractive_indices = np.unique(refractive_index)

    if unique_refractive_indices.size > 1:
        interface_levels = 0.5 * (
            unique_refractive_indices[:-1]
            + unique_refractive_indices[1:]
        )

        axis.contour(
            refractive_index.T,
            levels=interface_levels,
            colors="black",
            linestyles="--",
            linewidths=1.0,
        )

        axis.plot(
            [],
            [],
            color="black",
            linestyle="--",
            linewidth=1.0,
            label="Material interface",
        )
        axis.legend(loc="upper right")

    axis.set_xlabel("x grid index")
    axis.set_ylabel("y grid index")

    figure.colorbar(
        field_image,
        ax=axis,
        label="Wave amplitude",
    )

    def update_title() -> None:
        axis.set_title(
            "2D E_z Wave Equation - "
            f"{config.boundary.kind.capitalize()} Boundary\n"
            f"Step {simulation.state.step_index} | "
            f"{simulation.energy_status_text()} | "
            f"Source: {config.source.kind}"
        )

    def initialize_animation() -> list:
        """Draw the initial state without advancing the simulation."""
        field_image.set_array(simulation.state.current.T)
        update_title()
        return [field_image]

    def update(_frame: int) -> list:
        simulation.advance()
        simulation.print_progress_if_needed()

        field_image.set_array(simulation.state.current.T)
        update_title()

        return [field_image]

    return FuncAnimation(
        figure,
        update,
        init_func=initialize_animation,
        frames=config.time.steps,
        interval=visualization.animation_interval_ms,
        blit=False,
        repeat=False,
    )


def plot_energy_history(simulation: Wave2DSimulation) -> None:
    """Plot the energy recorded during the completed simulation."""
    config = simulation.config
    energy_array = np.asarray(simulation.state.energy_history)

    _, energy_axis = plt.subplots()

    if simulation.normalize_energy:
        plotted_energy = energy_array / simulation.initial_energy
        energy_axis.set_title(
            "Normalized Wave Energy - "
            f"{config.boundary.kind.capitalize()} Boundary"
        )
        energy_axis.set_ylabel("Energy / initial energy")
    else:
        plotted_energy = energy_array
        energy_axis.set_title(
            "Total Wave Energy - "
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


def add_material_profile_figure(
    simulation: Wave2DSimulation,
) -> None:
    """Create the optional refractive-index-map figure."""
    config = simulation.config

    if not config.visualization.show_material_profile:
        return

    refractive_index = (
        simulation.material_map.refractive_index
    )

    material_figure, material_axis = plt.subplots()

    material_image = material_axis.imshow(
        refractive_index.T,
        origin="lower",
        cmap="viridis",
    )

    material_axis.set_title(
        "Refractive-index map\n"
        f"minimum={refractive_index.min():.3f}, "
        f"maximum={refractive_index.max():.3f}"
    )
    material_axis.set_xlabel("x grid index")
    material_axis.set_ylabel("y grid index")

    material_figure.colorbar(
        material_image,
        ax=material_axis,
        label=r"Refractive index $n(x,y)$",
    )


def run_interactive_simulation(
    config: SimulationConfig,
    material_map: MaterialMap | None = None,
) -> Wave2DSimulation:
    """Validate, report, animate, and plot one simulation."""
    simulation = Wave2DSimulation(
        config,
        material_map=material_map,
    )

    maximum_wave_speed = float(
        np.max(simulation.material_map.wave_speed)
    )

    source_wave_speed = (
        float(
            simulation.material_map.wave_speed[
                config.source.x,
                config.source.y,
            ]
        )
        if config.source.kind == "point_sine"
        else maximum_wave_speed
    )

    print_configuration(
        config,
        maximum_wave_speed,
        source_wave_speed,
    )

    print(
        f"Refractive index:   "
        f"min={simulation.material_map.refractive_index.min():.3f}, "
        f"max={simulation.material_map.refractive_index.max():.3f}"
    )
    print(
        f"Wave speed:         "
        f"min={simulation.material_map.wave_speed.min():.3f}, "
        f"max={simulation.material_map.wave_speed.max():.3f}"
    )

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

    add_material_profile_figure(simulation)
    add_damping_profile_figure(simulation)
    animation = create_wave_animation(simulation)

    # Keep a live reference to the animation until the window closes.
    _ = animation
    plt.show()

    plot_energy_history(simulation)
    return simulation
