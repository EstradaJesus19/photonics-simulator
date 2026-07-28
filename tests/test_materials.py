"""Tests for material-map construction and validation."""

from dataclasses import replace
import unittest

import numpy as np

from wavesim.config import (
    GridConfig,
    MaterialConfig,
    create_default_config,
    validate_config,
)
from wavesim.materials import (
    MaterialMap,
    create_planar_interface_material_map,
    create_uniform_material_map,
    validate_material_map,
)
from wavesim.solver import (
    Wave2DSimulation,
    compute_energy,
    step_wave,
)


class UniformMaterialMapTest(unittest.TestCase):
    """Verify construction of uniform material maps."""

    def test_default_uniform_material(self) -> None:
        grid = GridConfig()
        material = MaterialConfig()

        material_map = create_uniform_material_map(grid, material)

        self.assertEqual(material_map.refractive_index.shape, grid.shape)
        self.assertEqual(material_map.wave_speed.shape, grid.shape)
        self.assertTrue(
            np.all(material_map.refractive_index == 1.0)
        )
        self.assertTrue(np.all(material_map.wave_speed == 1.0))

    def test_non_unit_refractive_index(self) -> None:
        grid = GridConfig()
        material = MaterialConfig(
            reference_wave_speed=1.0,
            background_refractive_index=2.0,
        )

        material_map = create_uniform_material_map(grid, material)

        self.assertTrue(
            np.all(material_map.refractive_index == 2.0)
        )
        self.assertTrue(np.all(material_map.wave_speed == 0.5))

    def test_simulation_owns_default_material_map(self) -> None:
        simulation = Wave2DSimulation(create_default_config())

        self.assertEqual(
            simulation.material_map.refractive_index.shape,
            simulation.config.grid.shape,
        )
        self.assertTrue(
            np.all(simulation.material_map.refractive_index == 1.0)
        )
        self.assertTrue(
            np.all(simulation.material_map.wave_speed == 1.0)
        )

    def test_step_uses_material_wave_speed(self) -> None:
        grid = GridConfig(nx=5, ny=5)
        material = MaterialConfig(
            reference_wave_speed=1.0,
            background_refractive_index=2.0,
        )
        material_map = create_uniform_material_map(grid, material)

        config = replace(
            create_default_config(),
            grid=grid,
            material=material,
            time=replace(
                create_default_config().time,
                dt=0.4,
                steps=1,
            ),
            boundary=replace(
                create_default_config().boundary,
                kind="fixed",
            ),
            initial_condition=replace(
                create_default_config().initial_condition,
                x0=2,
                y0=2,
            ),
            source=replace(
                create_default_config().source,
                kind="none",
                x=2,
                y=2,
            ),
        )

        current = np.zeros(grid.shape)
        current[2, 2] = 1.0
        previous = current.copy()
        damping_profile = np.zeros(grid.shape)

        next_field = step_wave(
            previous,
            current,
            config,
            material_map,
            damping_profile,
        )

        self.assertAlmostEqual(next_field[2, 2], 0.84)

    def test_energy_uses_material_wave_speed(self) -> None:
        grid = GridConfig(nx=5, ny=5)
        material = MaterialConfig(
            reference_wave_speed=1.0,
            background_refractive_index=2.0,
        )
        material_map = create_uniform_material_map(grid, material)

        config = replace(
            create_default_config(),
            grid=grid,
            material=material,
        )

        previous = np.zeros(grid.shape)
        current = np.ones(grid.shape)

        energy = compute_energy(
            previous,
            current,
            config,
            material_map,
        )

        expected_velocity = 1.0 / config.time.dt
        expected_density = (
            0.5 * expected_velocity**2 / 0.5**2
        )
        expected_energy = (
            expected_density
            * grid.nx
            * grid.ny
            * grid.dx
            * grid.dy
        )

        self.assertAlmostEqual(energy, expected_energy)

    def test_cfl_uses_fastest_material_speed(self) -> None:
        config = create_default_config()
        fast_material = replace(
            config.material,
            reference_wave_speed=2.0,
        )
        unstable_config = replace(
            config,
            material=fast_material,
        )

        with self.assertRaisesRegex(
            ValueError,
            "Courant number",
        ):
            Wave2DSimulation(unstable_config)


