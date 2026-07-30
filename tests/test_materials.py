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
    create_material_map_from_refractive_index,
    create_background_refractive_index_array,
    create_planar_interface_material_map,
    create_rectangular_material_map,
    create_uniform_material_map,
    add_rectangular_region,
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


class ReusableGeometryFunctionTest(unittest.TestCase):
    """Verify reusable refractive-index geometry operations."""

    def setUp(self) -> None:
        self.grid = GridConfig(nx=6, ny=5)
        self.material = MaterialConfig(
            reference_wave_speed=1.0,
            background_refractive_index=1.0,
        )

    def test_background_array_uses_configured_index(
        self,
    ) -> None:
        material = MaterialConfig(
            reference_wave_speed=1.0,
            background_refractive_index=1.25,
        )

        refractive_index = (
            create_background_refractive_index_array(
                self.grid,
                material,
            )
        )

        np.testing.assert_array_equal(
            refractive_index,
            np.full(self.grid.shape, 1.25),
        )
        self.assertTrue(
            np.issubdtype(
                refractive_index.dtype,
                np.floating,
            )
        )

    def test_rectangle_returns_copy_and_may_touch_edges(
        self,
    ) -> None:
        background = (
            create_background_refractive_index_array(
                self.grid,
                self.material,
            )
        )

        updated = add_rectangular_region(
            background,
            self.grid,
            x_start=0,
            x_stop=2,
            y_start=3,
            y_stop=self.grid.ny,
            region_refractive_index=1.5,
        )

        expected = np.ones(self.grid.shape)
        expected[0:2, 3:self.grid.ny] = 1.5

        np.testing.assert_array_equal(updated, expected)
        np.testing.assert_array_equal(
            background,
            np.ones(self.grid.shape),
        )
        self.assertFalse(
            np.shares_memory(updated, background)
        )

    def test_later_rectangle_overwrites_overlap(
        self,
    ) -> None:
        background = (
            create_background_refractive_index_array(
                self.grid,
                self.material,
            )
        )

        first = add_rectangular_region(
            background,
            self.grid,
            x_start=1,
            x_stop=5,
            y_start=1,
            y_stop=4,
            region_refractive_index=1.5,
        )
        second = add_rectangular_region(
            first,
            self.grid,
            x_start=3,
            x_stop=self.grid.nx,
            y_start=2,
            y_stop=self.grid.ny,
            region_refractive_index=2.0,
        )

        expected_first = np.ones(self.grid.shape)
        expected_first[1:5, 1:4] = 1.5

        expected_second = expected_first.copy()
        expected_second[
            3:self.grid.nx,
            2:self.grid.ny,
        ] = 2.0

        np.testing.assert_array_equal(
            first,
            expected_first,
        )
        np.testing.assert_array_equal(
            second,
            expected_second,
        )
        self.assertFalse(np.shares_memory(second, first))

    def test_general_rectangle_bounds_are_validated(
        self,
    ) -> None:
        background = np.ones(self.grid.shape)

        invalid_bounds = (
            (-1, 2, 1, 3),
            (1, self.grid.nx + 1, 1, 3),
            (2, 2, 1, 3),
            (3, 2, 1, 3),
            (1, 3, -1, 2),
            (1, 3, 1, self.grid.ny + 1),
            (1, 3, 2, 2),
            (1, 3, 3, 2),
        )

        for bounds in invalid_bounds:
            with self.subTest(bounds=bounds):
                with self.assertRaisesRegex(
                    ValueError,
                    "nonempty region",
                ):
                    add_rectangular_region(
                        background,
                        self.grid,
                        x_start=bounds[0],
                        x_stop=bounds[1],
                        y_start=bounds[2],
                        y_stop=bounds[3],
                        region_refractive_index=1.5,
                    )

    def test_general_rectangle_bounds_must_be_integers(
        self,
    ) -> None:
        background = np.ones(self.grid.shape)

        for invalid_x_start in (1.5, True):
            with self.subTest(
                invalid_x_start=invalid_x_start,
            ):
                with self.assertRaisesRegex(
                    TypeError,
                    "integer",
                ):
                    add_rectangular_region(
                        background,
                        self.grid,
                        x_start=invalid_x_start,
                        x_stop=3,
                        y_start=1,
                        y_stop=3,
                        region_refractive_index=1.5,
                    )

    def test_general_rectangle_index_is_validated(
        self,
    ) -> None:
        background = np.ones(self.grid.shape)

        for invalid_index in (
            0.0,
            -1.0,
            np.nan,
            np.inf,
        ):
            with self.subTest(invalid_index=invalid_index):
                with self.assertRaisesRegex(
                    ValueError,
                    "finite and positive",
                ):
                    add_rectangular_region(
                        background,
                        self.grid,
                        x_start=1,
                        x_stop=3,
                        y_start=1,
                        y_stop=3,
                        region_refractive_index=invalid_index,
                    )


