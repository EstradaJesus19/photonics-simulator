"""Tests for the Phase 2.3 planar-interface scenario."""

import unittest

import numpy as np

from simulations.materials.wave2d_planar_interface import (
    INTERFACE_INDEX,
    RIGHT_REFRACTIVE_INDEX,
    create_scenario,
)
from wavesim.solver import Wave2DSimulation


class PlanarInterfaceScenarioTest(unittest.TestCase):
    """Verify the complete planar-interface scenario configuration."""

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

    def test_scenario_material_regions(self) -> None:
        refractive_index = self.material_map.refractive_index
        wave_speed = self.material_map.wave_speed

        np.testing.assert_array_equal(
            refractive_index[:INTERFACE_INDEX, :],
            np.ones(
                (
                    INTERFACE_INDEX,
                    self.config.grid.ny,
                )
            ),
        )
        np.testing.assert_array_equal(
            refractive_index[INTERFACE_INDEX:, :],
            np.full(
                (
                    self.config.grid.nx - INTERFACE_INDEX,
                    self.config.grid.ny,
                ),
                RIGHT_REFRACTIVE_INDEX,
            ),
        )
        np.testing.assert_allclose(
            wave_speed[INTERFACE_INDEX:, :],
            1.0 / RIGHT_REFRACTIVE_INDEX,
        )

    def test_geometry_is_outside_sponge(self) -> None:
        config = self.config
        sponge_width = config.boundary.damping_width
        right_sponge_start = config.grid.nx - sponge_width

        self.assertGreater(config.source.x, sponge_width)
        self.assertLess(config.source.x, INTERFACE_INDEX)
        self.assertLess(INTERFACE_INDEX, right_sponge_start)

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

    def test_wave_crosses_interface_without_numerical_failure(
        self,
    ) -> None:
        simulation = Wave2DSimulation(
            self.config,
            material_map=self.material_map,
        )

        test_steps = 220

        for _ in range(test_steps):
            simulation.advance()

        current = simulation.state.current
        energy_history = np.asarray(
            simulation.state.energy_history
        )

        transmitted_region = current[
            INTERFACE_INDEX + 5:,
            :,
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
            float(np.max(np.abs(transmitted_region))),
            1e-3,
        )

        self.assertLess(
            float(np.max(np.abs(current))),
            10.0,
        )

if __name__ == "__main__":
    unittest.main()
