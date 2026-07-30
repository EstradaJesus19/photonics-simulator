"""Cross-cutting validation for the complete Phase 2 API."""

import unittest

import numpy as np

import wavesim

from dataclasses import replace

from simulations.wave2d_composite_geometry import (
    create_scenario as create_composite_scenario,
)
from simulations.wave2d_planar_interface import (
    create_scenario as create_planar_scenario,
)
from simulations.wave2d_rectangular_dielectric import (
    create_scenario as create_rectangle_scenario,
)
from wavesim.config import (
    MIN_POINTS_PER_WAVELENGTH,
    compute_courant_number,
)


EXPECTED_PHASE2_PUBLIC_NAMES = (
    "BoundaryConfig",
    "GridConfig",
    "InitialConditionConfig",
    "MaterialConfig",
    "MaterialMap",
    "SimulationConfig",
    "SimulationState",
    "SourceConfig",
    "TimeConfig",
    "VisualizationConfig",
    "Wave2DSimulation",
    "add_rectangular_region",
    "create_background_refractive_index_array",
    "create_default_config",
    "create_material_map_from_refractive_index",
    "create_planar_interface_material_map",
    "create_rectangular_material_map",
    "create_uniform_material_map",
    "validate_material_map",
    "validate_refractive_index_array",
)


class Phase2PublicApiTest(unittest.TestCase):
    """Verify the supported package-level Phase 2 API."""

    def test_expected_phase2_names_are_public(self) -> None:
        for name in EXPECTED_PHASE2_PUBLIC_NAMES:
            with self.subTest(name=name):
                self.assertIn(name, wavesim.__all__)
                self.assertTrue(hasattr(wavesim, name))


class Phase2ConstructorCompatibilityTest(unittest.TestCase):
    """Verify compatibility wrappers match reusable composition."""

    def setUp(self) -> None:
        self.grid = wavesim.GridConfig(nx=8, ny=7)
        self.material = wavesim.MaterialConfig(
            reference_wave_speed=2.0,
            background_refractive_index=1.25,
        )

    def assert_material_maps_equal(
        self,
        actual: wavesim.MaterialMap,
        expected: wavesim.MaterialMap,
    ) -> None:
        np.testing.assert_array_equal(
            actual.refractive_index,
            expected.refractive_index,
        )
        np.testing.assert_allclose(
            actual.wave_speed,
            expected.wave_speed,
        )

    def test_uniform_wrapper_matches_reusable_pipeline(
        self,
    ) -> None:
        refractive_index = (
            wavesim.create_background_refractive_index_array(
                self.grid,
                self.material,
            )
        )
        expected = (
            wavesim.create_material_map_from_refractive_index(
                self.grid,
                self.material,
                refractive_index,
            )
        )

        actual = wavesim.create_uniform_material_map(
            self.grid,
            self.material,
        )

        self.assert_material_maps_equal(actual, expected)

    def test_planar_wrapper_matches_reusable_pipeline(
        self,
    ) -> None:
        interface_index = 4
        right_refractive_index = 1.75

        refractive_index = (
            wavesim.create_background_refractive_index_array(
                self.grid,
                self.material,
            )
        )
        refractive_index = wavesim.add_rectangular_region(
            refractive_index,
            self.grid,
            x_start=interface_index,
            x_stop=self.grid.nx,
            y_start=0,
            y_stop=self.grid.ny,
            region_refractive_index=(
                right_refractive_index
            ),
        )
        expected = (
            wavesim.create_material_map_from_refractive_index(
                self.grid,
                self.material,
                refractive_index,
            )
        )

        actual = (
            wavesim.create_planar_interface_material_map(
                self.grid,
                self.material,
                interface_index=interface_index,
                right_refractive_index=(
                    right_refractive_index
                ),
            )
        )

        self.assert_material_maps_equal(actual, expected)

    def test_rectangle_wrapper_matches_reusable_pipeline(
        self,
    ) -> None:
        rectangle_refractive_index = 2.0

        refractive_index = (
            wavesim.create_background_refractive_index_array(
                self.grid,
                self.material,
            )
        )
        refractive_index = wavesim.add_rectangular_region(
            refractive_index,
            self.grid,
            x_start=2,
            x_stop=6,
            y_start=2,
            y_stop=5,
            region_refractive_index=(
                rectangle_refractive_index
            ),
        )
        expected = (
            wavesim.create_material_map_from_refractive_index(
                self.grid,
                self.material,
                refractive_index,
            )
        )

        actual = wavesim.create_rectangular_material_map(
            self.grid,
            self.material,
            x_start=2,
            x_stop=6,
            y_start=2,
            y_stop=5,
            rectangle_refractive_index=(
                rectangle_refractive_index
            ),
        )

        self.assert_material_maps_equal(actual, expected)


