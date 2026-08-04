"""Tests for headless scalar-field monitors."""

import unittest
from dataclasses import replace
from unittest.mock import patch

import numpy as np

from wavesim.config import (
    FieldMonitorConfig,
    create_default_config,
    validate_config,
)
from wavesim.monitors import (
    create_monitor_states,
    record_monitor_samples,
    sample_field_monitor,
)
from wavesim.solver import Wave2DSimulation


class MonitorSamplingTests(unittest.TestCase):
    """Verify point and vertical-line sampling."""

    def test_point_monitor_samples_one_cell(self) -> None:
        field = np.zeros((10, 12))
        field[4, 7] = 3.5
        monitor = FieldMonitorConfig(
            name="point",
            kind="point",
            x=4,
            y=7,
        )

        self.assertEqual(
            sample_field_monitor(field, monitor),
            3.5,
        )

    def test_vertical_line_monitor_returns_coherent_mean(self) -> None:
        field = np.zeros((10, 12))
        field[4, 3:7] = [1.0, 2.0, 3.0, 4.0]
        monitor = FieldMonitorConfig(
            name="line",
            kind="vertical_line",
            x=4,
            y_start=3,
            y_stop=7,
        )

        self.assertEqual(
            sample_field_monitor(field, monitor),
            2.5,
        )

    def test_line_monitor_uses_half_open_bounds(self) -> None:
        field = np.zeros((10, 12))
        field[4, 3:7] = 2.0
        field[4, 2] = 100.0
        field[4, 7] = 100.0

        monitor = FieldMonitorConfig(
            name="line",
            kind="vertical_line",
            x=4,
            y_start=3,
            y_stop=7,
        )

        self.assertEqual(
            sample_field_monitor(field, monitor),
            2.0,
        )


class MonitorHistoryTests(unittest.TestCase):
    """Verify monitor time indexing and history growth."""

    def test_states_include_the_initial_sample(self) -> None:
        field = np.zeros((10, 12))
        field[4, 7] = 3.5
        monitor = FieldMonitorConfig(
            name="point",
            kind="point",
            x=4,
            y=7,
        )

        states = create_monitor_states(
            (monitor,),
            field,
        )

        state = states["point"]

        self.assertEqual(state.steps, [0])
        self.assertEqual(state.times, [0.0])
        self.assertEqual(state.values, [3.5])

    def test_recording_appends_step_time_and_value(self) -> None:
        field = np.zeros((10, 12))
        monitor = FieldMonitorConfig(
            name="point",
            kind="point",
            x=4,
            y=7,
        )
        states = create_monitor_states(
            (monitor,),
            field,
        )

        field[4, 7] = 6.0

        record_monitor_samples(
            (monitor,),
            states,
            field,
            step_index=3,
            dt=0.4,
        )

        state = states["point"]

        self.assertEqual(state.steps, [0, 3])
        np.testing.assert_allclose(
            state.times,
            [0.0, 1.2],
        )
        self.assertEqual(state.values, [0.0, 6.0])

    def test_simulation_history_matches_energy_history_length(self) -> None:
        config = create_default_config()
        monitor = FieldMonitorConfig(
            name="center",
            kind="point",
            x=config.source.x,
            y=config.source.y,
        )
        config = replace(
            config,
            monitors=(monitor,),
        )

        simulation = Wave2DSimulation(config)

        for _ in range(5):
            simulation.advance()

        state = simulation.monitor_states["center"]

        self.assertEqual(state.steps, [0, 1, 2, 3, 4, 5])
        np.testing.assert_allclose(
            state.times,
            np.arange(6) * config.time.dt,
        )
        self.assertEqual(len(state.values), 6)
        self.assertEqual(
            len(state.values),
            len(simulation.state.energy_history),
        )

    def test_monitor_observes_source_injected_field(self) -> None:
        config = create_default_config()
        monitor = FieldMonitorConfig(
            name="center",
            kind="point",
            x=config.source.x,
            y=config.source.y,
        )
        config = replace(
            config,
            monitors=(monitor,),
        )
        simulation = Wave2DSimulation(config)
        stepped_field = np.zeros(config.grid.shape)

        def inject_known_value(
            field,
            step_index,
            supplied_config,
            source_profile,
        ) -> None:
            field[monitor.x, monitor.y] = 9.0

        with (
            patch(
                "wavesim.solver.step_wave",
                return_value=stepped_field,
            ),
            patch(
                "wavesim.solver.apply_source",
                side_effect=inject_known_value,
            ),
        ):
            simulation.advance()

        self.assertEqual(
            simulation.monitor_states["center"].values,
            [0.0, 9.0],
        )


class MonitorConfigTests(unittest.TestCase):
    """Verify monitor configuration validation."""

    def setUp(self) -> None:
        self.config = create_default_config()

    def test_default_configuration_has_no_monitors(self) -> None:
        self.assertEqual(self.config.monitors, ())
        validate_config(self.config)

    def test_duplicate_monitor_names_are_rejected(self) -> None:
        first = FieldMonitorConfig(
            name="probe",
            kind="point",
            x=20,
            y=30,
        )
        second = FieldMonitorConfig(
            name="probe",
            kind="point",
            x=40,
            y=50,
        )
        config = replace(
            self.config,
            monitors=(first, second),
        )

        with self.assertRaisesRegex(
            ValueError,
            "Duplicate monitor name",
        ):
            validate_config(config)

    def test_blank_monitor_name_is_rejected(self) -> None:
        monitor = FieldMonitorConfig(
            name="   ",
            kind="point",
            x=20,
            y=30,
        )

        with self.assertRaisesRegex(
            ValueError,
            "non-whitespace",
        ):
            validate_config(
                replace(
                    self.config,
                    monitors=(monitor,),
                )
            )

    def test_point_monitor_must_be_interior(self) -> None:
        monitor = FieldMonitorConfig(
            name="point",
            kind="point",
            x=20,
            y=0,
        )

        with self.assertRaisesRegex(
            ValueError,
            "inside the interior domain",
        ):
            validate_config(
                replace(
                    self.config,
                    monitors=(monitor,),
                )
            )

    def test_line_monitor_requires_bounds(self) -> None:
        monitor = FieldMonitorConfig(
            name="line",
            kind="vertical_line",
            x=20,
        )

        with self.assertRaisesRegex(
            ValueError,
            "require y_start and y_stop",
        ):
            validate_config(
                replace(
                    self.config,
                    monitors=(monitor,),
                )
            )

    def test_line_monitor_rejects_invalid_bounds(self) -> None:
        for y_start, y_stop in (
            (0, 20),
            (20, 20),
            (30, 20),
            (20, self.config.grid.ny),
        ):
            with self.subTest(
                y_start=y_start,
                y_stop=y_stop,
            ):
                monitor = FieldMonitorConfig(
                    name="line",
                    kind="vertical_line",
                    x=20,
                    y_start=y_start,
                    y_stop=y_stop,
                )

                with self.assertRaisesRegex(
                    ValueError,
                    "half-open interval",
                ):
                    validate_config(
                        replace(
                            self.config,
                            monitors=(monitor,),
                        )
                    )