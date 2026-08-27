"""Matched isolated-guide and directional-coupler experiment."""

from dataclasses import replace

import numpy as np

from wavesim.analysis import (
    HarmonicResponse,
    estimate_harmonic_response,
)
from wavesim.config import (
    FieldMonitorConfig,
    GridConfig,
    SimulationConfig,
    create_default_config,
)
from wavesim.geometry import create_rectangular_mask
from wavesim.materials import (
    MaterialMap,
    MaterialRegion,
    compose_material_regions,
    create_background_refractive_index_array,
    create_material_map_from_refractive_index,
)
from wavesim.solver import Wave2DSimulation


GRID_NX = 220
GRID_NY = 160

SPONGE_WIDTH = 20

CORE_REFRACTIVE_INDEX = 1.5
CORE_HEIGHT = 12.0

UPPER_CORE_CENTER_Y = 90.0
LOWER_CORE_CENTER_Y = 76.0

CORE_GAP = (
    UPPER_CORE_CENTER_Y
    - LOWER_CORE_CENTER_Y
    - CORE_HEIGHT
)

SOURCE_X = 35
SOURCE_Y_START = 85
SOURCE_Y_STOP = 96
SOURCE_FREQUENCY = 0.05
SOURCE_RAMP_CYCLES = 4.0

FIRST_MONITOR_X = 90
SECOND_MONITOR_X = 170

UPPER_MONITOR_Y_START = 85
UPPER_MONITOR_Y_STOP = 96

LOWER_MONITOR_Y_START = 71
LOWER_MONITOR_Y_STOP = 82

ANALYSIS_START_STEP = 750
ANALYSIS_STOP_STEP = 900


def create_core_mask(
    grid: GridConfig,
    *,
    center_y: float,
) -> np.ndarray:
    """Create one full-length straight core mask."""
    return create_rectangular_mask(
        grid,
        center_x=(
            (grid.nx - 1) * grid.dx / 2.0
        ),
        center_y=center_y,
        width=(grid.nx - 1) * grid.dx,
        height=CORE_HEIGHT,
    )


def create_scenario_pair(
) -> tuple[
    SimulationConfig,
    MaterialMap,
    MaterialMap,
]:
    """Create matched isolated-guide and coupler scenarios."""
    default = create_default_config()

    grid = replace(
        default.grid,
        nx=GRID_NX,
        ny=GRID_NY,
    )

    monitors = (
        FieldMonitorConfig(
            name="first_upper",
            kind="vertical_line",
            x=FIRST_MONITOR_X,
            y_start=UPPER_MONITOR_Y_START,
            y_stop=UPPER_MONITOR_Y_STOP,
        ),
        FieldMonitorConfig(
            name="first_lower",
            kind="vertical_line",
            x=FIRST_MONITOR_X,
            y_start=LOWER_MONITOR_Y_START,
            y_stop=LOWER_MONITOR_Y_STOP,
        ),
        FieldMonitorConfig(
            name="second_upper",
            kind="vertical_line",
            x=SECOND_MONITOR_X,
            y_start=UPPER_MONITOR_Y_START,
            y_stop=UPPER_MONITOR_Y_STOP,
        ),
        FieldMonitorConfig(
            name="second_lower",
            kind="vertical_line",
            x=SECOND_MONITOR_X,
            y_start=LOWER_MONITOR_Y_START,
            y_stop=LOWER_MONITOR_Y_STOP,
        ),
    )

    config = replace(
        default,
        grid=grid,
        time=replace(
            default.time,
            steps=ANALYSIS_STOP_STEP,
        ),
        initial_condition=replace(
            default.initial_condition,
            kind="zero",
            x0=SOURCE_X,
            y0=int(UPPER_CORE_CENTER_Y),
        ),
        source=replace(
            default.source,
            kind="line_sine",
            x=SOURCE_X,
            y=int(UPPER_CORE_CENTER_Y),
            y_start=SOURCE_Y_START,
            y_stop=SOURCE_Y_STOP,
            amplitude=0.5,
            frequency=SOURCE_FREQUENCY,
            ramp_cycles=SOURCE_RAMP_CYCLES,
        ),
        boundary=replace(
            default.boundary,
            kind="sponge",
            damping_width=SPONGE_WIDTH,
        ),
        monitors=monitors,
    )

    background = (
        create_background_refractive_index_array(
            grid,
            config.material,
        )
    )

    upper_core_mask = create_core_mask(
        grid,
        center_y=UPPER_CORE_CENTER_Y,
    )
    lower_core_mask = create_core_mask(
        grid,
        center_y=LOWER_CORE_CENTER_Y,
    )

    isolated_refractive_index = (
        compose_material_regions(
            background,
            grid,
            regions=(
                MaterialRegion(
                    mask=upper_core_mask,
                    refractive_index=(
                        CORE_REFRACTIVE_INDEX
                    ),
                ),
            ),
        )
    )

    coupled_refractive_index = (
        compose_material_regions(
            background,
            grid,
            regions=(
                MaterialRegion(
                    mask=upper_core_mask,
                    refractive_index=(
                        CORE_REFRACTIVE_INDEX
                    ),
                ),
                MaterialRegion(
                    mask=lower_core_mask,
                    refractive_index=(
                        CORE_REFRACTIVE_INDEX
                    ),
                ),
            ),
        )
    )

    isolated_map = (
        create_material_map_from_refractive_index(
            grid,
            config.material,
            isolated_refractive_index,
        )
    )
    coupled_map = (
        create_material_map_from_refractive_index(
            grid,
            config.material,
            coupled_refractive_index,
        )
    )

    return config, isolated_map, coupled_map


