"""Tests for source and monitor visualization helpers."""

import unittest
from dataclasses import replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from simulations.wave2d_controlled_line_source import (
    ANALYSIS_START_STEP,
    ANALYSIS_STOP_STEP,
    create_scenario,
)
from wavesim.solver import Wave2DSimulation
from wavesim.visualization import (
    add_monitor_history_figure,
    add_source_and_monitor_overlays,
)


class SourceMonitorOverlayTests(unittest.TestCase):
    """Verify source and monitor annotations."""

    def setUp(self) -> None:
        self.config, material_map = create_scenario()
        self.simulation = Wave2DSimulation(
            self.config,
            material_map=material_map,
        )

    def tearDown(self) -> None:
        plt.close("all")

    def test_line_source_and_monitors_are_drawn(self) -> None:
        figure, axis = plt.subplots()

        add_source_and_monitor_overlays(
            axis,
            self.simulation,
        )

        labels = [
            line.get_label()
            for line in axis.lines
        ]

        self.assertIn("Line source", labels)
        self.assertIn("Monitor: first", labels)
        self.assertIn("Monitor: second", labels)


class MonitorHistoryFigureTests(unittest.TestCase):
    """Verify headless monitor-history plotting."""

    def tearDown(self) -> None:
        plt.close("all")

    def test_no_monitors_produces_no_figure(self) -> None:
        config, material_map = create_scenario()
        config = replace(
            config,
            monitors=(),
        )
        simulation = Wave2DSimulation(
            config,
            material_map=material_map,
        )

        self.assertIsNone(
            add_monitor_history_figure(simulation)
        )

    def test_history_figure_contains_one_line_per_monitor(self) -> None:
        config, material_map = create_scenario()
        simulation = Wave2DSimulation(
            config,
            material_map=material_map,
        )

        for _ in range(10):
            simulation.advance()

        figure = add_monitor_history_figure(simulation)
        axis = figure.axes[0]

        labels = [
            line.get_label()
            for line in axis.lines
        ]

        self.assertIn("first", labels)
        self.assertIn("second", labels)

    def test_analysis_window_is_shaded(self) -> None:
        config, material_map = create_scenario()
        simulation = Wave2DSimulation(
            config,
            material_map=material_map,
        )

        for _ in range(config.time.steps):
            simulation.advance()

        figure = add_monitor_history_figure(
            simulation,
            analysis_start_step=ANALYSIS_START_STEP,
            analysis_stop_step=ANALYSIS_STOP_STEP,
        )
        axis = figure.axes[0]

        self.assertEqual(len(axis.patches), 1)

    def test_partial_analysis_window_is_rejected(self) -> None:
        config, material_map = create_scenario()
        simulation = Wave2DSimulation(
            config,
            material_map=material_map,
        )

        with self.assertRaisesRegex(
            ValueError,
            "both be supplied",
        ):
            add_monitor_history_figure(
                simulation,
                analysis_start_step=0,
            )