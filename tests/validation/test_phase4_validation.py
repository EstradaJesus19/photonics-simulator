"""Cross-feature validation for the evolving Phase 4 geometry API."""

import unittest

import wavesim


EXPECTED_PHASE4_PUBLIC_NAMES = {
    "add_circular_region",
    "add_elliptical_region",
    "add_masked_region",
    "create_circular_mask",
    "create_elliptical_mask",
    "create_grid_coordinate_arrays",
    "validate_geometry_mask",
    "add_physical_rectangular_region",
    "create_rectangular_mask",
    "add_polygonal_region",
    "create_polygon_mask",
    "MaterialRegion",
    "compose_material_regions",
}


class Phase4PublicApiTests(unittest.TestCase):
    """Protect the Phase 4.1 package-level API."""

    def test_expected_phase4_names_are_public(self) -> None:
        for name in EXPECTED_PHASE4_PUBLIC_NAMES:
            with self.subTest(name=name):
                self.assertIn(name, wavesim.__all__)
                self.assertTrue(hasattr(wavesim, name))


if __name__ == "__main__":
    unittest.main()
