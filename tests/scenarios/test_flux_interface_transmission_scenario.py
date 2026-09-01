"""Tests for scalar-power transmission through a planar interface."""

import unittest

import numpy as np

from simulations.measurements.wave2d_flux_interface_transmission import (
    ANALYSIS_START_STEP,
    ANALYSIS_STOP_STEP,
    INTERFACE_INDEX,
    LEFT_REFRACTIVE_INDEX,
    MINIMUM_ANALYSIS_CYCLES,
    MONITOR_TRANSVERSE_START,
    MONITOR_TRANSVERSE_STOP,
    RIGHT_REFRACTIVE_INDEX,
    SOURCE_FREQUENCY,
    SOURCE_RAMP_CYCLES,
    SOURCE_X,
    SOURCE_Y_START,
    SOURCE_Y_STOP,
    TRANSMISSION_MONITOR_FACE,
    analyze_transmission,
    create_scenario,
    theoretical_scalar_transmission,
)
from wavesim.config import (
    compute_courant_number,
    validate_config,
)
from wavesim.monitors import compute_flux_power_history
from wavesim.solver import Wave2DSimulation


class InterfaceTransmissionConfigurationTests(
    unittest.TestCase
):
    """Verify construction of the matched transmission experiment."""

    def setUp(self) -> None:
        (
            self.config,
            self.reference_material_map,
            self.interface_material_map,
        ) = create_scenario()

    def test_scenario_parameters(self) -> None:
        config = self.config

        self.assertEqual(config.grid.nx, 420)
        self.assertEqual(config.grid.ny, 180)
        self.assertEqual(
            config.time.steps,
            ANALYSIS_STOP_STEP,
        )

        self.assertEqual(config.source.kind, "line_sine")
        self.assertEqual(config.source.x, SOURCE_X)
        self.assertEqual(
            config.source.y_start,
            SOURCE_Y_START,
        )
        self.assertEqual(
            config.source.y_stop,
            SOURCE_Y_STOP,
        )
        self.assertEqual(
            config.source.frequency,
            SOURCE_FREQUENCY,
        )
        self.assertEqual(
            config.source.ramp_cycles,
            SOURCE_RAMP_CYCLES,
        )

        self.assertEqual(config.monitors, ())
        self.assertEqual(len(config.flux_monitors), 1)

    def test_reference_material_is_uniform(self) -> None:
        np.testing.assert_array_equal(
            self.reference_material_map.refractive_index,
            np.full(
                self.config.grid.shape,
                LEFT_REFRACTIVE_INDEX,
            ),
        )

    def test_interface_material_has_expected_regions(self) -> None:
        refractive_index = (
            self.interface_material_map.refractive_index
        )

        np.testing.assert_array_equal(
            refractive_index[:INTERFACE_INDEX, :],
            np.full(
                (
                    INTERFACE_INDEX,
                    self.config.grid.ny,
                ),
                LEFT_REFRACTIVE_INDEX,
            ),
        )

        np.testing.assert_array_equal(
            refractive_index[INTERFACE_INDEX:, :],
            np.full(
                (
                    self.config.grid.nx
                    - INTERFACE_INDEX,
                    self.config.grid.ny,
                ),
                RIGHT_REFRACTIVE_INDEX,
            ),
        )

    def test_monitor_is_inside_transmitted_medium(self) -> None:
        monitor = self.config.flux_monitors[0]

        self.assertEqual(monitor.name, "transmitted")
        self.assertEqual(monitor.axis, "x")
        self.assertEqual(
            monitor.face_index,
            TRANSMISSION_MONITOR_FACE,
        )
        self.assertEqual(
            monitor.transverse_start,
            MONITOR_TRANSVERSE_START,
        )
        self.assertEqual(
            monitor.transverse_stop,
            MONITOR_TRANSVERSE_STOP,
        )

        self.assertLess(SOURCE_X, INTERFACE_INDEX)
        self.assertLess(
            INTERFACE_INDEX,
            TRANSMISSION_MONITOR_FACE,
        )

        refractive_index = (
            self.interface_material_map.refractive_index
        )

        self.assertEqual(
            refractive_index[
                TRANSMISSION_MONITOR_FACE,
                0,
            ],
            RIGHT_REFRACTIVE_INDEX,
        )
        self.assertEqual(
            refractive_index[
                TRANSMISSION_MONITOR_FACE + 1,
                0,
            ],
            RIGHT_REFRACTIVE_INDEX,
        )

    def test_x_geometry_is_outside_sponge(self) -> None:
        sponge_width = self.config.boundary.damping_width
        right_sponge_start = (
            self.config.grid.nx - sponge_width
        )

        self.assertGreater(SOURCE_X, sponge_width)
        self.assertGreater(INTERFACE_INDEX, sponge_width)
        self.assertGreater(
            TRANSMISSION_MONITOR_FACE,
            sponge_width,
        )

        self.assertLess(SOURCE_X, right_sponge_start)
        self.assertLess(INTERFACE_INDEX, right_sponge_start)
        self.assertLess(
            TRANSMISSION_MONITOR_FACE + 1,
            right_sponge_start,
        )

    def test_scenario_satisfies_numerical_constraints(
        self,
    ) -> None:
        validate_config(self.config)

        maximum_wave_speed = float(
            np.max(
                self.interface_material_map.wave_speed
            )
        )

        courant = compute_courant_number(
            self.config,
            maximum_wave_speed,
        )

        wavelength = (
            maximum_wave_speed
            / self.config.source.frequency
        )

        points_per_wavelength = (
            wavelength
            / max(
                self.config.grid.dx,
                self.config.grid.dy,
            )
        )

        self.assertLessEqual(courant, 1.0)
        self.assertGreaterEqual(
            points_per_wavelength,
            10.0,
        )

    def test_analysis_window_contains_four_cycles(
        self,
    ) -> None:
        sample_count = (
            ANALYSIS_STOP_STEP
            - ANALYSIS_START_STEP
        )
        duration = sample_count * self.config.time.dt
        cycle_count = duration * SOURCE_FREQUENCY

        self.assertEqual(sample_count, 200)
        self.assertAlmostEqual(duration, 80.0)
        self.assertAlmostEqual(cycle_count, 4.0)
        self.assertGreaterEqual(
            cycle_count,
            MINIMUM_ANALYSIS_CYCLES,
        )

    def test_theoretical_transmission(self) -> None:
        transmission = theoretical_scalar_transmission(
            LEFT_REFRACTIVE_INDEX,
            RIGHT_REFRACTIVE_INDEX,
        )

        self.assertAlmostEqual(transmission, 0.96)

    def test_both_material_maps_construct_simulations(
        self,
    ) -> None:
        for material_map in (
            self.reference_material_map,
            self.interface_material_map,
        ):
            simulation = Wave2DSimulation(
                self.config,
                material_map=material_map,
            )

            self.assertEqual(
                set(simulation.flux_monitor_states),
                {"transmitted"},
            )


