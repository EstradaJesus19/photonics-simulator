"""Tests for the Phase 2.5 composite-geometry scenario."""

import unittest

import numpy as np

from simulations.wave2d_composite_geometry import (
    CORE_REFRACTIVE_INDEX,
    CORE_X_START,
    CORE_X_STOP,
    CORE_Y_START,
    CORE_Y_STOP,
    OUTER_REFRACTIVE_INDEX,
    OUTER_X_START,
    OUTER_X_STOP,
    OUTER_Y_START,
    OUTER_Y_STOP,
    create_scenario,
)
from wavesim.config import MIN_POINTS_PER_WAVELENGTH
from wavesim.solver import Wave2DSimulation


class CompositeGeometryScenarioTest(unittest.TestCase):
    """Verify the nested composite-material scenario."""

    def setUp(self) -> None:
        self.config, self.material_map = create_scenario()

    def test_scenario_parameters(self) -> None:
        config = self.config

        self.assertEqual(config.grid.nx, 240)
        self.assertEqual(config.grid.ny, 160)
        self.assertEqual(config.time.steps, 600)
        self.assertEqual(config.source.x, 60)
        self.assertEqual(
            config.source.y,
            config.grid.ny // 2,
        )
        self.assertEqual(config.source.frequency, 0.05)
        self.assertEqual(config.boundary.kind, "sponge")
        self.assertEqual(config.boundary.damping_width, 25)

    def test_composite_material_geometry(self) -> None:
        expected_index = np.ones(self.config.grid.shape)

        expected_index[
            OUTER_X_START:OUTER_X_STOP,
            OUTER_Y_START:OUTER_Y_STOP,
        ] = OUTER_REFRACTIVE_INDEX

        expected_index[
            CORE_X_START:CORE_X_STOP,
            CORE_Y_START:CORE_Y_STOP,
        ] = CORE_REFRACTIVE_INDEX

        np.testing.assert_array_equal(
            self.material_map.refractive_index,
            expected_index,
        )
        np.testing.assert_allclose(
            self.material_map.wave_speed,
            1.0 / expected_index,
        )
        np.testing.assert_array_equal(
            np.unique(self.material_map.refractive_index),
            np.array(
                [
                    1.0,
                    OUTER_REFRACTIVE_INDEX,
                    CORE_REFRACTIVE_INDEX,
                ]
            ),
        )

    def test_core_is_nested_and_geometry_avoids_sponge(
        self,
    ) -> None:
        config = self.config
        sponge_width = config.boundary.damping_width
        right_sponge_start = config.grid.nx - sponge_width
        top_sponge_start = config.grid.ny - sponge_width

        self.assertGreater(
            CORE_X_START,
            OUTER_X_START,
        )
        self.assertLess(
            CORE_X_STOP,
            OUTER_X_STOP,
        )
        self.assertGreater(
            CORE_Y_START,
            OUTER_Y_START,
        )
        self.assertLess(
            CORE_Y_STOP,
            OUTER_Y_STOP,
        )

        self.assertGreater(config.source.x, sponge_width)
        self.assertLess(config.source.x, OUTER_X_START)
        self.assertGreater(OUTER_X_START, sponge_width)
        self.assertLess(OUTER_X_STOP, right_sponge_start)
        self.assertGreater(OUTER_Y_START, sponge_width)
        self.assertLess(OUTER_Y_STOP, top_sponge_start)

    def test_all_materials_meet_wavelength_resolution(
        self,
    ) -> None:
        minimum_wave_speed = float(
            np.min(self.material_map.wave_speed)
        )
        minimum_wavelength = (
            minimum_wave_speed
            / self.config.source.frequency
        )
        largest_grid_spacing = max(
            self.config.grid.dx,
            self.config.grid.dy,
        )
        minimum_points_per_wavelength = (
            minimum_wavelength
            / largest_grid_spacing
        )

        self.assertGreaterEqual(
            minimum_points_per_wavelength,
            MIN_POINTS_PER_WAVELENGTH,
        )

    def test_scenario_constructs_valid_simulation(self) -> None:
        simulation = Wave2DSimulation(
            self.config,
            material_map=self.material_map,
        )

        self.assertIs(
            simulation.material_map,
            self.material_map,
        )
        self.assertEqual(
            simulation.state.current.shape,
            self.config.grid.shape,
        )
        self.assertTrue(np.isfinite(simulation.initial_energy))

    def test_wave_crosses_composite_geometry_without_failure(
        self,
    ) -> None:
        simulation = Wave2DSimulation(
            self.config,
            material_map=self.material_map,
        )

        test_steps = 420

        for _ in range(test_steps):
            simulation.advance()

        current = simulation.state.current
        energy_history = np.asarray(
            simulation.state.energy_history
        )
        center_y = self.config.source.y

        core_region = current[
            CORE_X_START + 5:CORE_X_STOP - 5,
            CORE_Y_START + 5:CORE_Y_STOP - 5,
        ]
        rear_transmitted_region = current[
            OUTER_X_STOP + 5:,
            center_y - 10:center_y + 10,
        ]

        self.assertEqual(
            simulation.state.step_index,
            test_steps,
        )
        self.assertEqual(
            len(simulation.state.energy_history),
            test_steps + 1,
        )

        self.assertTrue(np.all(np.isfinite(current)))
        self.assertTrue(
            np.all(np.isfinite(simulation.state.previous))
        )
        self.assertTrue(np.all(np.isfinite(energy_history)))

        self.assertGreater(simulation.current_energy, 0.0)
        self.assertGreater(
            float(np.max(np.abs(core_region))),
            1e-3,
        )
        self.assertGreater(
            float(
                np.max(
                    np.abs(rear_transmitted_region)
                )
            ),
            1e-3,
        )
        self.assertLess(
            float(np.max(np.abs(current))),
            10.0,
        )


if __name__ == "__main__":
    unittest.main()