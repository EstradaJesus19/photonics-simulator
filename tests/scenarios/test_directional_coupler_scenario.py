"""Tests for the Phase 4.7 directional-coupler scenario."""

import unittest

import numpy as np

from simulations.structures.wave2d_directional_coupler.simulation import (
    ANALYSIS_START_STEP,
    ANALYSIS_STOP_STEP,
    CORE_GAP,
    CORE_HEIGHT,
    CORE_REFRACTIVE_INDEX,
    FIRST_MONITOR_X,
    GRID_NX,
    GRID_NY,
    LOWER_CORE_CENTER_Y,
    LOWER_MONITOR_Y_START,
    LOWER_MONITOR_Y_STOP,
    SECOND_MONITOR_X,
    SOURCE_FREQUENCY,
    SOURCE_RAMP_CYCLES,
    SOURCE_X,
    SOURCE_Y_START,
    SOURCE_Y_STOP,
    SPONGE_WIDTH,
    UPPER_CORE_CENTER_Y,
    UPPER_MONITOR_Y_START,
    UPPER_MONITOR_Y_STOP,
    analyze_monitor_responses,
    create_core_mask,
    create_scenario_pair,
)
from wavesim.config import (
    compute_courant_number,
    validate_config,
)
from wavesim.solver import Wave2DSimulation


