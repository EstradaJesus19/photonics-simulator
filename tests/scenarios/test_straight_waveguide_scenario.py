"""Tests for the Phase 4.6 straight-waveguide scenario."""

import unittest

import numpy as np

from simulations.structures.wave2d_straight_waveguide.simulation import (
    ANALYSIS_START_STEP,
    ANALYSIS_STOP_STEP,
    CENTER_MONITOR_Y_START,
    CENTER_MONITOR_Y_STOP,
    FIRST_CENTER_MONITOR_X,
    OFFSET_MONITOR_Y_START,
    GRID_NX,
    GRID_NY,
    SECOND_CENTER_MONITOR_X,
    SOURCE_FREQUENCY,
    SOURCE_RAMP_CYCLES,
    SOURCE_X,
    SOURCE_Y_START,
    SOURCE_Y_STOP,
    SPONGE_WIDTH,
    WAVEGUIDE_CENTER_Y,
    WAVEGUIDE_HEIGHT,
    WAVEGUIDE_REFRACTIVE_INDEX,
    analyze_monitor_responses,
    create_scenario_pair,
)
from wavesim.config import (
    compute_courant_number,
    validate_config,
)
from wavesim.solver import Wave2DSimulation


class StraightWaveguideConfigurationTest(unittest.TestCase):
    """Verify construction of the paired waveguide scenario."""

    def setUp(self) -> None:
        (
            self.config,
            self.reference_map,
            self.waveguide_map,
        ) = create_scenario_pair()

    def test_scenario_parameters(self) -> None:
        self.assertEqual(
            self.config.grid.shape,
            (GRID_NX, GRID_NY),
        )
        self.assertEqual(
            self.config.time.steps,
            ANALYSIS_STOP_STEP,
        )
        self.assertEqual(
            self.config.source.kind,
            "line_sine",
        )
        self.assertEqual(
            self.config.source.x,
            SOURCE_X,
        )
        self.assertEqual(
            self.config.source.y_start,
            SOURCE_Y_START,
        )
        self.assertEqual(
            self.config.source.y_stop,
            SOURCE_Y_STOP,
        )
        self.assertEqual(
            self.config.source.frequency,
            SOURCE_FREQUENCY,
        )
        self.assertEqual(
            self.config.source.ramp_cycles,
            SOURCE_RAMP_CYCLES,
        )
        self.assertEqual(
            self.config.boundary.damping_width,
            SPONGE_WIDTH,
        )

    def test_reference_is_uniform(self) -> None:
        np.testing.assert_array_equal(
            self.reference_map.refractive_index,
            np.ones(self.config.grid.shape),
        )

    def test_waveguide_has_expected_strip(self) -> None:
        grid = self.config.grid

        x = np.arange(grid.nx) * grid.dx
        y = np.arange(grid.ny) * grid.dy

        expected_y = (
            np.abs(y - WAVEGUIDE_CENTER_Y)
            <= WAVEGUIDE_HEIGHT / 2.0
        )

        expected_mask = np.broadcast_to(
            expected_y[np.newaxis, :],
            grid.shape,
        )

        np.testing.assert_array_equal(
            self.waveguide_map.refractive_index[
                expected_mask
            ],
            np.full(
                np.count_nonzero(expected_mask),
                WAVEGUIDE_REFRACTIVE_INDEX,
            ),
        )
        np.testing.assert_array_equal(
            self.waveguide_map.refractive_index[
                ~expected_mask
            ],
            np.ones(
                np.count_nonzero(~expected_mask)
            ),
        )

    def test_source_and_center_monitors_are_in_waveguide(
        self,
    ) -> None:
        material = (
            self.waveguide_map.refractive_index
        )

        self.assertTrue(
            np.all(
                material[
                    SOURCE_X,
                    SOURCE_Y_START:SOURCE_Y_STOP,
                ]
                == WAVEGUIDE_REFRACTIVE_INDEX
            )
        )

        for monitor_x in (
            FIRST_CENTER_MONITOR_X,
            SECOND_CENTER_MONITOR_X,
        ):
            with self.subTest(monitor_x=monitor_x):
                self.assertTrue(
                    np.all(
                        material[
                            monitor_x,
                            CENTER_MONITOR_Y_START:
                            CENTER_MONITOR_Y_STOP,
                        ]
                        == WAVEGUIDE_REFRACTIVE_INDEX
                    )
                )

    def test_offset_monitor_is_outside_waveguide(
        self,
    ) -> None:
        material = (
            self.waveguide_map.refractive_index
        )

        self.assertTrue(
            np.all(
                material[
                    SECOND_CENTER_MONITOR_X,
                    OFFSET_MONITOR_Y_START:,
                ]
                == 1.0
            )
        )

    def test_active_components_avoid_sponge_except_guide(
        self,
    ) -> None:
        right_sponge_start = (
            self.config.grid.nx - SPONGE_WIDTH
        )
        top_sponge_start = (
            self.config.grid.ny - SPONGE_WIDTH
        )

        self.assertGreater(SOURCE_X, SPONGE_WIDTH)
        self.assertGreater(
            SOURCE_Y_START,
            SPONGE_WIDTH,
        )
        self.assertLess(
            SOURCE_Y_STOP,
            top_sponge_start,
        )

        self.assertGreater(
            FIRST_CENTER_MONITOR_X,
            SOURCE_X,
        )
        self.assertGreater(
            SECOND_CENTER_MONITOR_X,
            FIRST_CENTER_MONITOR_X,
        )
        self.assertLess(
            SECOND_CENTER_MONITOR_X,
            right_sponge_start,
        )

    def test_analysis_window_contains_three_cycles(
        self,
    ) -> None:
        sample_count = (
            ANALYSIS_STOP_STEP
            - ANALYSIS_START_STEP
        )
        duration = (
            sample_count
            * self.config.time.dt
        )
        cycle_count = (
            duration
            * self.config.source.frequency
        )

        self.assertEqual(sample_count, 150)
        self.assertAlmostEqual(cycle_count, 3.0)

    def test_both_maps_satisfy_numerical_constraints(
        self,
    ) -> None:
        validate_config(self.config)

        for material_map in (
            self.reference_map,
            self.waveguide_map,
        ):
            with self.subTest(material_map=material_map):
                maximum_wave_speed = float(
                    np.max(material_map.wave_speed)
                )
                courant = compute_courant_number(
                    self.config,
                    maximum_wave_speed,
                )

                self.assertLessEqual(courant, 1.0)

        shortest_wavelength = (
            1.0
            / WAVEGUIDE_REFRACTIVE_INDEX
            / SOURCE_FREQUENCY
        )
        points_per_wavelength = (
            shortest_wavelength
            / max(
                self.config.grid.dx,
                self.config.grid.dy,
            )
        )

        self.assertGreaterEqual(
            points_per_wavelength,
            10.0,
        )

    def test_pair_constructs_valid_simulations(self) -> None:
        reference = Wave2DSimulation(
            self.config,
            material_map=self.reference_map,
        )
        waveguide = Wave2DSimulation(
            self.config,
            material_map=self.waveguide_map,
        )

        self.assertEqual(
            set(reference.monitor_states),
            {
                "first_center",
                "second_center",
                "second_offset",
            },
        )
        self.assertEqual(
            set(reference.monitor_states),
            set(waveguide.monitor_states),
        )