class MaterialMapFinalizationTest(unittest.TestCase):
    """Verify finalization of completed refractive-index arrays."""

    def setUp(self) -> None:
        self.grid = GridConfig(nx=4, ny=3)
        self.material = MaterialConfig(
            reference_wave_speed=2.0,
            background_refractive_index=1.0,
        )

    def test_wave_speed_is_derived_from_defensive_float_copy(
        self,
    ) -> None:
        source_index = np.ones(
            self.grid.shape,
            dtype=int,
        )
        source_index[1:3, 1:] = 2

        expected_index = source_index.astype(float)
        expected_speed = 2.0 / expected_index

        material_map = (
            create_material_map_from_refractive_index(
                self.grid,
                self.material,
                source_index,
            )
        )

        np.testing.assert_array_equal(
            material_map.refractive_index,
            expected_index,
        )
        np.testing.assert_allclose(
            material_map.wave_speed,
            expected_speed,
        )

        self.assertTrue(
            np.issubdtype(
                material_map.refractive_index.dtype,
                np.floating,
            )
        )
        self.assertFalse(
            np.shares_memory(
                material_map.refractive_index,
                source_index,
            )
        )

        source_index[:, :] = 4

        np.testing.assert_array_equal(
            material_map.refractive_index,
            expected_index,
        )

    def test_incorrect_shape_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "shape"):
            create_material_map_from_refractive_index(
                self.grid,
                self.material,
                np.ones((3, 3)),
            )

    def test_invalid_refractive_indices_are_rejected(
        self,
    ) -> None:
        invalid_values = (
            (0.0, "positive"),
            (-1.0, "positive"),
            (np.nan, "finite"),
            (np.inf, "finite"),
        )

        for value, expected_message in invalid_values:
            with self.subTest(value=value):
                refractive_index = np.ones(self.grid.shape)
                refractive_index[1, 1] = value

                with self.assertRaisesRegex(
                    ValueError,
                    expected_message,
                ):
                    create_material_map_from_refractive_index(
                        self.grid,
                        self.material,
                        refractive_index,
                    )


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


class RectangularMaterialMapTest(unittest.TestCase):
    """Verify construction of an embedded rectangular material."""

    def setUp(self) -> None:
        self.grid = GridConfig(nx=8, ny=7)
        self.material = MaterialConfig(
            reference_wave_speed=1.0,
            background_refractive_index=1.0,
        )

    def test_rectangle_regions_and_wave_speeds(self) -> None:
        material_map = create_rectangular_material_map(
            self.grid,
            self.material,
            x_start=2,
            x_stop=6,
            y_start=2,
            y_stop=5,
            rectangle_refractive_index=2.0,
        )

        expected_index = np.ones(self.grid.shape)
        expected_index[2:6, 2:5] = 2.0

        expected_speed = np.ones(self.grid.shape)
        expected_speed[2:6, 2:5] = 0.5

        np.testing.assert_array_equal(
            material_map.refractive_index,
            expected_index,
        )
        np.testing.assert_array_equal(
            material_map.wave_speed,
            expected_speed,
        )

    def test_rectangle_must_remain_strictly_inside_grid(
        self,
    ) -> None:
        invalid_bounds = (
            (0, 6, 2, 5),
            (2, self.grid.nx, 2, 5),
            (2, 6, 0, 5),
            (2, 6, 2, self.grid.ny),
            (4, 4, 2, 5),
            (5, 4, 2, 5),
            (2, 6, 4, 4),
            (2, 6, 5, 4),
        )

        for bounds in invalid_bounds:
            with self.subTest(bounds=bounds):
                with self.assertRaisesRegex(
                    ValueError,
                    "nonempty region",
                ):
                    create_rectangular_material_map(
                        self.grid,
                        self.material,
                        x_start=bounds[0],
                        x_stop=bounds[1],
                        y_start=bounds[2],
                        y_stop=bounds[3],
                        rectangle_refractive_index=2.0,
                    )

    def test_rectangle_bounds_must_be_integers(self) -> None:
        with self.assertRaisesRegex(TypeError, "integer"):
            create_rectangular_material_map(
                self.grid,
                self.material,
                x_start=2.5,
                x_stop=6,
                y_start=2,
                y_stop=5,
                rectangle_refractive_index=2.0,
            )

    def test_rectangle_refractive_index_must_be_valid(
        self,
    ) -> None:
        for rectangle_refractive_index in (
            0.0,
            -1.0,
            np.nan,
            np.inf,
        ):
            with self.subTest(
                rectangle_refractive_index=(
                    rectangle_refractive_index
                ),
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "finite and positive",
                ):
                    create_rectangular_material_map(
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


if __name__ == "__main__":
    unittest.main()
