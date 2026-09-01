"""Tests for uniform-medium scalar-flux propagation."""

import unittest

import numpy as np

from simulations.measurements.wave2d_flux_propagation import (
    ANALYSIS_START_STEP,
    ANALYSIS_STOP_STEP,
    LEFT_MONITOR_FACE,
    MINIMUM_ANALYSIS_CYCLES,
    MONITOR_TRANSVERSE_START,
    MONITOR_TRANSVERSE_STOP,
    RIGHT_FAR_MONITOR_FACE,
    RIGHT_NEAR_MONITOR_FACE,
    SOURCE_FREQUENCY,
    SOURCE_RAMP_CYCLES,
    SOURCE_X,
    SOURCE_Y_START,
    SOURCE_Y_STOP,
    analyze_flux_power,
    create_scenario,
)
from wavesim.config import (
    compute_courant_number,
    validate_config,
)
from wavesim.monitors import compute_flux_power_history
from wavesim.solver import Wave2DSimulation


class FluxPropagationConfigurationTests(unittest.TestCase):
    """Verify construction of the uniform flux experiment."""

    def setUp(self) -> None:
        self.config, self.material_map = create_scenario()

    def test_scenario_parameters(self) -> None:
        config = self.config

        self.assertEqual(config.grid.nx, 300)
        self.assertEqual(config.grid.ny, 180)
        self.assertEqual(
            config.time.steps,
            ANALYSIS_STOP_STEP,
        )

        self.assertEqual(
            config.source.kind,
            "line_sine",
        )
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
        self.assertEqual(
            {
                monitor.name
                for monitor in config.flux_monitors
            },
            {
                "left",
                "right_near",
                "right_far",
            },
        )

    def test_material_is_uniform(self) -> None:
        np.testing.assert_array_equal(
            self.material_map.refractive_index,
            np.ones(self.config.grid.shape),
        )
        np.testing.assert_array_equal(
            self.material_map.wave_speed,
            np.ones(self.config.grid.shape),
        )

    def test_monitor_geometry_and_sign_orientation(self) -> None:
        monitors = {
            monitor.name: monitor
            for monitor in self.config.flux_monitors
        }

        self.assertLess(LEFT_MONITOR_FACE, SOURCE_X)
        self.assertGreater(
            RIGHT_NEAR_MONITOR_FACE,
            SOURCE_X,
        )
        self.assertGreater(
            RIGHT_FAR_MONITOR_FACE,
            RIGHT_NEAR_MONITOR_FACE,
        )

        for monitor in monitors.values():
            self.assertEqual(monitor.axis, "x")
            self.assertEqual(
                monitor.transverse_start,
                MONITOR_TRANSVERSE_START,
            )
            self.assertEqual(
                monitor.transverse_stop,
                MONITOR_TRANSVERSE_STOP,
            )

    def test_source_and_monitors_are_outside_sponge(self) -> None:
        sponge_width = self.config.boundary.damping_width
        right_sponge_start = (
            self.config.grid.nx - sponge_width
        )
        top_sponge_start = (
            self.config.grid.ny - sponge_width
        )

        self.assertGreater(SOURCE_X, sponge_width)
        self.assertLess(SOURCE_X, right_sponge_start)

        self.assertGreater(
            LEFT_MONITOR_FACE,
            sponge_width,
        )
        self.assertLess(
            RIGHT_FAR_MONITOR_FACE + 1,
            right_sponge_start,
        )

        self.assertGreaterEqual(
            MONITOR_TRANSVERSE_START,
            sponge_width,
        )
        self.assertLessEqual(
            MONITOR_TRANSVERSE_STOP,
            top_sponge_start,
        )

    def test_scenario_satisfies_numerical_constraints(self) -> None:
        validate_config(self.config)

        maximum_wave_speed = float(
            np.max(self.material_map.wave_speed)
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
        self.assertGreaterEqual(points_per_wavelength, 10.0)

    def test_analysis_window_contains_five_cycles(self) -> None:
        sample_count = (
            ANALYSIS_STOP_STEP
            - ANALYSIS_START_STEP
        )
        duration = sample_count * self.config.time.dt
        cycle_count = duration * SOURCE_FREQUENCY

        self.assertEqual(sample_count, 250)
        self.assertAlmostEqual(cycle_count, 5.0)
        self.assertGreaterEqual(
            cycle_count,
            MINIMUM_ANALYSIS_CYCLES,
        )

    def test_scenario_constructs_valid_simulation(self) -> None:
        simulation = Wave2DSimulation(
            self.config,
            material_map=self.material_map,
        )

        self.assertEqual(
            set(simulation.flux_monitor_states),
            {
                "left",
                "right_near",
                "right_far",
            },
        )

        for state in simulation.flux_monitor_states.values():
            self.assertEqual(state.steps, [])
            self.assertEqual(state.times, [])
            self.assertEqual(state.profiles, [])


class FluxPropagationRuntimeTests(unittest.TestCase):
    """Verify real signed-power propagation in a uniform medium."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.config, cls.material_map = create_scenario()
        cls.simulation = Wave2DSimulation(
            cls.config,
            material_map=cls.material_map,
        )

        for _ in range(cls.config.time.steps):
            cls.simulation.advance()

        cls.result = analyze_flux_power(cls.simulation)

    def test_flux_histories_are_complete_and_finite(self) -> None:
        expected_length = self.config.time.steps
        expected_profile_length = (
            MONITOR_TRANSVERSE_STOP
            - MONITOR_TRANSVERSE_START
        )

        for state in self.simulation.flux_monitor_states.values():
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
        monitor_by_name = {
            monitor.name: monitor
            for monitor in self.config.flux_monitors
        }

        for name, state in (
            self.simulation.flux_monitor_states.items()
        ):
            history = compute_flux_power_history(
                state,
                monitor_by_name[name],
                self.config.grid,
            )

            self.assertEqual(
                history.shape,
                (self.config.time.steps,),
            )
            self.assertTrue(np.all(np.isfinite(history)))

    def test_average_power_has_expected_direction(self) -> None:
        self.assertLess(
            self.result.left.mean_power,
            0.0,
        )
        self.assertGreater(
            self.result.right_near.mean_power,
            0.0,
        )
        self.assertGreater(
            self.result.right_far.mean_power,
            0.0,
        )

    def test_average_power_is_measurably_nonzero(self) -> None:
        self.assertGreater(
            abs(self.result.left.mean_power),
            10.0,
        )
        self.assertGreater(
            self.result.right_near.mean_power,
            10.0,
        )
        self.assertGreater(
            self.result.right_far.mean_power,
            10.0,
        )

    def test_analysis_metadata_is_correct(self) -> None:
        for response in (
            self.result.left,
            self.result.right_near,
            self.result.right_far,
        ):
            self.assertEqual(
                response.start_step,
                ANALYSIS_START_STEP,
            )
            self.assertEqual(
                response.stop_step,
                ANALYSIS_STOP_STEP,
            )
            self.assertEqual(response.sample_count, 250)
            self.assertAlmostEqual(response.duration, 100.0)
            self.assertAlmostEqual(response.cycle_count, 5.0)

    def test_right_side_power_is_consistent(self) -> None:
        self.assertLess(
            self.result.right_consistency_error,
            0.05,
        )

    def test_opposite_launch_power_is_approximately_symmetric(
        self,
    ) -> None:
        self.assertLess(
            self.result.left_right_symmetry_error,
            0.10,
        )