class StraightWaveguidePropagationTest(unittest.TestCase):
    """Verify propagation and qualitative confinement."""

    @classmethod
    def setUpClass(cls) -> None:
        (
            cls.config,
            cls.reference_map,
            cls.waveguide_map,
        ) = create_scenario_pair()

        cls.reference = Wave2DSimulation(
            cls.config,
            material_map=cls.reference_map,
        )
        cls.waveguide = Wave2DSimulation(
            cls.config,
            material_map=cls.waveguide_map,
        )

        for _ in range(cls.config.time.steps):
            cls.reference.advance()
            cls.waveguide.advance()

        cls.reference_responses = (
            analyze_monitor_responses(cls.reference)
        )
        cls.waveguide_responses = (
            analyze_monitor_responses(cls.waveguide)
        )

    def test_histories_are_complete_and_finite(
        self,
    ) -> None:
        expected_length = (
            self.config.time.steps + 1
        )

        for simulation in (
            self.reference,
            self.waveguide,
        ):
            for state in (
                simulation.monitor_states.values()
            ):
                self.assertEqual(
                    len(state.values),
                    expected_length,
                )
                self.assertTrue(
                    np.all(np.isfinite(state.values))
                )

    def test_wave_reaches_both_center_monitors(self) -> None:
        for monitor_name in (
            "first_center",
            "second_center",
        ):
            response = self.waveguide_responses[
                monitor_name
            ]

            with self.subTest(
                monitor_name=monitor_name
            ):
                self.assertGreater(
                    response.amplitude,
                    1e-4,
                )
                self.assertEqual(
                    response.sample_count,
                    150,
                )
                self.assertAlmostEqual(
                    response.cycle_count,
                    3.0,
                )

    def test_waveguide_concentrates_downstream_field(
        self,
    ) -> None:
        core_amplitude = (
            self.waveguide_responses[
                "second_center"
            ].amplitude
        )
        cladding_amplitude = (
            self.waveguide_responses[
                "second_offset"
            ].amplitude
        )

        self.assertGreater(
            core_amplitude,
            cladding_amplitude,
        )

    def test_waveguide_improves_core_cladding_contrast(
        self,
    ) -> None:
        reference_contrast = (
            self.reference_responses[
                "second_center"
            ].amplitude
            / self.reference_responses[
                "second_offset"
            ].amplitude
        )
        waveguide_contrast = (
            self.waveguide_responses[
                "second_center"
            ].amplitude
            / self.waveguide_responses[
                "second_offset"
            ].amplitude
        )

        self.assertGreater(
            waveguide_contrast,
            reference_contrast,
        )
