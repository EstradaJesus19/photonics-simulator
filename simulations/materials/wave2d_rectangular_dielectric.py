"""Run a 2D E_z simulation with one rectangular dielectric region."""

from dataclasses import replace

from wavesim.config import (
    SimulationConfig,
    create_default_config,
)
from wavesim.materials import (
    MaterialMap,
    create_rectangular_material_map,
)


RECTANGLE_X_START = 110
RECTANGLE_X_STOP = 160
RECTANGLE_Y_START = 50
RECTANGLE_Y_STOP = 110
RECTANGLE_REFRACTIVE_INDEX = 1.5


def create_scenario() -> tuple[SimulationConfig, MaterialMap]:
    """Create the Phase 2.4 rectangular-dielectric scenario."""
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

    material_map = create_rectangular_material_map(
        grid,
        config.material,
        x_start=RECTANGLE_X_START,
        x_stop=RECTANGLE_X_STOP,
        y_start=RECTANGLE_Y_START,
        y_stop=RECTANGLE_Y_STOP,
        rectangle_refractive_index=(
            RECTANGLE_REFRACTIVE_INDEX
        ),
    )

    return config, material_map


def main() -> None:
    """Run the Phase 2.4 rectangular-dielectric scenario."""
    # Defer Matplotlib so create_scenario() remains usable headlessly.
    from wavesim.visualization import run_interactive_simulation

    config, material_map = create_scenario()

    run_interactive_simulation(
        config,
        material_map=material_map,
    )


if __name__ == "__main__":
    main()