"""Paired reference and straight dielectric-waveguide experiment."""

from dataclasses import replace

from wavesim.analysis import (
    HarmonicResponse,
    estimate_harmonic_response,
)
from wavesim.config import (
    FieldMonitorConfig,
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
    create_uniform_material_map,
)
from wavesim.solver import Wave2DSimulation


GRID_NX = 220
GRID_NY = 140

SPONGE_WIDTH = 20

WAVEGUIDE_CENTER_Y = 69.5
WAVEGUIDE_HEIGHT = 16.0
WAVEGUIDE_REFRACTIVE_INDEX = 1.5

SOURCE_X = 35
SOURCE_Y_START = 63
SOURCE_Y_STOP = 77
SOURCE_FREQUENCY = 0.05
SOURCE_RAMP_CYCLES = 4.0

FIRST_CENTER_MONITOR_X = 90
SECOND_CENTER_MONITOR_X = 150

CENTER_MONITOR_Y_START = 63
CENTER_MONITOR_Y_STOP = 77

OFFSET_MONITOR_Y_START = 90
OFFSET_MONITOR_Y_STOP = 104

ANALYSIS_START_STEP = 650
ANALYSIS_STOP_STEP = 800


def create_scenario_pair(
) -> tuple[
    SimulationConfig,
    MaterialMap,
    MaterialMap,
]:
    """Create matched uniform-reference and waveguide scenarios."""
    default = create_default_config()

    grid = replace(
        default.grid,
        nx=GRID_NX,
        ny=GRID_NY,
    )

    monitors = (
        FieldMonitorConfig(
            name="first_center",
            kind="vertical_line",
            x=FIRST_CENTER_MONITOR_X,
            y_start=CENTER_MONITOR_Y_START,
            y_stop=CENTER_MONITOR_Y_STOP,
        ),
        FieldMonitorConfig(
            name="second_center",
            kind="vertical_line",
            x=SECOND_CENTER_MONITOR_X,
            y_start=CENTER_MONITOR_Y_START,
            y_stop=CENTER_MONITOR_Y_STOP,
        ),
        FieldMonitorConfig(
            name="second_offset",
            kind="vertical_line",
            x=SECOND_CENTER_MONITOR_X,
            y_start=OFFSET_MONITOR_Y_START,
            y_stop=OFFSET_MONITOR_Y_STOP,
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
            y0=grid.ny // 2,
        ),
        source=replace(
            default.source,
            kind="line_sine",
            x=SOURCE_X,
            y=grid.ny // 2,
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

    reference_map = create_uniform_material_map(
        grid,
        config.material,
    )

    background = (
        create_background_refractive_index_array(
            grid,
            config.material,
        )
    )

    waveguide_mask = create_rectangular_mask(
        grid,
        center_x=(grid.nx - 1) * grid.dx / 2.0,
        center_y=WAVEGUIDE_CENTER_Y,
        width=(grid.nx - 1) * grid.dx,
        height=WAVEGUIDE_HEIGHT,
    )

    waveguide_refractive_index = (
        compose_material_regions(
            background,
            grid,
            regions=(
                MaterialRegion(
                    mask=waveguide_mask,
                    refractive_index=(
                        WAVEGUIDE_REFRACTIVE_INDEX
                    ),
                ),
            ),
        )
    )

    waveguide_map = (
        create_material_map_from_refractive_index(
            grid,
            config.material,
            waveguide_refractive_index,
        )
    )

    return config, reference_map, waveguide_map


def run_scenario_pair(
) -> tuple[
    Wave2DSimulation,
    Wave2DSimulation,
]:
    """Run the matched reference and waveguide simulations."""
    config, reference_map, waveguide_map = (
        create_scenario_pair()
    )

    reference = Wave2DSimulation(
        config,
        material_map=reference_map,
    )
    waveguide = Wave2DSimulation(
        config,
        material_map=waveguide_map,
    )

    for _ in range(config.time.steps):
        reference.advance()
        waveguide.advance()

    return reference, waveguide


def analyze_monitor_responses(
    simulation: Wave2DSimulation,
) -> dict[str, HarmonicResponse]:
    """Estimate steady harmonic responses at all monitors."""
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
    """Run and report the straight-waveguide experiment."""
    reference, waveguide = run_scenario_pair()

    reference_responses = analyze_monitor_responses(
        reference
    )
    waveguide_responses = analyze_monitor_responses(
        waveguide
    )

    reference_center = reference_responses[
        "second_center"
    ].amplitude
    reference_offset = reference_responses[
        "second_offset"
    ].amplitude

    waveguide_core = waveguide_responses[
        "second_center"
    ].amplitude
    waveguide_cladding = waveguide_responses[
        "second_offset"
    ].amplitude

    reference_contrast = (
        reference_center / reference_offset
    )
    waveguide_contrast = (
        waveguide_core / waveguide_cladding
    )

    core_window_enhancement = (
        waveguide_core / reference_center
    )
    cladding_window_ratio = (
        waveguide_cladding / reference_offset
    )
    contrast_improvement = (
        waveguide_contrast / reference_contrast
    )

    print()
    print("Straight dielectric-waveguide experiment")
    print("----------------------------------------")
    print(
        f"Analysis steps: "
        f"[{ANALYSIS_START_STEP}, "
        f"{ANALYSIS_STOP_STEP})"
    )

    print()
    print("Uniform reference")
    print(
        f"  Downstream center amplitude:  "
        f"{reference_center:.6f}"
    )
    print(
        f"  Downstream offset amplitude:  "
        f"{reference_offset:.6f}"
    )
    print(
        f"  Center/offset contrast:       "
        f"{reference_contrast:.6f}"
    )

    print()
    print("Dielectric waveguide")
    print(
        f"  Downstream core amplitude:    "
        f"{waveguide_core:.6f}"
    )
    print(
        f"  Downstream cladding amplitude:"
        f" {waveguide_cladding:.6f}"
    )
    print(
        f"  Core/cladding contrast:       "
        f"{waveguide_contrast:.6f}"
    )

    print()
    print("Matched comparison")
    print(
        f"  Core-window enhancement:      "
        f"{core_window_enhancement:.6f}"
    )
    print(
        f"  Cladding-window ratio:        "
        f"{cladding_window_ratio:.6f}"
    )
    print(
        f"  Contrast improvement:         "
        f"{contrast_improvement:.6f}"
    )


if __name__ == "__main__":
    main()