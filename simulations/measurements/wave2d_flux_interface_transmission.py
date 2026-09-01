"""Scalar-power transmission through a planar material interface."""

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
    create_planar_interface_material_map,
    create_uniform_material_map,
)
from wavesim.monitors import compute_flux_power_history
from wavesim.solver import Wave2DSimulation


SOURCE_X = 50
SOURCE_Y_START = 35
SOURCE_Y_STOP = 145

INTERFACE_INDEX = 230
TRANSMISSION_MONITOR_FACE = 250

MONITOR_TRANSVERSE_START = 0
MONITOR_TRANSVERSE_STOP = 180

LEFT_REFRACTIVE_INDEX = 1.0
RIGHT_REFRACTIVE_INDEX = 1.5

SOURCE_FREQUENCY = 0.05
SOURCE_RAMP_CYCLES = 4.0

ANALYSIS_START_STEP = 650
ANALYSIS_STOP_STEP = 850
MINIMUM_ANALYSIS_CYCLES = 3.0


@dataclass(frozen=True)
class InterfaceTransmissionResult:
    """Measured and theoretical interface-transmission results."""

    reference: AveragePower
    interface: AveragePower
    theoretical_transmission: float

    @property
    def measured_transmission(self) -> float:
        """Return transmitted power relative to the matched reference."""
        return (
            self.interface.mean_power
            / self.reference.mean_power
        )

    @property
    def absolute_error(self) -> float:
        """Return the absolute transmission-coefficient error."""
        return abs(
            self.measured_transmission
            - self.theoretical_transmission
        )

    @property
    def relative_error(self) -> float:
        """Return error relative to the theoretical transmission."""
        return (
            self.absolute_error
            / self.theoretical_transmission
        )


def theoretical_scalar_transmission(
    left_refractive_index: float,
    right_refractive_index: float,
) -> float:
    """Return the normal-incidence scalar power transmission.

    Continuity of the scalar field and its normal derivative gives

        t = 2 n_left / (n_left + n_right)

    for the transmitted field amplitude.

    Because the time-averaged scalar-wave flux is proportional to
    refractive index times amplitude squared, the power ratio is

        T = (n_right / n_left) t**2
          = 4 n_left n_right / (n_left + n_right)**2.
    """
    return (
        4.0
        * left_refractive_index
        * right_refractive_index
        / (
            left_refractive_index
            + right_refractive_index
        )
        ** 2
    )


def create_scenario(
) -> tuple[SimulationConfig, MaterialMap, MaterialMap]:
    """Create matched reference and interface material maps."""
    default = create_default_config()

    grid = replace(
        default.grid,
        nx=420,
        ny=180,
    )

    flux_monitor = FluxMonitorConfig(
        name="transmitted",
        axis="x",
        face_index=TRANSMISSION_MONITOR_FACE,
        transverse_start=MONITOR_TRANSVERSE_START,
        transverse_stop=MONITOR_TRANSVERSE_STOP,
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
        flux_monitors=(flux_monitor,),
    )

    reference_material_map = create_uniform_material_map(
        grid,
        config.material,
    )

    interface_material_map = (
        create_planar_interface_material_map(
            grid,
            config.material,
            interface_index=INTERFACE_INDEX,
            right_refractive_index=RIGHT_REFRACTIVE_INDEX,
        )
    )

    return (
        config,
        reference_material_map,
        interface_material_map,
    )


def run_simulations(
) -> tuple[Wave2DSimulation, Wave2DSimulation]:
    """Run the matched reference and interface simulations."""
    (
        config,
        reference_material_map,
        interface_material_map,
    ) = create_scenario()

    reference_simulation = Wave2DSimulation(
        config,
        material_map=reference_material_map,
    )

    interface_simulation = Wave2DSimulation(
        config,
        material_map=interface_material_map,
    )

    print("Running matched uniform reference...")

    for _ in range(config.time.steps):
        reference_simulation.advance()
        reference_simulation.print_progress_if_needed()

    print("Running planar-interface simulation...")

    for _ in range(config.time.steps):
        interface_simulation.advance()
        interface_simulation.print_progress_if_needed()

    return reference_simulation, interface_simulation


def calculate_average_transmitted_power(
    simulation: Wave2DSimulation,
) -> AveragePower:
    """Calculate average power at the transmission monitor."""
    if simulation.state.step_index < ANALYSIS_STOP_STEP:
        raise ValueError(
            "Simulation has not reached the configured "
            "transmission-analysis window."
        )

    monitor = simulation.config.flux_monitors[0]
    state = simulation.flux_monitor_states[monitor.name]

    power_history = compute_flux_power_history(
        state,
        monitor,
        simulation.config.grid,
    )

    return estimate_average_power(
        power_history,
        simulation.config.time.dt,
        start_step=ANALYSIS_START_STEP,
        stop_step=ANALYSIS_STOP_STEP,
        frequency=simulation.config.source.frequency,
        minimum_cycles=MINIMUM_ANALYSIS_CYCLES,
    )


def analyze_transmission(
    reference_simulation: Wave2DSimulation,
    interface_simulation: Wave2DSimulation,
) -> InterfaceTransmissionResult:
    """Compare interface power with the matched reference power."""
    reference = calculate_average_transmitted_power(
        reference_simulation
    )
    interface = calculate_average_transmitted_power(
        interface_simulation
    )

    if reference.mean_power <= 0.0:
        raise ValueError(
            "Reference power must be positive before calculating "
            "the transmission ratio."
        )

    theoretical_transmission = (
        theoretical_scalar_transmission(
            LEFT_REFRACTIVE_INDEX,
            RIGHT_REFRACTIVE_INDEX,
        )
    )

    return InterfaceTransmissionResult(
        reference=reference,
        interface=interface,
        theoretical_transmission=theoretical_transmission,
    )


def print_transmission_report(
    result: InterfaceTransmissionResult,
) -> None:
    """Print the interface-transmission comparison."""
    print()
    print("Scalar interface transmission")
    print("-----------------------------")
    print(
        f"Refractive indices:      "
        f"{LEFT_REFRACTIVE_INDEX:.3f} -> "
        f"{RIGHT_REFRACTIVE_INDEX:.3f}"
    )
    print(
        f"Analysis steps:          "
        f"[{ANALYSIS_START_STEP}, {ANALYSIS_STOP_STEP})"
    )
    print(
        f"Analysis cycles:         "
        f"{result.reference.cycle_count:.2f}"
    )
    print(
        f"Reference mean power:    "
        f"{result.reference.mean_power:.6f}"
    )
    print(
        f"Interface mean power:    "
        f"{result.interface.mean_power:.6f}"
    )
    print(
        f"Measured transmission:   "
        f"{result.measured_transmission:.6f}"
    )
    print(
        f"Theoretical transmission:"
        f" {result.theoretical_transmission:.6f}"
    )
    print(
        f"Absolute error:          "
        f"{result.absolute_error:.6f}"
    )
    print(
        f"Relative error:          "
        f"{100.0 * result.relative_error:.2f}%"
    )


def main() -> None:
    """Run and report the matched transmission experiment."""
    (
        reference_simulation,
        interface_simulation,
    ) = run_simulations()

    result = analyze_transmission(
        reference_simulation,
        interface_simulation,
    )

    print_transmission_report(result)


if __name__ == "__main__":
    main()