class Phase2ScenarioValidationTest(unittest.TestCase):
    """Verify shared invariants across every official Phase 2 scenario."""

    def setUp(self) -> None:
        uniform_config = wavesim.create_default_config()
        uniform_map = wavesim.create_uniform_material_map(
            uniform_config.grid,
            uniform_config.material,
        )

        planar_config, planar_map = (
            create_planar_scenario()
        )
        rectangle_config, rectangle_map = (
            create_rectangle_scenario()
        )
        composite_config, composite_map = (
            create_composite_scenario()
        )

        self.scenarios = (
            ("uniform", uniform_config, uniform_map),
            ("planar", planar_config, planar_map),
            ("rectangle", rectangle_config, rectangle_map),
            ("composite", composite_config, composite_map),
        )

    def test_all_material_maps_satisfy_phase2_contract(
        self,
    ) -> None:
        for name, config, material_map in self.scenarios:
            with self.subTest(name=name):
                wavesim.validate_material_map(
                    material_map,
                    config.grid,
                )

                self.assertEqual(
                    material_map.refractive_index.shape,
                    config.grid.shape,
                )
                self.assertEqual(
                    material_map.wave_speed.shape,
                    config.grid.shape,
                )

                self.assertTrue(
                    np.all(
                        np.isfinite(
                            material_map.refractive_index
                        )
                    )
                )
                self.assertTrue(
                    np.all(
                        material_map.refractive_index > 0
                    )
                )
                self.assertTrue(
                    np.all(
                        np.isfinite(
                            material_map.wave_speed
                        )
                    )
                )
                self.assertTrue(
                    np.all(material_map.wave_speed > 0)
                )

                np.testing.assert_allclose(
                    material_map.wave_speed,
                    (
                        config.material.reference_wave_speed
                        / material_map.refractive_index
                    ),
                )

    def test_all_scenarios_satisfy_cfl_stability(
        self,
    ) -> None:
        for name, config, material_map in self.scenarios:
            with self.subTest(name=name):
                maximum_wave_speed = float(
                    np.max(material_map.wave_speed)
                )
                courant_number = compute_courant_number(
                    config,
                    maximum_wave_speed,
                )

                self.assertLessEqual(
                    courant_number,
                    1.0,
                )

    def test_all_driven_scenarios_meet_wavelength_resolution(
        self,
    ) -> None:
        for name, config, material_map in self.scenarios:
            with self.subTest(name=name):
                self.assertEqual(
                    config.source.kind,
                    "point_sine",
                )

                minimum_wave_speed = float(
                    np.min(material_map.wave_speed)
                )
                minimum_wavelength = (
                    minimum_wave_speed
                    / config.source.frequency
                )
                largest_grid_spacing = max(
                    config.grid.dx,
                    config.grid.dy,
                )
                minimum_points_per_wavelength = (
                    minimum_wavelength
                    / largest_grid_spacing
                )

                self.assertGreaterEqual(
                    minimum_points_per_wavelength,
                    MIN_POINTS_PER_WAVELENGTH,
                )

    def test_all_scenarios_construct_valid_simulations(
        self,
    ) -> None:
        for name, config, material_map in self.scenarios:
            with self.subTest(name=name):
                simulation = wavesim.Wave2DSimulation(
                    config,
                    material_map=material_map,
                )

                self.assertIs(
                    simulation.material_map,
                    material_map,
                )
                self.assertEqual(
                    simulation.state.current.shape,
                    config.grid.shape,
                )
                self.assertTrue(
                    np.isfinite(simulation.initial_energy)
                )


class Phase2EnergyValidationTest(unittest.TestCase):
    """Verify source-free energy behavior across composite materials."""

    def test_fixed_composite_run_approximately_conserves_energy(
        self,
    ) -> None:
        config, material_map = create_composite_scenario()

        config = replace(
            config,
            time=replace(
                config.time,
                steps=300,
            ),
            initial_condition=replace(
                config.initial_condition,
                kind="gaussian",
                x0=60,
                y0=config.grid.ny // 2,
                sigma=8.0,
            ),
            source=replace(
                config.source,
                kind="none",
            ),
            boundary=replace(
                config.boundary,
                kind="fixed",
            ),
        )

        simulation = wavesim.Wave2DSimulation(
            config,
            material_map=material_map,
        )

        self.assertGreater(simulation.initial_energy, 0.0)
        self.assertTrue(simulation.normalize_energy)

        for _ in range(config.time.steps):
            simulation.advance()

        energy_history = np.asarray(
            simulation.state.energy_history
        )
        relative_energy = (
            energy_history
            / simulation.initial_energy
        )

        self.assertTrue(
            np.all(np.isfinite(energy_history))
        )
        self.assertEqual(
            len(energy_history),
            config.time.steps + 1,
        )

        maximum_relative_drift = float(
            np.max(
                np.abs(relative_energy - 1.0)
            )
        )

        self.assertLess(
            maximum_relative_drift,
            0.05,
        )


if __name__ == "__main__":
    unittest.main()