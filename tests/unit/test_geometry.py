"""Tests for the shared Phase 4 geometry contract."""

import unittest

import numpy as np

from collections.abc import Sequence

from wavesim import (
    GridConfig,
    MaterialRegion,
    MaterialConfig,
    add_circular_region,
    add_elliptical_region,
    add_masked_region,
    add_physical_rectangular_region,
    create_background_refractive_index_array,
    create_circular_mask,
    create_elliptical_mask,
    create_grid_coordinate_arrays,
    create_material_map_from_refractive_index,
    create_polygon_mask,
    create_rectangular_mask,
    compose_material_regions,
    validate_geometry_mask,
    add_polygonal_region,

)


class GridCoordinateArrayTest(unittest.TestCase):
    def test_coordinates_follow_xy_array_orientation(self) -> None:
        grid = GridConfig(nx=3, ny=2, dx=0.5, dy=2.0)

        x, y = create_grid_coordinate_arrays(grid)

        np.testing.assert_array_equal(
            x,
            np.array([[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]]),
        )
        np.testing.assert_array_equal(
            y,
            np.array([[0.0, 2.0], [0.0, 2.0], [0.0, 2.0]]),
        )
        self.assertEqual(x.shape, grid.shape)
        self.assertEqual(y.shape, grid.shape)


class GeometryMaskTest(unittest.TestCase):
    def setUp(self) -> None:
        self.grid = GridConfig(nx=4, ny=3)

    def test_valid_mask_is_accepted(self) -> None:
        mask = np.zeros(self.grid.shape, dtype=bool)
        mask[1, 2] = True

        validate_geometry_mask(mask, self.grid)

    def test_mask_must_be_boolean_array_with_grid_shape(self) -> None:
        invalid_masks = (
            ([[True]], TypeError, "NumPy array"),
            (np.ones((3, 3), dtype=bool), ValueError, "shape"),
            (np.ones(self.grid.shape), TypeError, "boolean"),
            (np.zeros(self.grid.shape, dtype=bool), ValueError, "at least one"),
        )

        for mask, error_type, message in invalid_masks:
            with self.subTest(mask=mask):
                with self.assertRaisesRegex(error_type, message):
                    validate_geometry_mask(mask, self.grid)

    def test_masked_region_returns_copy_and_overwrites_selected_samples(
        self,
    ) -> None:
        background = np.ones(self.grid.shape)
        mask = np.zeros(self.grid.shape, dtype=bool)
        mask[0, 0] = True
        mask[2:, 1:] = True

        updated = add_masked_region(
            background,
            self.grid,
            mask=mask,
            region_refractive_index=1.75,
        )

        expected = background.copy()
        expected[mask] = 1.75
        np.testing.assert_array_equal(updated, expected)
        np.testing.assert_array_equal(background, np.ones(self.grid.shape))
        self.assertFalse(np.shares_memory(updated, background))

    def test_later_masked_region_wins_in_overlap(self) -> None:
        background = np.ones(self.grid.shape)
        first_mask = np.zeros(self.grid.shape, dtype=bool)
        first_mask[1:3, :] = True
        second_mask = np.zeros(self.grid.shape, dtype=bool)
        second_mask[2:, 1:] = True

        first = add_masked_region(
            background,
            self.grid,
            mask=first_mask,
            region_refractive_index=1.5,
        )
        second = add_masked_region(
            first,
            self.grid,
            mask=second_mask,
            region_refractive_index=2.0,
        )

        self.assertEqual(second[2, 1], 2.0)
        self.assertEqual(second[1, 1], 1.5)
        self.assertEqual(second[0, 0], 1.0)

    def test_masked_region_refractive_index_is_validated(self) -> None:
        mask = np.ones(self.grid.shape, dtype=bool)

        for value in (0.0, -1.0, np.nan, np.inf):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "finite and positive"):
                    add_masked_region(
                        np.ones(self.grid.shape),
                        self.grid,
                        mask=mask,
                        region_refractive_index=value,
                    )


