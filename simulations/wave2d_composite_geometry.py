"""Run a 2D E_z simulation with nested dielectric regions."""

from dataclasses import replace

from wavesim.config import (
    SimulationConfig,
    create_default_config,
)
from wavesim.materials import (
    MaterialMap,
    add_rectangular_region,
    create_background_refractive_index_array,
    create_material_map_from_refractive_index,
)


OUTER_X_START = 110
OUTER_X_STOP = 170
OUTER_Y_START = 45
OUTER_Y_STOP = 115
OUTER_REFRACTIVE_INDEX = 1.5

CORE_X_START = 130
CORE_X_STOP = 155
CORE_Y_START = 65
CORE_Y_STOP = 95
CORE_REFRACTIVE_INDEX = 2.0


def create_scenario() -> tuple[SimulationConfig, MaterialMap]:
    """Create the Phase 2.5 composite-geometry scenario."""
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

    refractive_index = (
        create_background_refractive_index_array(
            grid,
            config.material,
        )
    )

    refractive_index = add_rectangular_region(
        refractive_index,
        grid,
        x_start=OUTER_X_START,
        x_stop=OUTER_X_STOP,
        y_start=OUTER_Y_START,
        y_stop=OUTER_Y_STOP,
        region_refractive_index=(
            OUTER_REFRACTIVE_INDEX
        ),
    )

    refractive_index = add_rectangular_region(
        refractive_index,
        grid,
        x_start=CORE_X_START,
        x_stop=CORE_X_STOP,
        y_start=CORE_Y_START,
        y_stop=CORE_Y_STOP,
        region_refractive_index=(
            CORE_REFRACTIVE_INDEX
        ),
    )

    material_map = (
        create_material_map_from_refractive_index(
            grid,
            config.material,
            refractive_index,
        )
    )

    return config, material_map


def main() -> None:
    """Run the Phase 2.5 composite-geometry scenario."""
    # Defer Matplotlib so create_scenario() remains usable headlessly.
    from wavesim.visualization import run_interactive_simulation

    config, material_map = create_scenario()

    run_interactive_simulation(
        config,
        material_map=material_map,
    )


if __name__ == "__main__":
    main()