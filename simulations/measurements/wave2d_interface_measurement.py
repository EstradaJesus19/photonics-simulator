"""Paired reference and interface experiments for harmonic scattering."""

from dataclasses import dataclass, replace

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
    create_planar_interface_material_map,
    create_uniform_material_map,
)
from wavesim.solver import Wave2DSimulation


SOURCE_X = 45
SOURCE_Y_START = 35
SOURCE_Y_STOP = 145

UPSTREAM_MONITOR_X = 110
INTERFACE_INDEX = 180
DOWNSTREAM_MONITOR_X = 225

MONITOR_Y_START = 60
MONITOR_Y_STOP = 120

RIGHT_REFRACTIVE_INDEX = 1.5
SOURCE_FREQUENCY = 0.05
SOURCE_RAMP_CYCLES = 4.0

ANALYSIS_START_STEP = 750
ANALYSIS_STOP_STEP = 900


@dataclass(frozen=True)
class ScatteringResponse:
    """Separated harmonic responses from the paired experiments."""

    incident: complex
    reflected: complex
    transmitted: complex
    downstream_reference: complex

    @property
    def reflection_amplitude(self) -> complex:
        return self.reflected / self.incident

    @property
    def transmission_amplitude(self) -> complex:
        return (
            self.transmitted
            / self.downstream_reference
        )

    @property
    def reflectance(self) -> float:
        return float(abs(self.reflection_amplitude) ** 2)

    @property
    def transmittance(self) -> float:
        # Scalar-wave flux correction: k2 / k1 = n2 / n1.
        return float(
            RIGHT_REFRACTIVE_INDEX
            * abs(self.transmission_amplitude) ** 2
        )


def create_scenario_pair(
) -> tuple[SimulationConfig, MaterialMap, MaterialMap]:
    """Create matched uniform-reference and interface material maps."""
    default = create_default_config()

    grid = replace(
        default.grid,
        nx=340,
        ny=180,
    )

    monitors = (
        FieldMonitorConfig(
            name="upstream",
            kind="vertical_line",
            x=UPSTREAM_MONITOR_X,
            y_start=MONITOR_Y_START,
            y_stop=MONITOR_Y_STOP,
        ),
        FieldMonitorConfig(
            name="downstream",
            kind="vertical_line",
            x=DOWNSTREAM_MONITOR_X,
            y_start=MONITOR_Y_START,
            y_stop=MONITOR_Y_STOP,
        ),
    )

    config = replace(
        default,
        grid=grid,
        time=replace(
            default.time,
            steps=900,
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

    reference_map = create_uniform_material_map(
        grid,
        config.material,
    )

    interface_map = create_planar_interface_material_map(
        grid,
        config.material,
        interface_index=INTERFACE_INDEX,
        right_refractive_index=RIGHT_REFRACTIVE_INDEX,
    )

    return config, reference_map, interface_map


def analyze_monitor(
    simulation: Wave2DSimulation,
    name: str,
) -> HarmonicResponse:
    """Estimate one configured monitor's steady harmonic response."""
    if simulation.state.step_index < ANALYSIS_STOP_STEP:
        raise ValueError(
            "Simulation has not reached the analysis window."
        )

    return estimate_harmonic_response(
        simulation.monitor_states[name].values,
        simulation.config.time.dt,
        simulation.config.source.frequency,
        start_step=ANALYSIS_START_STEP,
        stop_step=ANALYSIS_STOP_STEP,
    )


def analyze_scattering(
    reference: Wave2DSimulation,
    interface: Wave2DSimulation,
) -> ScatteringResponse:
    """Separate incident, reflected, and transmitted responses."""
    reference_upstream = analyze_monitor(
        reference,
        "upstream",
    )
    interface_upstream = analyze_monitor(
        interface,
        "upstream",
    )
    reference_downstream = analyze_monitor(
        reference,
        "downstream",
    )
    interface_downstream = analyze_monitor(
        interface,
        "downstream",
    )

    return ScatteringResponse(
        incident=reference_upstream.complex_amplitude,
        reflected=(
            interface_upstream.complex_amplitude
            - reference_upstream.complex_amplitude
        ),
        transmitted=interface_downstream.complex_amplitude,
        downstream_reference=(
            reference_downstream.complex_amplitude
        ),
    )


def run_to_completion(
    simulation: Wave2DSimulation,
) -> None:
    """Advance one simulation through its configured step count."""
    while simulation.state.step_index < simulation.config.time.steps:
        simulation.advance()


def main() -> None:
    """Run the paired headless experiment and print its measurements."""
    config, reference_map, interface_map = create_scenario_pair()

    reference = Wave2DSimulation(
        config,
        material_map=reference_map,
    )
    interface = Wave2DSimulation(
        config,
        material_map=interface_map,
    )

    run_to_completion(reference)
    run_to_completion(interface)

    response = analyze_scattering(reference, interface)

    print("Scalar interface measurement")
    print("----------------------------")
    print(
        f"|r|:             "
        f"{abs(response.reflection_amplitude):.6f}"
    )
    print(
        f"|t|:             "
        f"{abs(response.transmission_amplitude):.6f}"
    )
    print(f"R:               {response.reflectance:.6f}")
    print(f"T:               {response.transmittance:.6f}")
    print(
        f"R + T:           "
        f"{response.reflectance + response.transmittance:.6f}"
    )


if __name__ == "__main__":
    main()