class CircularMaskTest(unittest.TestCase):
    def test_circle_uses_physical_coordinates(self) -> None:
        grid = GridConfig(
            nx=7,
            ny=7,
            dx=0.5,
            dy=0.5,
        )

        mask = create_circular_mask(
            grid,
            center_x=1.5,
            center_y=1.5,
            radius=1.0,
        )

        self.assertTrue(mask[3, 3])
        self.assertTrue(mask[1, 3])
        self.assertTrue(mask[5, 3])
        self.assertTrue(mask[3, 1])
        self.assertTrue(mask[3, 5])

        self.assertFalse(mask[0, 3])
        self.assertFalse(mask[3, 0])
        self.assertFalse(mask[1, 1])

    def test_circle_includes_analytical_boundary(self) -> None:
        grid = GridConfig(nx=5, ny=5)

        mask = create_circular_mask(
            grid,
            center_x=2.0,
            center_y=2.0,
            radius=1.0,
        )

        expected = np.zeros(grid.shape, dtype=bool)
        expected[2, 2] = True
        expected[1, 2] = True
        expected[3, 2] = True
        expected[2, 1] = True
        expected[2, 3] = True

        np.testing.assert_array_equal(mask, expected)

    def test_circle_is_naturally_clipped_at_grid_edge(self) -> None:
        grid = GridConfig(nx=5, ny=5)

        mask = create_circular_mask(
            grid,
            center_x=0.0,
            center_y=2.0,
            radius=1.0,
        )

        self.assertTrue(mask[0, 2])
        self.assertTrue(mask[1, 2])
        self.assertTrue(mask[0, 1])
        self.assertTrue(mask[0, 3])
        self.assertEqual(np.count_nonzero(mask), 4)

    def test_circle_must_intersect_the_grid(self) -> None:
        grid = GridConfig(nx=5, ny=5)

        with self.assertRaisesRegex(
            ValueError,
            "at least one grid sample",
        ):
            create_circular_mask(
                grid,
                center_x=20.0,
                center_y=20.0,
                radius=1.0,
            )

    def test_circle_parameters_are_validated(self) -> None:
        grid = GridConfig(nx=5, ny=5)

        invalid_cases = (
            (np.nan, 2.0, 1.0, "center_x"),
            (2.0, np.inf, 1.0, "center_y"),
            (2.0, 2.0, 0.0, "radius"),
            (2.0, 2.0, -1.0, "radius"),
            (2.0, 2.0, np.inf, "radius"),
        )

        for center_x, center_y, radius, message in invalid_cases:
            with self.subTest(
                center_x=center_x,
                center_y=center_y,
                radius=radius,
            ):
                with self.assertRaisesRegex(
                    (TypeError, ValueError),
                    message,
                ):
                    create_circular_mask(
                        grid,
                        center_x=center_x,
                        center_y=center_y,
                        radius=radius,
                    )


