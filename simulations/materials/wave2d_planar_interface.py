"""Run a 2D E_z wave simulation with one planar dielectric interface."""

from dataclasses import replace

from wavesim.config import (
    SimulationConfig,
    create_default_config,
)
from wavesim.materials import (
    MaterialMap,
    create_planar_interface_material_map,
)


INTERFACE_INDEX = 120
RIGHT_REFRACTIVE_INDEX = 1.5


def create_scenario() -> tuple[SimulationConfig, MaterialMap]:
    """Create the Phase 2.3 planar-interface configuration and map."""
    default = create_default_config()

    grid = replace(
        default.grid,
        nx=240,
        ny=160,
    )

    config = replace(
        default,
        grid=grid,
        time=replace(
            default.time,
            steps=600,
        ),
        initial_condition=replace(
            default.initial_condition,
            kind="zero",
            x0=60,
            y0=grid.ny // 2,
        ),
        source=replace(
            default.source,
            kind="point_sine",
            x=60,
            y=grid.ny // 2,
            frequency=0.05,
        ),
        boundary=replace(
            default.boundary,
            kind="sponge",
            damping_width=25,
        ),
    )

    material_map = create_planar_interface_material_map(
        grid,
        config.material,
        interface_index=INTERFACE_INDEX,
        right_refractive_index=RIGHT_REFRACTIVE_INDEX,
    )

    return config, material_map


def main() -> None:
    """Run the Phase 2.3 planar-interface scenario."""
    # Defer Matplotlib so create_scenario() remains usable headlessly.
    from wavesim.visualization import run_interactive_simulation

    config, material_map = create_scenario()

    run_interactive_simulation(
        config,
        material_map=material_map,
    )


if __name__ == "__main__":
    main()