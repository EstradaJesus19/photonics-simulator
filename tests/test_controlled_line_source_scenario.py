"""Tests for the controlled line-source propagation scenario."""

import unittest

import numpy as np

from simulations.wave2d_controlled_line_source import (
    ANALYSIS_START_STEP,
    ANALYSIS_STOP_STEP,
    FIRST_MONITOR_X,
    MONITOR_Y_START,
    MONITOR_Y_STOP,
    SECOND_MONITOR_X,
    SOURCE_FREQUENCY,
    SOURCE_RAMP_CYCLES,
    SOURCE_X,
    SOURCE_Y_START,
    SOURCE_Y_STOP,
    analyze_monitor_responses,
    create_scenario,
)
from wavesim.config import (
    compute_courant_number,
    validate_config,
)
from wavesim.solver import Wave2DSimulation


class ControlledLineSourceConfigurationTests(unittest.TestCase):
    """Verify controlled-source scenario construction."""

    def setUp(self) -> None:
        self.config, self.material_map = create_scenario()

    def test_scenario_parameters(self) -> None:
        config = self.config

        self.assertEqual(config.grid.nx, 260)
        self.assertEqual(config.grid.ny, 180)
        self.assertEqual(config.time.steps, 700)

        self.assertEqual(config.source.kind, "line_sine")
        self.assertEqual(config.source.x, SOURCE_X)
        self.assertEqual(config.source.y_start, SOURCE_Y_START)
        self.assertEqual(config.source.y_stop, SOURCE_Y_STOP)
        self.assertEqual(
            config.source.frequency,
            SOURCE_FREQUENCY,
        )
        self.assertEqual(
            config.source.ramp_cycles,
            SOURCE_RAMP_CYCLES,
        )

        self.assertEqual(config.boundary.kind, "sponge")
        self.assertEqual(config.boundary.damping_width, 25)

    def test_material_is_uniform(self) -> None:
        np.testing.assert_array_equal(
            self.material_map.refractive_index,
            np.ones(self.config.grid.shape),
        )
        np.testing.assert_array_equal(
            self.material_map.wave_speed,
            np.ones(self.config.grid.shape),
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
        self.assertGreater(SOURCE_Y_START, sponge_width)
        self.assertLess(SOURCE_Y_STOP, top_sponge_start)

        self.assertGreater(FIRST_MONITOR_X, SOURCE_X)
        self.assertGreater(SECOND_MONITOR_X, FIRST_MONITOR_X)
        self.assertLess(SECOND_MONITOR_X, right_sponge_start)

        self.assertGreater(MONITOR_Y_START, sponge_width)
        self.assertLess(MONITOR_Y_STOP, top_sponge_start)

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
            ANALYSIS_STOP_STEP - ANALYSIS_START_STEP
        )
        duration = sample_count * self.config.time.dt
        cycle_count = duration * self.config.source.frequency

        self.assertEqual(sample_count, 250)
        self.assertAlmostEqual(cycle_count, 5.0)

    def test_scenario_constructs_valid_simulation(self) -> None:
        simulation = Wave2DSimulation(
            self.config,
            material_map=self.material_map,
        )

        self.assertEqual(
            set(simulation.monitor_states),
            {"first", "second"},
        )
        self.assertEqual(
            len(simulation.monitor_states["first"].values),
            1,
        )


class ControlledLineSourcePropagationTests(unittest.TestCase):
    """Verify controlled propagation and harmonic monitor responses."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.config, cls.material_map = create_scenario()
        cls.simulation = Wave2DSimulation(
            cls.config,
            material_map=cls.material_map,
        )

        for _ in range(cls.config.time.steps):
            cls.simulation.advance()

        cls.responses = analyze_monitor_responses(cls.simulation)

    def test_complete_histories_are_finite(self) -> None:
        expected_length = self.config.time.steps + 1

        self.assertEqual(
            self.simulation.state.step_index,
            self.config.time.steps,
        )

        for state in self.simulation.monitor_states.values():
            self.assertEqual(len(state.steps), expected_length)
            self.assertEqual(len(state.times), expected_length)
            self.assertEqual(len(state.values), expected_length)
            self.assertTrue(
                np.all(np.isfinite(state.values))
            )

    def test_both_monitors_measure_harmonic_propagation(self) -> None:
        first = self.responses["first"]
        second = self.responses["second"]

        self.assertGreater(first.amplitude, 1e-4)
        self.assertGreater(second.amplitude, 1e-4)

        self.assertEqual(first.sample_count, 250)
        self.assertEqual(second.sample_count, 250)
        self.assertAlmostEqual(first.cycle_count, 5.0)
        self.assertAlmostEqual(second.cycle_count, 5.0)

    def test_monitor_amplitudes_are_consistent(self) -> None:
        first = self.responses["first"]
        second = self.responses["second"]

        amplitude_ratio = second.amplitude / first.amplitude

        self.assertGreater(amplitude_ratio, 0.7)
        self.assertLess(amplitude_ratio, 1.3)

    def test_phase_advance_matches_numerical_dispersion(self) -> None:
        first = self.responses["first"]
        second = self.responses["second"]

        measured_phase_advance = np.angle(
            second.complex_amplitude
            / first.complex_amplitude
        )

        frequency = self.config.source.frequency
        dt = self.config.time.dt
        dx = self.config.grid.dx
        wave_speed = 1.0

        omega = 2.0 * np.pi * frequency
        courant_x = wave_speed * dt / dx

        numerical_wave_number = (
            2.0
            / dx
            * np.arcsin(
                np.sin(0.5 * omega * dt)
                / courant_x
            )
        )

        monitor_separation = (
            SECOND_MONITOR_X - FIRST_MONITOR_X
        )

        expected_phase_advance = np.angle(
            np.exp(
                -1.0j
                * numerical_wave_number
                * monitor_separation
            )
        )

        phase_error = np.angle(
            np.exp(
                1.0j
                * (
                    measured_phase_advance
                    - expected_phase_advance
                )
            )
        )

        self.assertLess(abs(phase_error), 0.25)