class EllipticalMaskTest(unittest.TestCase):
    def test_ellipse_has_independent_physical_radii(self) -> None:
        grid = GridConfig(nx=9, ny=9)

        mask = create_elliptical_mask(
            grid,
            center_x=4.0,
            center_y=4.0,
            radius_x=3.0,
            radius_y=1.0,
        )

        self.assertTrue(mask[1, 4])
        self.assertTrue(mask[7, 4])
        self.assertTrue(mask[4, 3])
        self.assertTrue(mask[4, 5])

        self.assertFalse(mask[0, 4])
        self.assertFalse(mask[4, 2])
        self.assertFalse(mask[2, 3])

    def test_equal_ellipse_radii_match_circle(self) -> None:
        grid = GridConfig(
            nx=8,
            ny=7,
            dx=0.5,
            dy=0.75,
        )

        circle = create_circular_mask(
            grid,
            center_x=1.5,
            center_y=2.25,
            radius=1.25,
        )
        ellipse = create_elliptical_mask(
            grid,
            center_x=1.5,
            center_y=2.25,
            radius_x=1.25,
            radius_y=1.25,
        )

        np.testing.assert_array_equal(circle, ellipse)

    def test_ellipse_radii_are_validated_independently(self) -> None:
        grid = GridConfig(nx=5, ny=5)

        invalid_radii = (
            (0.0, 1.0, "radius_x"),
            (-1.0, 1.0, "radius_x"),
            (1.0, 0.0, "radius_y"),
            (1.0, np.nan, "radius_y"),
        )

        for radius_x, radius_y, message in invalid_radii:
            with self.subTest(
                radius_x=radius_x,
                radius_y=radius_y,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    message,
                ):
                    create_elliptical_mask(
                        grid,
                        center_x=2.0,
                        center_y=2.0,
                        radius_x=radius_x,
                        radius_y=radius_y,
                    )


class CurvedMaterialRegionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.grid = GridConfig(nx=7, ny=7)
        self.background = np.ones(self.grid.shape)

    def test_circular_region_assigns_only_selected_samples(self) -> None:
        updated = add_circular_region(
            self.background,
            self.grid,
            center_x=3.0,
            center_y=3.0,
            radius=1.0,
            region_refractive_index=1.5,
        )

        mask = create_circular_mask(
            self.grid,
            center_x=3.0,
            center_y=3.0,
            radius=1.0,
        )

        expected = self.background.copy()
        expected[mask] = 1.5

        np.testing.assert_array_equal(updated, expected)
        np.testing.assert_array_equal(
            self.background,
            np.ones(self.grid.shape),
        )

    def test_elliptical_region_can_overwrite_circle(self) -> None:
        with_circle = add_circular_region(
            self.background,
            self.grid,
            center_x=3.0,
            center_y=3.0,
            radius=2.0,
            region_refractive_index=1.5,
        )

        composed = add_elliptical_region(
            with_circle,
            self.grid,
            center_x=3.0,
            center_y=3.0,
            radius_x=1.0,
            radius_y=2.0,
            region_refractive_index=2.0,
        )

        self.assertEqual(composed[3, 3], 2.0)
        self.assertEqual(composed[1, 3], 1.5)
        self.assertEqual(composed[0, 0], 1.0)

    def test_region_refractive_index_is_validated(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "finite and positive",
        ):
            add_circular_region(
                self.background,
                self.grid,
                center_x=3.0,
                center_y=3.0,
                radius=1.0,
                region_refractive_index=0.0,
            )


