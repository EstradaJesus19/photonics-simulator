"""Uniform-medium scenario with controlled line-source excitation."""

from dataclasses import replace

import numpy as np

from wavesim.analysis import (
    HarmonicResponse,
    estimate_harmonic_response,
)
from wavesim.config import (
    FieldMonitorConfig,
    SimulationConfig,
    create_default_config,
)
from wavesim.materials import (
    MaterialMap,
    create_uniform_material_map,
)
from wavesim.solver import Wave2DSimulation


SOURCE_X = 45
SOURCE_Y_START = 35
SOURCE_Y_STOP = 145

FIRST_MONITOR_X = 90
SECOND_MONITOR_X = 125
MONITOR_Y_START = 60
MONITOR_Y_STOP = 120

SOURCE_FREQUENCY = 0.05
SOURCE_RAMP_CYCLES = 4.0

ANALYSIS_START_STEP = 450
ANALYSIS_STOP_STEP = 700


def create_scenario() -> tuple[SimulationConfig, MaterialMap]:
    """Create the controlled uniform-medium propagation scenario."""
    default = create_default_config()

    grid = replace(
        default.grid,
        nx=260,
        ny=180,
    )

    monitors = (
        FieldMonitorConfig(
            name="first",
            kind="vertical_line",
            x=FIRST_MONITOR_X,
            y_start=MONITOR_Y_START,
            y_stop=MONITOR_Y_STOP,
        ),
        FieldMonitorConfig(
            name="second",
            kind="vertical_line",
            x=SECOND_MONITOR_X,
            y_start=MONITOR_Y_START,
            y_stop=MONITOR_Y_STOP,
        ),
    )

    config = replace(
        default,
        grid=grid,
        time=replace(
            default.time,
            steps=700,
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
            damping_width=25,
        ),
        monitors=monitors,
    )

    material_map = create_uniform_material_map(
        grid,
        config.material,
    )

    return config, material_map


def analyze_monitor_responses(
    simulation: Wave2DSimulation,
) -> dict[str, HarmonicResponse]:
    """Analyze the steady-state response at every configured monitor."""
    if simulation.state.step_index < ANALYSIS_STOP_STEP:
        raise ValueError(
            "Simulation has not reached the configured analysis window."
        )

    return {
        name: estimate_harmonic_response(
            state.values,
            simulation.config.time.dt,
            simulation.config.source.frequency,
            start_step=ANALYSIS_START_STEP,
            stop_step=ANALYSIS_STOP_STEP,
        )
        for name, state in simulation.monitor_states.items()
    }


def main() -> None:
    """Run and report the controlled line-source scenario."""
    from wavesim.visualization import run_interactive_simulation

    config, material_map = create_scenario()

    simulation = run_interactive_simulation(
        config,
        material_map=material_map,
        monitor_analysis_window=(
            ANALYSIS_START_STEP,
            ANALYSIS_STOP_STEP,
        ),
    )

    responses = analyze_monitor_responses(simulation)

    first = responses["first"]
    second = responses["second"]

    response_ratio = (
        second.complex_amplitude
        / first.complex_amplitude
    )

    print()
    print("Controlled-source harmonic response")
    print("-----------------------------------")
    print(
        f"Analysis steps:     "
        f"[{ANALYSIS_START_STEP}, {ANALYSIS_STOP_STEP})"
    )
    print(f"Analysis cycles:    {first.cycle_count:.2f}")
    print(f"First amplitude:    {first.amplitude:.6f}")
    print(f"First phase:        {first.phase:.6f} rad")
    print(f"Second amplitude:   {second.amplitude:.6f}")
    print(f"Second phase:       {second.phase:.6f} rad")
    print(f"Amplitude ratio:    {abs(response_ratio):.6f}")
    print(
        f"Wrapped phase:      "
        f"{np.angle(response_ratio):.6f} rad"
    )


if __name__ == "__main__":
    main()