class DirectionalCouplerConfigurationTest(unittest.TestCase):
    """Verify paired directional-coupler construction."""

    def setUp(self) -> None:
        (
            self.config,
            self.isolated_map,
            self.coupled_map,
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

    def test_core_gap_is_positive(self) -> None:
        self.assertGreater(CORE_GAP, 0.0)
        self.assertAlmostEqual(CORE_GAP, 2.0)

    def test_isolated_map_contains_only_upper_core(
        self,
    ) -> None:
        upper_mask = create_core_mask(
            self.config.grid,
            center_y=UPPER_CORE_CENTER_Y,
        )
        lower_mask = create_core_mask(
            self.config.grid,
            center_y=LOWER_CORE_CENTER_Y,
        )

        np.testing.assert_array_equal(
            self.isolated_map.refractive_index[
                upper_mask
            ],
            np.full(
                np.count_nonzero(upper_mask),
                CORE_REFRACTIVE_INDEX,
            ),
        )
        np.testing.assert_array_equal(
            self.isolated_map.refractive_index[
                lower_mask
            ],
            np.ones(
                np.count_nonzero(lower_mask)
            ),
        )

    def test_coupled_map_contains_both_cores(
        self,
    ) -> None:
        upper_mask = create_core_mask(
            self.config.grid,
            center_y=UPPER_CORE_CENTER_Y,
        )
        lower_mask = create_core_mask(
            self.config.grid,
            center_y=LOWER_CORE_CENTER_Y,
        )

        self.assertFalse(
            np.any(upper_mask & lower_mask)
        )

        for mask in (upper_mask, lower_mask):
            with self.subTest(mask=mask):
                np.testing.assert_array_equal(
                    self.coupled_map.refractive_index[
                        mask
                    ],
                    np.full(
                        np.count_nonzero(mask),
                        CORE_REFRACTIVE_INDEX,
                    ),
                )

    def test_source_is_inside_upper_core(self) -> None:
        source_material = (
            self.coupled_map.refractive_index[
                SOURCE_X,
                SOURCE_Y_START:SOURCE_Y_STOP,
            ]
        )

        np.testing.assert_array_equal(
            source_material,
            np.full(
                source_material.shape,
                CORE_REFRACTIVE_INDEX,
            ),
        )

    def test_monitor_windows_match_core_positions(
        self,
    ) -> None:
        for material_map in (
            self.isolated_map,
            self.coupled_map,
        ):
            with self.subTest(material_map=material_map):
                self.assertTrue(
                    np.all(
                        material_map.refractive_index[
                            FIRST_MONITOR_X,
                            UPPER_MONITOR_Y_START:
                            UPPER_MONITOR_Y_STOP,
                        ]
                        == CORE_REFRACTIVE_INDEX
                    )
                )
                self.assertTrue(
                    np.all(
                        material_map.refractive_index[
                            SECOND_MONITOR_X,
                            UPPER_MONITOR_Y_START:
                            UPPER_MONITOR_Y_STOP,
                        ]
                        == CORE_REFRACTIVE_INDEX
                    )
                )

        self.assertTrue(
            np.all(
                self.isolated_map.refractive_index[
                    SECOND_MONITOR_X,
                    LOWER_MONITOR_Y_START:
                    LOWER_MONITOR_Y_STOP,
                ]
                == 1.0
            )
        )
        self.assertTrue(
            np.all(
                self.coupled_map.refractive_index[
                    SECOND_MONITOR_X,
                    LOWER_MONITOR_Y_START:
                    LOWER_MONITOR_Y_STOP,
                ]
                == CORE_REFRACTIVE_INDEX
            )
        )

    def test_active_components_avoid_sponge(self) -> None:
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
            FIRST_MONITOR_X,
            SOURCE_X,
        )
        self.assertGreater(
            SECOND_MONITOR_X,
            FIRST_MONITOR_X,
        )
        self.assertLess(
            SECOND_MONITOR_X,
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

    def test_maps_satisfy_numerical_constraints(
        self,
    ) -> None:
        validate_config(self.config)

        for material_map in (
            self.isolated_map,
            self.coupled_map,
        ):
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
            / CORE_REFRACTIVE_INDEX
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
        isolated = Wave2DSimulation(
            self.config,
            material_map=self.isolated_map,
        )
        coupled = Wave2DSimulation(
            self.config,
            material_map=self.coupled_map,
        )

        expected_monitors = {
            "first_upper",
            "first_lower",
            "second_upper",
            "second_lower",
        }

        self.assertEqual(
            set(isolated.monitor_states),
            expected_monitors,
        )
        self.assertEqual(
            set(coupled.monitor_states),
            expected_monitors,
        )


class DirectionalCouplerPropagationTest(unittest.TestCase):
    """Verify scalar-field transfer between coupled guides."""

    @classmethod
    def setUpClass(cls) -> None:
        (
            cls.config,
            cls.isolated_map,
            cls.coupled_map,
        ) = create_scenario_pair()

        cls.isolated = Wave2DSimulation(
            cls.config,
            material_map=cls.isolated_map,
        )
        cls.coupled = Wave2DSimulation(
            cls.config,
            material_map=cls.coupled_map,
        )

        for _ in range(cls.config.time.steps):
            cls.isolated.advance()
            cls.coupled.advance()

        cls.isolated_responses = (
            analyze_monitor_responses(cls.isolated)
        )
        cls.coupled_responses = (
            analyze_monitor_responses(cls.coupled)
        )

    def test_histories_are_complete_and_finite(
        self,
    ) -> None:
        expected_length = (
            self.config.time.steps + 1
        )

        for simulation in (
            self.isolated,
            self.coupled,
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

    def test_all_coupled_monitors_detect_field(
        self,
    ) -> None:
        for name, response in (
            self.coupled_responses.items()
        ):
            with self.subTest(name=name):
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

    def test_isolated_reference_remains_upper_dominant(
        self,
    ) -> None:
        upper = self.isolated_responses[
            "second_upper"
        ].amplitude
        lower = self.isolated_responses[
            "second_lower"
        ].amplitude

        self.assertGreater(upper, lower)

    def test_coupled_field_transfers_downstream(
        self,
    ) -> None:
        upstream_ratio = (
            self.coupled_responses[
                "first_lower"
            ].amplitude
            / self.coupled_responses[
                "first_upper"
            ].amplitude
        )
        downstream_ratio = (
            self.coupled_responses[
                "second_lower"
            ].amplitude
            / self.coupled_responses[
                "second_upper"
            ].amplitude
        )

        self.assertGreater(
            downstream_ratio,
            upstream_ratio,
        )

    def test_lower_guide_dominates_downstream(
        self,
    ) -> None:
        upper = self.coupled_responses[
            "second_upper"
        ].amplitude
        lower = self.coupled_responses[
            "second_lower"
        ].amplitude

        self.assertGreater(lower, upper)

    def test_coupler_enhances_lower_window_response(
        self,
    ) -> None:
        isolated_lower = (
            self.isolated_responses[
                "second_lower"
            ].amplitude
        )
        coupled_lower = (
            self.coupled_responses[
                "second_lower"
            ].amplitude
        )

        enhancement = (
            coupled_lower / isolated_lower
        )

        self.assertGreater(enhancement, 3.0)