class PlanarInterfaceMaterialMapTest(unittest.TestCase):
    """Verify construction of a vertical planar material interface."""

    def setUp(self) -> None:
        self.grid = GridConfig(nx=6, ny=4)
        self.material = MaterialConfig(
            reference_wave_speed=1.0,
            background_refractive_index=1.0,
        )

    def test_interface_regions_and_wave_speeds(self) -> None:
        material_map = create_planar_interface_material_map(
            self.grid,
            self.material,
            interface_index=3,
            right_refractive_index=1.5,
        )

        self.assertEqual(
            material_map.refractive_index.shape,
            self.grid.shape,
        )
        self.assertEqual(
            material_map.wave_speed.shape,
            self.grid.shape,
        )
        np.testing.assert_array_equal(
            material_map.refractive_index[:3, :],
            np.ones((3, self.grid.ny)),
        )
        np.testing.assert_array_equal(
            material_map.refractive_index[3:, :],
            np.full((3, self.grid.ny), 1.5),
        )
        np.testing.assert_array_equal(
            material_map.wave_speed[:3, :],
            np.ones((3, self.grid.ny)),
        )
        np.testing.assert_allclose(
            material_map.wave_speed[3:, :],
            np.full((3, self.grid.ny), 1.0 / 1.5),
        )

    def test_interface_index_must_leave_cells_on_both_sides(
        self,
    ) -> None:
        for interface_index in (0, self.grid.nx):
            with self.subTest(interface_index=interface_index):
                with self.assertRaisesRegex(
                    ValueError,
                    "at least one x cell",
                ):
                    create_planar_interface_material_map(
                        self.grid,
                        self.material,
                        interface_index=interface_index,
                        right_refractive_index=1.5,
                    )

    def test_interface_index_must_be_an_integer(self) -> None:
        with self.assertRaisesRegex(TypeError, "integer"):
            create_planar_interface_material_map(
                self.grid,
                self.material,
                interface_index=2.5,
                right_refractive_index=1.5,
            )

    def test_right_refractive_index_must_be_valid(self) -> None:
        for right_refractive_index in (
            0.0,
            -1.0,
            np.nan,
            np.inf,
        ):
            with self.subTest(
                right_refractive_index=right_refractive_index,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "finite and positive",
                ):
                    create_planar_interface_material_map(
                        self.grid,
                        self.material,
                        interface_index=3,
                        right_refractive_index=right_refractive_index,
                    )

    def test_simulation_accepts_planar_material_map(self) -> None:
        config = create_default_config()

        material_map = create_planar_interface_material_map(
            config.grid,
            config.material,
            interface_index=75,
            right_refractive_index=1.5,
        )

        simulation = Wave2DSimulation(
            config,
            material_map=material_map,
        )

        self.assertIs(simulation.material_map, material_map)
        self.assertTrue(
            np.all(
                simulation.material_map.refractive_index[:75, :]
                == 1.0
            )
        )
        self.assertTrue(
            np.all(
                simulation.material_map.refractive_index[75:, :]
                == 1.5
            )
        )

    def test_supplied_map_controls_cfl_validation(self) -> None:
        config = create_default_config()

        fast_material_map = create_planar_interface_material_map(
            config.grid,
            config.material,
            interface_index=75,
            right_refractive_index=0.5,
        )

        with self.assertRaisesRegex(
            ValueError,
            "Courant number",
        ):
            Wave2DSimulation(
                config,
                material_map=fast_material_map,
            )


class MaterialConfigValidationTest(unittest.TestCase):
    """Verify rejection of invalid material settings."""

    def test_nonpositive_reference_speed_is_rejected(self) -> None:
        config = create_default_config()
        invalid_config = replace(
            config,
            material=replace(
                config.material,
                reference_wave_speed=0.0,
            ),
        )

        with self.assertRaises(ValueError):
            validate_config(invalid_config)

    def test_nonpositive_refractive_index_is_rejected(self) -> None:
        config = create_default_config()
        invalid_config = replace(
            config,
            material=replace(
                config.material,
                background_refractive_index=0.0,
            ),
        )

        with self.assertRaises(ValueError):
            validate_config(invalid_config)


class MaterialMapValidationTest(unittest.TestCase):
    """Verify rejection of invalid material arrays."""

    def setUp(self) -> None:
        self.grid = GridConfig(nx=5, ny=5)

    def test_incorrect_refractive_index_shape_is_rejected(self) -> None:
        material_map = MaterialMap(
            refractive_index=np.ones((4, 5)),
            wave_speed=np.ones(self.grid.shape),
        )

        with self.assertRaisesRegex(ValueError, "shape"):
            validate_material_map(material_map, self.grid)

    def test_incorrect_wave_speed_shape_is_rejected(self) -> None:
        material_map = MaterialMap(
            refractive_index=np.ones(self.grid.shape),
            wave_speed=np.ones((5, 4)),
        )

        with self.assertRaisesRegex(ValueError, "shape"):
            validate_material_map(material_map, self.grid)

    def test_nonfinite_refractive_index_is_rejected(self) -> None:
        refractive_index = np.ones(self.grid.shape)
        refractive_index[2, 2] = np.nan

        material_map = MaterialMap(
            refractive_index=refractive_index,
            wave_speed=np.ones(self.grid.shape),
        )

        with self.assertRaisesRegex(ValueError, "finite"):
            validate_material_map(material_map, self.grid)

    def test_nonfinite_wave_speed_is_rejected(self) -> None:
        wave_speed = np.ones(self.grid.shape)
        wave_speed[2, 2] = np.inf

        material_map = MaterialMap(
            refractive_index=np.ones(self.grid.shape),
            wave_speed=wave_speed,
        )

        with self.assertRaisesRegex(ValueError, "finite"):
            validate_material_map(material_map, self.grid)

    def test_nonpositive_refractive_index_is_rejected(self) -> None:
        refractive_index = np.ones(self.grid.shape)
        refractive_index[2, 2] = 0.0

        material_map = MaterialMap(
            refractive_index=refractive_index,
            wave_speed=np.ones(self.grid.shape),
        )

        with self.assertRaisesRegex(ValueError, "positive"):
            validate_material_map(material_map, self.grid)

    def test_nonpositive_wave_speed_is_rejected(self) -> None:
        wave_speed = np.ones(self.grid.shape)
        wave_speed[2, 2] = -1.0

        material_map = MaterialMap(
            refractive_index=np.ones(self.grid.shape),
            wave_speed=wave_speed,
        )

        with self.assertRaisesRegex(ValueError, "positive"):
            validate_material_map(material_map, self.grid)


if __name__ == "__main__":
    unittest.main()