class RotatedRectangleMaskTest(unittest.TestCase):
    def test_zero_angle_rectangle_uses_physical_dimensions(
        self,
    ) -> None:
        grid = GridConfig(nx=7, ny=7)

        mask = create_rectangular_mask(
            grid,
            center_x=3.0,
            center_y=3.0,
            width=4.0,
            height=2.0,
        )

        expected = np.zeros(grid.shape, dtype=bool)
        expected[1:6, 2:5] = True

        np.testing.assert_array_equal(mask, expected)

    def test_positive_angle_rotates_rectangle_counterclockwise(
        self,
    ) -> None:
        grid = GridConfig(nx=9, ny=9)

        mask = create_rectangular_mask(
            grid,
            center_x=4.0,
            center_y=4.0,
            width=4.0,
            height=2.0,
            angle_degrees=45.0,
        )

        self.assertTrue(mask[4, 4])
        self.assertTrue(mask[5, 5])
        self.assertTrue(mask[3, 3])

        self.assertFalse(mask[5, 3])
        self.assertFalse(mask[3, 5])

    def test_ninety_degrees_swaps_axis_aligned_extent(
        self,
    ) -> None:
        grid = GridConfig(nx=9, ny=9)

        mask = create_rectangular_mask(
            grid,
            center_x=4.0,
            center_y=4.0,
            width=4.0,
            height=2.0,
            angle_degrees=90.0,
        )

        self.assertTrue(mask[4, 2])
        self.assertTrue(mask[4, 6])
        self.assertTrue(mask[3, 4])
        self.assertTrue(mask[5, 4])

        self.assertFalse(mask[2, 4])
        self.assertFalse(mask[6, 4])

    def test_rectangle_is_clipped_by_finite_grid(
        self,
    ) -> None:
        grid = GridConfig(nx=5, ny=5)

        mask = create_rectangular_mask(
            grid,
            center_x=0.0,
            center_y=2.0,
            width=2.0,
            height=2.0,
        )

        expected = np.zeros(grid.shape, dtype=bool)
        expected[0:2, 1:4] = True

        np.testing.assert_array_equal(mask, expected)

    def test_rectangle_parameters_are_validated(self) -> None:
        grid = GridConfig(nx=5, ny=5)

        invalid_cases = (
            {
                "center_x": np.nan,
                "center_y": 2.0,
                "width": 2.0,
                "height": 1.0,
                "angle_degrees": 0.0,
                "message": "center_x",
            },
            {
                "center_x": 2.0,
                "center_y": 2.0,
                "width": 0.0,
                "height": 1.0,
                "angle_degrees": 0.0,
                "message": "width",
            },
            {
                "center_x": 2.0,
                "center_y": 2.0,
                "width": 2.0,
                "height": -1.0,
                "angle_degrees": 0.0,
                "message": "height",
            },
            {
                "center_x": 2.0,
                "center_y": 2.0,
                "width": 2.0,
                "height": 1.0,
                "angle_degrees": np.inf,
                "message": "angle_degrees",
            },
        )

        for case in invalid_cases:
            parameters = dict(case)
            message = parameters.pop("message")

            with self.subTest(parameters=parameters):
                with self.assertRaisesRegex(
                    (TypeError, ValueError),
                    message,
                ):
                    create_rectangular_mask(
                        grid,
                        **parameters,
                    )


class RotatedEllipseMaskTest(unittest.TestCase):
    def test_zero_angle_preserves_phase_4_2_behavior(
        self,
    ) -> None:
        grid = GridConfig(nx=9, ny=9)

        implicit_zero = create_elliptical_mask(
            grid,
            center_x=4.0,
            center_y=4.0,
            radius_x=3.0,
            radius_y=1.0,
        )
        explicit_zero = create_elliptical_mask(
            grid,
            center_x=4.0,
            center_y=4.0,
            radius_x=3.0,
            radius_y=1.0,
            angle_degrees=0.0,
        )

        np.testing.assert_array_equal(
            implicit_zero,
            explicit_zero,
        )

    def test_ninety_degree_rotation_swaps_ellipse_axes(
        self,
    ) -> None:
        grid = GridConfig(nx=9, ny=9)

        horizontal = create_elliptical_mask(
            grid,
            center_x=4.0,
            center_y=4.0,
            radius_x=3.0,
            radius_y=1.0,
        )
        vertical = create_elliptical_mask(
            grid,
            center_x=4.0,
            center_y=4.0,
            radius_x=3.0,
            radius_y=1.0,
            angle_degrees=90.0,
        )

        self.assertTrue(horizontal[1, 4])
        self.assertFalse(horizontal[4, 1])

        self.assertFalse(vertical[1, 4])
        self.assertTrue(vertical[4, 1])

    def test_invalid_ellipse_angle_is_rejected(self) -> None:
        grid = GridConfig(nx=5, ny=5)

        with self.assertRaisesRegex(
            ValueError,
            "angle_degrees",
        ):
            create_elliptical_mask(
                grid,
                center_x=2.0,
                center_y=2.0,
                radius_x=2.0,
                radius_y=1.0,
                angle_degrees=np.nan,
            )


