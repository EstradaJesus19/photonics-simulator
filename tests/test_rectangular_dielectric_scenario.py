"""Tests for the Phase 2.4 rectangular-dielectric scenario."""

import unittest

import numpy as np

from simulations.wave2d_rectangular_dielectric import (
    RECTANGLE_REFRACTIVE_INDEX,
    RECTANGLE_X_START,
    RECTANGLE_X_STOP,
    RECTANGLE_Y_START,
    RECTANGLE_Y_STOP,
    create_scenario,
)
from wavesim.solver import Wave2DSimulation


class RectangularDielectricScenarioTest(unittest.TestCase):
    """Verify the rectangular-dielectric scenario configuration."""

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

    def test_scenario_material_geometry(self) -> None:
        expected_index = np.ones(self.config.grid.shape)

        expected_index[
            RECTANGLE_X_START:RECTANGLE_X_STOP,
            RECTANGLE_Y_START:RECTANGLE_Y_STOP,
        ] = RECTANGLE_REFRACTIVE_INDEX

        np.testing.assert_array_equal(
            self.material_map.refractive_index,
            expected_index,
        )

        expected_speed = 1.0 / expected_index

        np.testing.assert_allclose(
            self.material_map.wave_speed,
            expected_speed,
        )

    def test_geometry_is_outside_sponge(self) -> None:
        config = self.config
        sponge_width = config.boundary.damping_width
        right_sponge_start = config.grid.nx - sponge_width
        top_sponge_start = config.grid.ny - sponge_width

        self.assertGreater(
            config.source.x,
            sponge_width,
        )
        self.assertLess(
            config.source.x,
            RECTANGLE_X_START,
        )
        self.assertGreater(
            RECTANGLE_X_START,
            sponge_width,
        )
        self.assertLess(
            RECTANGLE_X_STOP,
            right_sponge_start,
        )
        self.assertGreater(
            RECTANGLE_Y_START,
            sponge_width,
        )
        self.assertLess(
            RECTANGLE_Y_STOP,
            top_sponge_start,
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

    def test_wave_crosses_rectangle_without_numerical_failure(
        self,
    ) -> None:
        simulation = Wave2DSimulation(
            self.config,
            material_map=self.material_map,
        )

        test_steps = 360

        for _ in range(test_steps):
            simulation.advance()

        current = simulation.state.current
        energy_history = np.asarray(
            simulation.state.energy_history
        )
        center_y = self.config.source.y

        interior_region = current[
            RECTANGLE_X_START + 5:RECTANGLE_X_STOP - 5,
            center_y - 10:center_y + 10,
        ]
        rear_transmitted_region = current[
            RECTANGLE_X_STOP + 5:,
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
            float(np.max(np.abs(interior_region))),
            1e-3,
        )
        self.assertGreater(
            float(np.max(np.abs(rear_transmitted_region))),
            1e-3,
        )

        self.assertLess(
            float(np.max(np.abs(current))),
            10.0,
        )


if __name__ == "__main__":
    unittest.main()