class InterfaceTransmissionRuntimeTests(unittest.TestCase):
    """Verify measured transmission against scalar-wave theory."""

    @classmethod
    def setUpClass(cls) -> None:
        (
            cls.config,
            cls.reference_material_map,
            cls.interface_material_map,
        ) = create_scenario()

        cls.reference_simulation = Wave2DSimulation(
            cls.config,
            material_map=cls.reference_material_map,
        )

        cls.interface_simulation = Wave2DSimulation(
            cls.config,
            material_map=cls.interface_material_map,
        )

        for _ in range(cls.config.time.steps):
            cls.reference_simulation.advance()
            cls.interface_simulation.advance()

        cls.result = analyze_transmission(
            cls.reference_simulation,
            cls.interface_simulation,
        )

    def test_flux_histories_are_complete_and_finite(
        self,
    ) -> None:
        expected_length = self.config.time.steps
        expected_profile_length = (
            MONITOR_TRANSVERSE_STOP
            - MONITOR_TRANSVERSE_START
        )

        for simulation in (
            self.reference_simulation,
            self.interface_simulation,
        ):
            state = simulation.flux_monitor_states[
                "transmitted"
            ]

            self.assertEqual(
                len(state.steps),
                expected_length,
            )
            self.assertEqual(
                len(state.times),
                expected_length,
            )
            self.assertEqual(
                len(state.profiles),
                expected_length,
            )
            self.assertEqual(
                state.steps,
                list(range(expected_length)),
            )

            np.testing.assert_allclose(
                state.times,
                np.arange(expected_length)
                * self.config.time.dt,
            )

            for profile in state.profiles:
                self.assertEqual(
                    profile.shape,
                    (expected_profile_length,),
                )
                self.assertTrue(
                    np.all(np.isfinite(profile))
                )
                self.assertFalse(profile.flags.writeable)

    def test_power_histories_are_finite(self) -> None:
        monitor = self.config.flux_monitors[0]

        for simulation in (
            self.reference_simulation,
            self.interface_simulation,
        ):
            state = simulation.flux_monitor_states[
                monitor.name
            ]

            history = compute_flux_power_history(
                state,
                monitor,
                self.config.grid,
            )

            self.assertEqual(
                history.shape,
                (self.config.time.steps,),
            )
            self.assertTrue(np.all(np.isfinite(history)))

    def test_average_powers_are_positive_and_nonzero(
        self,
    ) -> None:
        self.assertGreater(
            self.result.reference.mean_power,
            10.0,
        )
        self.assertGreater(
            self.result.interface.mean_power,
            10.0,
        )

    def test_analysis_metadata_is_correct(self) -> None:
        for response in (
            self.result.reference,
            self.result.interface,
        ):
            self.assertEqual(
                response.start_step,
                ANALYSIS_START_STEP,
            )
            self.assertEqual(
                response.stop_step,
                ANALYSIS_STOP_STEP,
            )
            self.assertEqual(response.sample_count, 200)
            self.assertAlmostEqual(response.duration, 80.0)
            self.assertAlmostEqual(response.cycle_count, 4.0)

    def test_transmission_has_physical_range(self) -> None:
        self.assertGreater(
            self.result.measured_transmission,
            0.0,
        )
        self.assertLessEqual(
            self.result.measured_transmission,
            1.0,
        )

    def test_transmission_matches_scalar_theory(self) -> None:
        self.assertAlmostEqual(
            self.result.theoretical_transmission,
            0.96,
        )

        self.assertLess(
            self.result.absolute_error,
            0.02,
        )
        self.assertLess(
            self.result.relative_error,
            0.02,
        )


if __name__ == "__main__":
    unittest.main()