class PhysicalRectangleRegionTest(unittest.TestCase):
    def test_physical_rectangle_applies_refractive_index(
        self,
    ) -> None:
        grid = GridConfig(nx=7, ny=7)
        background = np.ones(grid.shape)

        updated = add_physical_rectangular_region(
            background,
            grid,
            center_x=3.0,
            center_y=3.0,
            width=4.0,
            height=2.0,
            angle_degrees=0.0,
            region_refractive_index=1.75,
        )

        mask = create_rectangular_mask(
            grid,
            center_x=3.0,
            center_y=3.0,
            width=4.0,
            height=2.0,
        )

        expected = background.copy()
        expected[mask] = 1.75

        np.testing.assert_array_equal(updated, expected)
        np.testing.assert_array_equal(
            background,
            np.ones(grid.shape),
        )


class PolygonMaskTest(unittest.TestCase):
    def test_axis_aligned_square_includes_boundary(
        self,
    ) -> None:
        grid = GridConfig(nx=6, ny=6)

        mask = create_polygon_mask(
            grid,
            vertices=(
                (1.0, 1.0),
                (4.0, 1.0),
                (4.0, 4.0),
                (1.0, 4.0),
            ),
        )

        expected = np.zeros(grid.shape, dtype=bool)
        expected[1:5, 1:5] = True

        np.testing.assert_array_equal(mask, expected)

    def test_clockwise_and_counterclockwise_match(
        self,
    ) -> None:
        grid = GridConfig(nx=6, ny=6)

        counterclockwise = (
            (1.0, 1.0),
            (4.0, 1.0),
            (4.0, 4.0),
            (1.0, 4.0),
        )
        clockwise = tuple(reversed(counterclockwise))

        first = create_polygon_mask(
            grid,
            vertices=counterclockwise,
        )
        second = create_polygon_mask(
            grid,
            vertices=clockwise,
        )

        np.testing.assert_array_equal(first, second)

    def test_concave_polygon_excludes_notch(
        self,
    ) -> None:
        grid = GridConfig(nx=7, ny=7)

        mask = create_polygon_mask(
            grid,
            vertices=(
                (1.0, 1.0),
                (5.0, 1.0),
                (5.0, 5.0),
                (3.0, 3.0),
                (1.0, 5.0),
            ),
        )

        self.assertTrue(mask[2, 2])
        self.assertTrue(mask[4, 2])
        self.assertTrue(mask[3, 3])

        self.assertFalse(mask[3, 4])
        self.assertFalse(mask[0, 0])

    def test_polygon_is_clipped_by_grid(
        self,
    ) -> None:
        grid = GridConfig(nx=5, ny=5)

        mask = create_polygon_mask(
            grid,
            vertices=(
                (-2.0, 1.0),
                (2.0, 1.0),
                (2.0, 3.0),
                (-2.0, 3.0),
            ),
        )

        expected = np.zeros(grid.shape, dtype=bool)
        expected[0:3, 1:4] = True

        np.testing.assert_array_equal(mask, expected)

    def test_completely_outside_polygon_is_rejected(
        self,
    ) -> None:
        grid = GridConfig(nx=5, ny=5)

        with self.assertRaisesRegex(
            ValueError,
            "at least one grid sample",
        ):
            create_polygon_mask(
                grid,
                vertices=(
                    (10.0, 10.0),
                    (12.0, 10.0),
                    (11.0, 12.0),
                ),
            )

    def test_invalid_vertex_collections_are_rejected(
        self,
    ) -> None:
        grid = GridConfig(nx=5, ny=5)

        invalid_cases = (
            (
                ((1.0, 1.0), (2.0, 2.0)),
                "at least three",
            ),
            (
                ((1.0, 1.0, 0.0),) * 3,
                "shape",
            ),
            (
                (
                    (1.0, 1.0),
                    (3.0, 1.0),
                    (np.nan, 3.0),
                ),
                "finite",
            ),
            (
                (
                    (1.0, 1.0),
                    (3.0, 1.0),
                    (1.0, 1.0),
                ),
                "duplicates",
            ),
            (
                (
                    (1.0, 1.0),
                    (2.0, 2.0),
                    (3.0, 3.0),
                ),
                "nonzero area",
            ),
        )

        for vertices, message in invalid_cases:
            with self.subTest(vertices=vertices):
                with self.assertRaisesRegex(
                    (TypeError, ValueError),
                    message,
                ):
                    create_polygon_mask(
                        grid,
                        vertices=vertices,
                    )

    def test_self_intersecting_polygon_is_rejected(
        self,
    ) -> None:
        grid = GridConfig(nx=6, ny=6)

        with self.assertRaisesRegex(
            ValueError,
            "self-intersect",
        ):
            create_polygon_mask(
                grid,
                vertices=(
                    (1.0, 1.0),
                    (4.0, 4.0),
                    (1.0, 4.0),
                    (4.0, 1.0),
                ),
            )


