"""Tests for reproducible geometry-gallery generation."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from simulations.materials.wave2d_geometry_gallery.figures import (
    GALLERY_FIGURE_NAME,
    generate_figures,
)


class GeometryGalleryFigureGenerationTest(
    unittest.TestCase
):
    """Verify headless creation of the gallery figure."""

    def tearDown(self) -> None:
        plt.close("all")

    def test_gallery_figure_is_saved(self) -> None:
        with TemporaryDirectory() as directory:
            output_paths = generate_figures(
                Path(directory)
            )

            self.assertEqual(
                len(output_paths),
                1,
            )
            self.assertEqual(
                output_paths[0].name,
                GALLERY_FIGURE_NAME,
            )
            self.assertTrue(
                output_paths[0].is_file()
            )
            self.assertGreater(
                output_paths[0].stat().st_size,
                0,
            )


if __name__ == "__main__":
    unittest.main()