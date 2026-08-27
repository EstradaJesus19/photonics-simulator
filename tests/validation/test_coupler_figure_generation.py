"""Tests for reproducible Phase 4.7 figure generation."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from simulations.structures.wave2d_directional_coupler.figures import (
    FIELD_FIGURE_NAME,
    HISTORY_FIGURE_NAME,
    MATERIAL_FIGURE_NAME,
    RESPONSE_FIGURE_NAME,
    generate_figures,
)


class CouplerFigureGenerationTest(unittest.TestCase):
    """Verify headless creation of coupler figures."""

    def tearDown(self) -> None:
        plt.close("all")

    def test_all_documentation_figures_are_saved(
        self,
    ) -> None:
        expected_names = {
            MATERIAL_FIGURE_NAME,
            FIELD_FIGURE_NAME,
            HISTORY_FIGURE_NAME,
            RESPONSE_FIGURE_NAME,
        }

        with TemporaryDirectory() as directory:
            output_paths = generate_figures(
                Path(directory)
            )

            self.assertEqual(
                {
                    path.name
                    for path in output_paths
                },
                expected_names,
            )

            for path in output_paths:
                with self.subTest(path=path):
                    self.assertTrue(path.is_file())
                    self.assertGreater(
                        path.stat().st_size,
                        0,
                    )