class PolygonMaterialRegionTest(unittest.TestCase):
    def test_polygonal_region_applies_refractive_index(
        self,
    ) -> None:
        grid = GridConfig(nx=6, ny=6)
        background = np.ones(grid.shape)

        vertices = (
            (1.0, 1.0),
            (4.0, 1.0),
            (2.0, 4.0),
        )

        updated = add_polygonal_region(
            background,
            grid,
            vertices=vertices,
            region_refractive_index=1.8,
        )

        mask = create_polygon_mask(
            grid,
            vertices=vertices,
        )

        expected = background.copy()
        expected[mask] = 1.8

        np.testing.assert_array_equal(updated, expected)
        np.testing.assert_array_equal(
            background,
            np.ones(grid.shape),
        )


class MaterialRegionTest(unittest.TestCase):
    def test_region_owns_read_only_mask_copy(self) -> None:
        mask = np.zeros((4, 3), dtype=bool)
        mask[1, 2] = True

        region = MaterialRegion(
            mask=mask,
            refractive_index=1.5,
        )

        self.assertFalse(
            np.shares_memory(region.mask, mask)
        )
        self.assertFalse(region.mask.flags.writeable)

        mask[:, :] = False

        self.assertTrue(region.mask[1, 2])

        with self.assertRaises(ValueError):
            region.mask[0, 0] = True

    def test_region_rejects_invalid_mask(self) -> None:
        invalid_masks = (
            [[True]],
            np.ones((2, 2)),
            np.zeros((2, 2), dtype=bool),
        )

        for mask in invalid_masks:
            with self.subTest(mask=mask):
                with self.assertRaises(
                    (TypeError, ValueError),
                ):
                    MaterialRegion(
                        mask=mask,
                        refractive_index=1.5,
                    )

    def test_region_rejects_invalid_refractive_index(
        self,
    ) -> None:
        mask = np.ones((2, 2), dtype=bool)

        for value in (
            True,
            "1.5",
            0.0,
            -1.0,
            np.nan,
            np.inf,
        ):
            with self.subTest(value=value):
                with self.assertRaises(
                    (TypeError, ValueError),
                ):
                    MaterialRegion(
                        mask=mask,
                        refractive_index=value,
                    )


class MaterialRegionCompositionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.grid = GridConfig(nx=9, ny=9)
        self.background = np.ones(self.grid.shape)

    def test_mixed_regions_are_composed_in_order(
        self,
    ) -> None:
        circle_mask = create_circular_mask(
            self.grid,
            center_x=4.0,
            center_y=4.0,
            radius=3.0,
        )
        rectangle_mask = create_rectangular_mask(
            self.grid,
            center_x=4.0,
            center_y=4.0,
            width=2.0,
            height=6.0,
            angle_degrees=45.0,
        )
        polygon_mask = create_polygon_mask(
            self.grid,
            vertices=(
                (3.0, 3.0),
                (6.0, 3.0),
                (4.0, 6.0),
            ),
        )

        composed = compose_material_regions(
            self.background,
            self.grid,
            regions=(
                MaterialRegion(
                    mask=circle_mask,
                    refractive_index=1.5,
                ),
                MaterialRegion(
                    mask=rectangle_mask,
                    refractive_index=1.75,
                ),
                MaterialRegion(
                    mask=polygon_mask,
                    refractive_index=2.0,
                ),
            ),
        )

        expected = self.background.copy()
        expected[circle_mask] = 1.5
        expected[rectangle_mask] = 1.75
        expected[polygon_mask] = 2.0

        np.testing.assert_array_equal(
            composed,
            expected,
        )
        np.testing.assert_array_equal(
            self.background,
            np.ones(self.grid.shape),
        )

    def test_later_region_wins_in_overlap(self) -> None:
        first_mask = np.zeros(
            self.grid.shape,
            dtype=bool,
        )
        first_mask[2:7, 2:7] = True

        second_mask = np.zeros(
            self.grid.shape,
            dtype=bool,
        )
        second_mask[4:8, 4:8] = True

        composed = compose_material_regions(
            self.background,
            self.grid,
            regions=(
                MaterialRegion(first_mask, 1.5),
                MaterialRegion(second_mask, 2.0),
            ),
        )

        self.assertEqual(composed[3, 3], 1.5)
        self.assertEqual(composed[5, 5], 2.0)
        self.assertEqual(composed[7, 7], 2.0)
        self.assertEqual(composed[0, 0], 1.0)

    def test_empty_composition_returns_copy(self) -> None:
        composed = compose_material_regions(
            self.background,
            self.grid,
            regions=(),
        )

        np.testing.assert_array_equal(
            composed,
            self.background,
        )
        self.assertFalse(
            np.shares_memory(
                composed,
                self.background,
            )
        )
        self.assertTrue(
            np.issubdtype(
                composed.dtype,
                np.floating,
            )
        )

    def test_region_mask_must_match_grid(self) -> None:
        incorrect_mask = np.ones(
            (4, 4),
            dtype=bool,
        )

        region = MaterialRegion(
            mask=incorrect_mask,
            refractive_index=1.5,
        )

        with self.assertRaisesRegex(
            ValueError,
            "not aligned",
        ):
            compose_material_regions(
                self.background,
                self.grid,
                regions=(region,),
            )

    def test_composition_rejects_non_region_items(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "MaterialRegion",
        ):
            compose_material_regions(
                self.background,
                self.grid,
                regions=("not a region",),
            )


class ComposedMaterialMapTest(unittest.TestCase):
    def test_composed_array_can_be_finalized(
        self,
    ) -> None:
        grid = GridConfig(nx=7, ny=7)
        material = MaterialConfig(
            reference_wave_speed=1.0,
            background_refractive_index=1.0,
        )

        background = (
            create_background_refractive_index_array(
                grid,
                material,
            )
        )

        circle_mask = create_circular_mask(
            grid,
            center_x=3.0,
            center_y=3.0,
            radius=2.0,
        )

        refractive_index = compose_material_regions(
            background,
            grid,
            regions=(
                MaterialRegion(
                    circle_mask,
                    2.0,
                ),
            ),
        )

        material_map = (
            create_material_map_from_refractive_index(
                grid,
                material,
                refractive_index,
            )
        )

        np.testing.assert_array_equal(
            material_map.refractive_index[
                circle_mask
            ],
            np.full(
                np.count_nonzero(circle_mask),
                2.0,
            ),
        )
        np.testing.assert_array_equal(
            material_map.wave_speed[
                circle_mask
            ],
            np.full(
                np.count_nonzero(circle_mask),
                0.5,
            ),
        )


if __name__ == "__main__":
    unittest.main()
