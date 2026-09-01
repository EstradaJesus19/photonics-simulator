"""Tests for headless scalar-field monitors."""

import unittest
from dataclasses import replace
from unittest.mock import patch

import numpy as np

from wavesim.analysis import estimate_average_power
from wavesim.config import (
    FieldMonitorConfig,
    FluxMonitorConfig,
    create_default_config,
    validate_config,
)
from wavesim.monitors import (
    compute_flux_power_history,
    create_flux_monitor_states,
    create_monitor_states,
    integrate_flux_profile,
    record_flux_monitor_samples,
    record_monitor_samples,
    sample_field_monitor,
    sample_flux_monitor,
)
from wavesim.solver import Wave2DSimulation
from wavesim.analysis import estimate_average_power


class MonitorSamplingTests(unittest.TestCase):
    """Verify point and line sampling."""

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

    def test_horizontal_line_monitor_returns_coherent_mean(
        self,
    ) -> None:
        field = np.zeros((10, 12))
        field[2:6, 7] = [1.0, 2.0, 3.0, 4.0]
        monitor = FieldMonitorConfig(
            name="horizontal",
            kind="horizontal_line",
            y=7,
            x_start=2,
            x_stop=6,
        )

        self.assertEqual(
            sample_field_monitor(field, monitor),
            2.5,
        )