def run_scenario_pair(
) -> tuple[
    Wave2DSimulation,
    Wave2DSimulation,
]:
    """Run the isolated-guide and coupled-guide simulations."""
    config, isolated_map, coupled_map = (
        create_scenario_pair()
    )

    isolated = Wave2DSimulation(
        config,
        material_map=isolated_map,
    )
    coupled = Wave2DSimulation(
        config,
        material_map=coupled_map,
    )

    for _ in range(config.time.steps):
        isolated.advance()
        coupled.advance()

    return isolated, coupled


def analyze_monitor_responses(
    simulation: Wave2DSimulation,
) -> dict[str, HarmonicResponse]:
    """Estimate harmonic responses at every configured monitor."""
    if simulation.state.step_index < ANALYSIS_STOP_STEP:
        raise ValueError(
            "Simulation has not reached the configured "
            "analysis window."
        )

    return {
        name: estimate_harmonic_response(
            state.values,
            simulation.config.time.dt,
            simulation.config.source.frequency,
            start_step=ANALYSIS_START_STEP,
            stop_step=ANALYSIS_STOP_STEP,
        )
        for name, state in (
            simulation.monitor_states.items()
        )
    }


def main() -> None:
    """Run and report the directional-coupler experiment."""
    isolated, coupled = run_scenario_pair()

    isolated_responses = analyze_monitor_responses(
        isolated
    )
    coupled_responses = analyze_monitor_responses(
        coupled
    )

    isolated_second_upper = isolated_responses[
        "second_upper"
    ].amplitude
    isolated_second_lower = isolated_responses[
        "second_lower"
    ].amplitude

    coupled_first_upper = coupled_responses[
        "first_upper"
    ].amplitude
    coupled_first_lower = coupled_responses[
        "first_lower"
    ].amplitude
    coupled_second_upper = coupled_responses[
        "second_upper"
    ].amplitude
    coupled_second_lower = coupled_responses[
        "second_lower"
    ].amplitude

    isolated_downstream_ratio = (
        isolated_second_lower
        / isolated_second_upper
    )
    coupled_upstream_ratio = (
        coupled_first_lower
        / coupled_first_upper
    )
    coupled_downstream_ratio = (
        coupled_second_lower
        / coupled_second_upper
    )
    lower_window_enhancement = (
        coupled_second_lower
        / isolated_second_lower
    )

    print()
    print("Two-dimensional directional-coupler experiment")
    print("----------------------------------------------")
    print(
        f"Core gap: {CORE_GAP:.3f}"
    )
    print(
        f"Analysis steps: "
        f"[{ANALYSIS_START_STEP}, "
        f"{ANALYSIS_STOP_STEP})"
    )

    print()
    print("Isolated upper-guide reference")
    print(
        f"  Downstream upper amplitude: "
        f"{isolated_second_upper:.6f}"
    )
    print(
        f"  Downstream lower amplitude: "
        f"{isolated_second_lower:.6f}"
    )
    print(
        f"  Lower/upper ratio:          "
        f"{isolated_downstream_ratio:.6f}"
    )

    print()
    print("Directional coupler")
    print(
        f"  Upstream upper amplitude:   "
        f"{coupled_first_upper:.6f}"
    )
    print(
        f"  Upstream lower amplitude:   "
        f"{coupled_first_lower:.6f}"
    )
    print(
        f"  Upstream lower/upper ratio: "
        f"{coupled_upstream_ratio:.6f}"
    )
    print(
        f"  Downstream upper amplitude: "
        f"{coupled_second_upper:.6f}"
    )
    print(
        f"  Downstream lower amplitude: "
        f"{coupled_second_lower:.6f}"
    )
    print(
        f"  Downstream lower/upper ratio:"
        f" {coupled_downstream_ratio:.6f}"
    )

    print()
    print("Matched comparison")
    print(
        f"  Lower-window enhancement:   "
        f"{lower_window_enhancement:.6f}"
    )


if __name__ == "__main__":
    main()