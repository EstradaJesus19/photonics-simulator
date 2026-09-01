"""Uniform-medium validation of signed scalar-energy flux."""

from dataclasses import dataclass, replace

from wavesim.analysis import (
    AveragePower,
    estimate_average_power,
)
from wavesim.config import (
    FluxMonitorConfig,
    SimulationConfig,
    create_default_config,
)
from wavesim.materials import (
    MaterialMap,
    create_uniform_material_map,
)
from wavesim.monitors import compute_flux_power_history
from wavesim.solver import Wave2DSimulation


SOURCE_X = 130
SOURCE_Y_START = 35
SOURCE_Y_STOP = 145

LEFT_MONITOR_FACE = 90
RIGHT_NEAR_MONITOR_FACE = 170
RIGHT_FAR_MONITOR_FACE = 205

MONITOR_TRANSVERSE_START = 25
MONITOR_TRANSVERSE_STOP = 155

SOURCE_FREQUENCY = 0.05
SOURCE_RAMP_CYCLES = 4.0

ANALYSIS_START_STEP = 450
ANALYSIS_STOP_STEP = 700
MINIMUM_ANALYSIS_CYCLES = 3.0


@dataclass(frozen=True)
class FluxPropagationResult:
    """Average signed powers from the uniform-medium experiment."""

    left: AveragePower
    right_near: AveragePower
    right_far: AveragePower

    @property
    def right_consistency_error(self) -> float:
        """Return relative disagreement between right-side monitors."""
        scale = max(
            abs(self.right_near.mean_power),
            abs(self.right_far.mean_power),
        )

        return (
            abs(
                self.right_far.mean_power
                - self.right_near.mean_power
            )
            / scale
        )

    @property
    def left_right_symmetry_error(self) -> float:
        """Return relative disagreement of opposite power magnitudes."""
        left_magnitude = abs(self.left.mean_power)
        right_magnitude = abs(self.right_near.mean_power)
        scale = max(left_magnitude, right_magnitude)

        return abs(
            left_magnitude - right_magnitude
        ) / scale


def create_scenario() -> tuple[SimulationConfig, MaterialMap]:
    """Create the uniform-medium scalar-flux experiment."""
    default = create_default_config()

    grid = replace(
        default.grid,
        nx=300,
        ny=180,
    )

    flux_monitors = (
        FluxMonitorConfig(
            name="left",
            axis="x",
            face_index=LEFT_MONITOR_FACE,
            transverse_start=MONITOR_TRANSVERSE_START,
            transverse_stop=MONITOR_TRANSVERSE_STOP,
        ),
        FluxMonitorConfig(
            name="right_near",
            axis="x",
            face_index=RIGHT_NEAR_MONITOR_FACE,
            transverse_start=MONITOR_TRANSVERSE_START,
            transverse_stop=MONITOR_TRANSVERSE_STOP,
        ),
        FluxMonitorConfig(
            name="right_far",
            axis="x",
            face_index=RIGHT_FAR_MONITOR_FACE,
            transverse_start=MONITOR_TRANSVERSE_START,
            transverse_stop=MONITOR_TRANSVERSE_STOP,
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
            damping_width=25,
        ),
        monitors=(),
        flux_monitors=flux_monitors,
    )

    material_map = create_uniform_material_map(
        grid,
        config.material,
    )

    return config, material_map


def run_simulation() -> Wave2DSimulation:
    """Run the configured flux-propagation experiment."""
    config, material_map = create_scenario()

    simulation = Wave2DSimulation(
        config,
        material_map=material_map,
    )

    for _ in range(config.time.steps):
        simulation.advance()
        simulation.print_progress_if_needed()

    return simulation


def analyze_flux_power(
    simulation: Wave2DSimulation,
) -> FluxPropagationResult:
    """Calculate steady-window average power at every flux monitor."""
    if simulation.state.step_index < ANALYSIS_STOP_STEP:
        raise ValueError(
            "Simulation has not reached the configured "
            "flux-analysis window."
        )

    monitor_by_name = {
        monitor.name: monitor
        for monitor in simulation.config.flux_monitors
    }

    responses: dict[str, AveragePower] = {}

    for name, monitor in monitor_by_name.items():
        state = simulation.flux_monitor_states[name]

        power_history = compute_flux_power_history(
            state,
            monitor,
            simulation.config.grid,
        )

        responses[name] = estimate_average_power(
            power_history,
            simulation.config.time.dt,
            start_step=ANALYSIS_START_STEP,
            stop_step=ANALYSIS_STOP_STEP,
            frequency=simulation.config.source.frequency,
            minimum_cycles=MINIMUM_ANALYSIS_CYCLES,
        )

    return FluxPropagationResult(
        left=responses["left"],
        right_near=responses["right_near"],
        right_far=responses["right_far"],
    )


def print_flux_report(
    result: FluxPropagationResult,
) -> None:
    """Print the signed-power validation result."""
    print()
    print("Uniform scalar-flux propagation")
    print("--------------------------------")
    print(
        f"Analysis steps:          "
        f"[{ANALYSIS_START_STEP}, {ANALYSIS_STOP_STEP})"
    )
    print(
        f"Analysis cycles:         "
        f"{result.left.cycle_count:.2f}"
    )
    print(
        f"Left mean power:         "
        f"{result.left.mean_power:.6f}"
    )
    print(
        f"Right-near mean power:   "
        f"{result.right_near.mean_power:.6f}"
    )
    print(
        f"Right-far mean power:    "
        f"{result.right_far.mean_power:.6f}"
    )
    print(
        f"Right consistency error: "
        f"{100.0 * result.right_consistency_error:.2f}%"
    )
    print(
        f"Left/right symmetry:     "
        f"{100.0 * result.left_right_symmetry_error:.2f}%"
    )
    print(
        f"Left transported energy: "
        f"{result.left.transported_energy:.6f}"
    )
    print(
        f"Near transported energy: "
        f"{result.right_near.transported_energy:.6f}"
    )
    print(
        f"Far transported energy:  "
        f"{result.right_far.transported_energy:.6f}"
    )


def main() -> None:
    """Run, analyze, and report the flux experiment."""
    simulation = run_simulation()
    result = analyze_flux_power(simulation)
    print_flux_report(result)


if __name__ == "__main__":
    main()