class FluxMonitorSamplingTests(unittest.TestCase):
    """Verify face-profile sampling and aperture integration."""

    def setUp(self) -> None:
        self.flux_x = np.arange(9 * 12, dtype=float).reshape(9, 12)
        self.flux_y = np.arange(10 * 11, dtype=float).reshape(10, 11)

    def test_x_monitor_stores_selected_face_profile(self) -> None:
        monitor = FluxMonitorConfig(
            name="x_flux",
            axis="x",
            face_index=4,
            transverse_start=3,
            transverse_stop=7,
        )

        profile = sample_flux_monitor(
            self.flux_x,
            self.flux_y,
            monitor,
        )

        np.testing.assert_array_equal(
            profile,
            self.flux_x[4, 3:7],
        )
        self.assertFalse(profile.flags.writeable)
        self.assertFalse(np.shares_memory(profile, self.flux_x))

    def test_y_monitor_stores_selected_face_profile(self) -> None:
        monitor = FluxMonitorConfig(
            name="y_flux",
            axis="y",
            face_index=5,
            transverse_start=2,
            transverse_stop=6,
        )

        profile = sample_flux_monitor(
            self.flux_x,
            self.flux_y,
            monitor,
        )

        np.testing.assert_array_equal(
            profile,
            self.flux_y[2:6, 5],
        )

    def test_profile_integration_uses_transverse_spacing(self) -> None:
        base = create_default_config()
        grid = replace(base.grid, dx=2.0, dy=0.5)
        profile = np.array([1.0, 2.0, 3.0])
        x_monitor = FluxMonitorConfig(
            name="x_flux",
            axis="x",
            face_index=4,
            transverse_start=3,
            transverse_stop=6,
        )
        y_monitor = FluxMonitorConfig(
            name="y_flux",
            axis="y",
            face_index=5,
            transverse_start=2,
            transverse_stop=5,
        )

        self.assertEqual(
            integrate_flux_profile(profile, x_monitor, grid),
            3.0,
        )
        self.assertEqual(
            integrate_flux_profile(profile, y_monitor, grid),
            12.0,
        )

    def test_recording_preserves_integer_time_and_profile(self) -> None:
        monitor = FluxMonitorConfig(
            name="x_flux",
            axis="x",
            face_index=4,
            transverse_start=3,
            transverse_stop=7,
        )
        states = create_flux_monitor_states((monitor,))

        record_flux_monitor_samples(
            (monitor,),
            states,
            self.flux_x,
            self.flux_y,
            step_index=3,
            dt=0.4,
        )

        state = states["x_flux"]
        self.assertEqual(state.steps, [3])
        np.testing.assert_allclose(state.times, [1.2])
        np.testing.assert_array_equal(
            state.profiles[0],
            self.flux_x[4, 3:7],
        )

    def test_stored_profiles_support_average_power_analysis(
        self,
    ) -> None:
        base = create_default_config()
        grid = replace(base.grid, dx=2.0, dy=0.5)
        monitor = FluxMonitorConfig(
            name="x_flux",
            axis="x",
            face_index=4,
            transverse_start=3,
            transverse_stop=6,
        )
        state = create_flux_monitor_states((monitor,))["x_flux"]

        for step in range(20):
            state.steps.append(step)
            state.times.append(step * 0.1)

            profile = np.full(3, 2.0)
            profile.setflags(write=False)
            state.profiles.append(profile)

        powers = compute_flux_power_history(
            state,
            monitor,
            grid,
        )

        result = estimate_average_power(
            powers,
            dt=0.1,
            start_step=5,
            stop_step=15,
        )

        # Three faces × flux 2 × dy 0.5 = power 3.
        self.assertEqual(result.mean_power, 3.0)
        self.assertAlmostEqual(
            result.transported_energy,
            3.0,
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

    def test_flux_history_uses_current_step_after_source(self) -> None:
        config = create_default_config()
        monitor = FluxMonitorConfig(
            name="transmitted",
            axis="x",
            face_index=20,
            transverse_start=30,
            transverse_stop=34,
        )
        config = replace(
            config,
            flux_monitors=(monitor,),
        )
        simulation = Wave2DSimulation(config)
        stepped_field = np.zeros(config.grid.shape)
        expected_flux_x = np.zeros(
            (config.grid.nx - 1, config.grid.ny)
        )
        expected_flux_y = np.zeros(
            (config.grid.nx, config.grid.ny - 1)
        )
        expected_flux_x[20, 30:34] = [1.0, 2.0, 3.0, 4.0]

        def inject_marker(
            field,
            step_index,
            supplied_config,
            source_profile,
        ) -> None:
            field[10, 10] = 9.0

        def observe_source_then_return_flux(
            previous,
            current,
            next_field,
            supplied_config,
        ):
            self.assertEqual(next_field[10, 10], 9.0)
            return expected_flux_x, expected_flux_y

        with (
            patch(
                "wavesim.solver.step_wave",
                return_value=stepped_field,
            ),
            patch(
                "wavesim.solver.apply_source",
                side_effect=inject_marker,
            ),
            patch(
                "wavesim.solver.compute_energy_flux",
                side_effect=observe_source_then_return_flux,
            ),
        ):
            simulation.advance()

        state = simulation.flux_monitor_states["transmitted"]
        self.assertEqual(state.steps, [0])
        self.assertEqual(state.times, [0.0])
        np.testing.assert_array_equal(
            state.profiles[0],
            [1.0, 2.0, 3.0, 4.0],
        )


class MonitorConfigTests(unittest.TestCase):
    """Verify monitor configuration validation."""

    def setUp(self) -> None:
        self.config = create_default_config()

    def test_default_configuration_has_no_monitors(self) -> None:
        self.assertEqual(self.config.monitors, ())
        self.assertEqual(self.config.flux_monitors, ())
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

    def test_horizontal_line_monitor_is_validated(self) -> None:
        monitor = FieldMonitorConfig(
            name="horizontal",
            kind="horizontal_line",
            y=30,
            x_start=20,
            x_stop=40,
        )

        validate_config(
            replace(
                self.config,
                monitors=(monitor,),
            )
        )

    def test_flux_monitor_axes_and_bounds_are_validated(self) -> None:
        monitors = (
            FluxMonitorConfig(
                name="x_flux",
                axis="x",
                face_index=20,
                transverse_start=10,
                transverse_stop=30,
            ),
            FluxMonitorConfig(
                name="y_flux",
                axis="y",
                face_index=20,
                transverse_start=10,
                transverse_stop=30,
            ),
        )

        validate_config(
            replace(
                self.config,
                flux_monitors=monitors,
            )
        )

    def test_monitor_names_are_unique_across_monitor_types(self) -> None:
        field_monitor = FieldMonitorConfig(
            name="shared",
            kind="point",
            x=20,
            y=30,
        )
        flux_monitor = FluxMonitorConfig(
            name="shared",
            axis="x",
            face_index=40,
            transverse_start=20,
            transverse_stop=30,
        )

        with self.assertRaisesRegex(
            ValueError,
            "Duplicate monitor name",
        ):
            validate_config(
                replace(
                    self.config,
                    monitors=(field_monitor,),
                    flux_monitors=(flux_monitor,),
                )
            )

    def test_point_source_overlap_is_rejected_for_both_axes(
        self,
    ) -> None:
        source = self.config.source
        monitors = (
            FluxMonitorConfig(
                name="x_overlap",
                axis="x",
                face_index=source.x - 1,
                transverse_start=source.y,
                transverse_stop=source.y + 1,
            ),
            FluxMonitorConfig(
                name="y_overlap",
                axis="y",
                face_index=source.y,
                transverse_start=source.x,
                transverse_stop=source.x + 1,
            ),
        )

        for monitor in monitors:
            with self.subTest(axis=monitor.axis):
                with self.assertRaisesRegex(
                    ValueError,
                    "overlaps the active source",
                ):
                    validate_config(
                        replace(
                            self.config,
                            flux_monitors=(monitor,),
                        )
                    )

    def test_line_source_overlap_is_rejected_for_both_axes(
        self,
    ) -> None:
        config = replace(
            self.config,
            source=replace(
                self.config.source,
                kind="line_sine",
                x=20,
                y_start=30,
                y_stop=40,
            ),
        )
        monitors = (
            FluxMonitorConfig(
                name="x_overlap",
                axis="x",
                face_index=19,
                transverse_start=35,
                transverse_stop=45,
            ),
            FluxMonitorConfig(
                name="y_overlap",
                axis="y",
                face_index=29,
                transverse_start=15,
                transverse_stop=25,
            ),
        )

        for monitor in monitors:
            with self.subTest(axis=monitor.axis):
                with self.assertRaisesRegex(
                    ValueError,
                    "overlaps the active source",
                ):
                    validate_config(
                        replace(
                            config,
                            flux_monitors=(monitor,),
                        )
                    )

class FluxPowerHistoryTests(unittest.TestCase):
    """Verify conversion from stored flux profiles to signed power."""

    def setUp(self) -> None:
        base = create_default_config()
        self.grid = replace(base.grid, dx=2.0, dy=0.5)
        self.monitor = FluxMonitorConfig(
            name="x_flux",
            axis="x",
            face_index=4,
            transverse_start=3,
            transverse_stop=6,
        )

    def create_state(self):
        """Return one empty state for the configured test monitor."""
        return create_flux_monitor_states(
            (self.monitor,)
        )[self.monitor.name]

    def test_power_history_is_derived_from_stored_profiles(
        self,
    ) -> None:
        state = self.create_state()

        state.steps.extend([0, 1])
        state.times.extend([0.0, 0.4])
        state.profiles.extend(
            [
                np.array([1.0, 2.0, 3.0]),
                np.array([-2.0, -2.0, -2.0]),
            ]
        )

        powers = compute_flux_power_history(
            state,
            self.monitor,
            self.grid,
        )

        np.testing.assert_allclose(
            powers,
            [3.0, -3.0],
        )

    def test_history_lists_must_have_equal_lengths(self) -> None:
        state = self.create_state()
        state.steps.append(0)

        with self.assertRaisesRegex(ValueError, "matching lengths"):
            compute_flux_power_history(
                state,
                self.monitor,
                self.grid,
            )

    def test_profiles_must_be_one_dimensional(self) -> None:
        state = self.create_state()
        state.steps.append(0)
        state.times.append(0.0)
        state.profiles.append(np.zeros((1, 3)))

        with self.assertRaisesRegex(ValueError, "one-dimensional"):
            compute_flux_power_history(
                state,
                self.monitor,
                self.grid,
            )

    def test_profile_length_must_match_aperture(self) -> None:
        state = self.create_state()
        state.steps.append(0)
        state.times.append(0.0)
        state.profiles.append(np.zeros(2))

        with self.assertRaisesRegex(ValueError, "configured aperture"):
            compute_flux_power_history(
                state,
                self.monitor,
                self.grid,
            )

    def test_profiles_must_be_finite(self) -> None:
        for invalid_value in (np.nan, np.inf):
            with self.subTest(invalid_value=invalid_value):
                state = self.create_state()
                state.steps.append(0)
                state.times.append(0.0)
                profile = np.zeros(3)
                profile[1] = invalid_value
                state.profiles.append(profile)

                with self.assertRaisesRegex(ValueError, "finite"):
                    compute_flux_power_history(
                        state,
                        self.monitor,
                        self.grid,
                    )
