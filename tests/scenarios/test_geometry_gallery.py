"""Tests for the Phase 4 advanced-geometry gallery."""

from itertools import combinations
import unittest

import numpy as np

from simulations.materials.wave2d_geometry_gallery.maps import (
    BACKGROUND_REFRACTIVE_INDEX,
    COMPOSITION_CIRCLE_INDEX,
    COMPOSITION_POLYGON_INDEX,
    COMPOSITION_RECTANGLE_INDEX,
    GALLERY_CASE_NAMES,
    GRID_NX,
    GRID_NY,
    SINGLE_REGION_REFRACTIVE_INDEX,
    create_gallery_maps,
)


class GeometryGalleryTest(unittest.TestCase):
    """Verify reproducible gallery-map construction."""

    def setUp(self) -> None:
        self.grid, self.gallery_maps = (
            create_gallery_maps()
        )

    def test_expected_cases_are_created(self) -> None:
        self.assertEqual(
            self.grid.shape,
            (GRID_NX, GRID_NY),
        )
        self.assertEqual(
            tuple(self.gallery_maps),
            GALLERY_CASE_NAMES,
        )

    def test_maps_are_aligned_and_physical(
        self,
    ) -> None:
        for name, material_map in (
            self.gallery_maps.items()
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    material_map.refractive_index.shape,
                    self.grid.shape,
                )
                self.assertEqual(
                    material_map.wave_speed.shape,
                    self.grid.shape,
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
                        material_map.refractive_index
                        > 0.0
                    )
                )

                np.testing.assert_allclose(
                    material_map.wave_speed,
                    1.0
                    / material_map.refractive_index,
                )

    def test_single_region_cases_use_two_indices(
        self,
    ) -> None:
        for name in GALLERY_CASE_NAMES[:-1]:
            with self.subTest(name=name):
                np.testing.assert_array_equal(
                    np.unique(
                        self.gallery_maps[
                            name
                        ].refractive_index
                    ),
                    np.array(
                        (
                            BACKGROUND_REFRACTIVE_INDEX,
                            SINGLE_REGION_REFRACTIVE_INDEX,
                        )
                    ),
                )

    def test_composition_keeps_all_region_indices(
        self,
    ) -> None:
        composition = self.gallery_maps[
            "ordered_composition"
        ].refractive_index

        np.testing.assert_array_equal(
            np.unique(composition),
            np.array(
                (
                    BACKGROUND_REFRACTIVE_INDEX,
                    COMPOSITION_CIRCLE_INDEX,
                    COMPOSITION_RECTANGLE_INDEX,
                    COMPOSITION_POLYGON_INDEX,
                )
            ),
        )

    def test_single_shapes_are_geometrically_distinct(
        self,
    ) -> None:
        foreground_masks = {
            name: (
                self.gallery_maps[
                    name
                ].refractive_index
                != BACKGROUND_REFRACTIVE_INDEX
            )
            for name in GALLERY_CASE_NAMES[:-1]
        }

        for first_name, second_name in combinations(
            foreground_masks,
            2,
        ):
            with self.subTest(
                first=first_name,
                second=second_name,
            ):
                self.assertFalse(
                    np.array_equal(
                        foreground_masks[first_name],
                        foreground_masks[second_name],
                    )
                )


if __name__ == "__main__":
    unittest.main()