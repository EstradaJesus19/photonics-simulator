"""Regression tests for the established Phase 2 source behavior."""

import unittest
from dataclasses import replace
from unittest.mock import patch

import numpy as np

from wavesim.config import (
    create_default_config,
    validate_config,
)
from wavesim.solver import (
    Wave2DSimulation,
    apply_source,
)
from wavesim.sources import (
    compute_source_envelope,
    create_source_profile,
    validate_source_profile,
)


class ApplySourceTests(unittest.TestCase):
    """Protect the source semantics established before Phase 3."""

    def setUp(self) -> None:
        self.config = create_default_config()

    def test_none_source_leaves_field_unchanged(self) -> None:
        config = replace(
            self.config,
            source=replace(
                self.config.source,
                kind="none",
            ),
        )
        field = np.arange(
            config.grid.nx * config.grid.ny,
            dtype=float,
        ).reshape(config.grid.shape)
        expected = field.copy()

        apply_source(
            field,
            step_index=7,
            config=config,
        )

        np.testing.assert_array_equal(field, expected)

    def test_point_sine_changes_only_the_configured_cell(self) -> None:
        config = replace(
            self.config,
            source=replace(
                self.config.source,
                x=20,
                y=30,
                amplitude=0.75,
                frequency=0.05,
            ),
        )
        field = np.zeros(config.grid.shape)
        step_index = 7

        apply_source(field, step_index, config)

        expected_value = (
            config.source.amplitude
            * np.sin(
                2.0
                * np.pi
                * config.source.frequency
                * step_index
                * config.time.dt
            )
        )

        self.assertAlmostEqual(
            field[config.source.x, config.source.y],
            expected_value,
        )
        self.assertEqual(
            np.count_nonzero(field),
            1,
        )

    def test_point_sine_is_added_instead_of_assigned(self) -> None:
        source = self.config.source
        field = np.zeros(self.config.grid.shape)
        field[source.x, source.y] = 3.0
        step_index = 4

        apply_source(
            field,
            step_index,
            self.config,
        )

        expected_source_value = (
            source.amplitude
            * np.sin(
                2.0
                * np.pi
                * source.frequency
                * step_index
                * self.config.time.dt
            )
        )

        self.assertAlmostEqual(
            field[source.x, source.y],
            3.0 + expected_source_value,
        )

    def test_point_sine_uses_the_next_step_time(self) -> None:
        field = np.zeros(self.config.grid.shape)
        step_index = 11

        apply_source(
            field,
            step_index,
            self.config,
        )

        source = self.config.source
        expected_time = step_index * self.config.time.dt
        expected_value = source.amplitude * np.sin(
            2.0 * np.pi * source.frequency * expected_time
        )

        self.assertAlmostEqual(
            field[source.x, source.y],
            expected_value,
        )

    def test_line_sine_updates_only_its_aperture(self) -> None:
        config = replace(
            self.config,
            source=replace(
                self.config.source,
                kind="line_sine",
                x=20,
                y_start=30,
                y_stop=40,
                amplitude=0.75,
                frequency=0.05,
            ),
        )
        field = np.zeros(config.grid.shape)
        step_index = 7

        apply_source(field, step_index, config)

        expected_value = (
            config.source.amplitude
            * np.sin(
                2.0
                * np.pi
                * config.source.frequency
                * step_index
                * config.time.dt
            )
        )

        np.testing.assert_allclose(
            field[20, 30:40],
            expected_value,
        )
        self.assertEqual(np.count_nonzero(field), 10)
        self.assertTrue(np.all(field[19, :] == 0.0))
        self.assertTrue(np.all(field[21, :] == 0.0))
        self.assertEqual(field[20, 29], 0.0)
        self.assertEqual(field[20, 40], 0.0)


class SourceOrderingTests(unittest.TestCase):
    """Verify that advance applies the source after the wave update."""

    def test_advance_applies_source_to_the_completed_next_field(self) -> None:
        config = create_default_config()
        simulation = Wave2DSimulation(config)
        stepped_field = np.full(config.grid.shape, 2.0)
        observed = {}

        def record_source_application(
            field: np.ndarray,
            step_index: int,
            supplied_config,
            source_profile: np.ndarray,
        ) -> None:
            observed["field"] = field
            observed["step_index"] = step_index
            observed["config"] = supplied_config
            observed["source_profile"] = source_profile
            field[config.source.x, config.source.y] += 5.0

        with (
            patch(
                "wavesim.solver.step_wave",
                return_value=stepped_field,
            ) as mocked_step,
            patch(
                "wavesim.solver.apply_source",
                side_effect=record_source_application,
            ) as mocked_source,
        ):
            simulation.advance()

        mocked_step.assert_called_once()
        mocked_source.assert_called_once()

        self.assertIs(
            observed["field"],
            stepped_field,
        )
        self.assertEqual(observed["step_index"], 1)
        self.assertIs(observed["config"], config)
        self.assertIs(
            observed["source_profile"],
            simulation.source_profile,
        )
        self.assertEqual(
            simulation.source_profile[
                config.source.x,
                config.source.y,
            ],
            1.0,
        )
        self.assertEqual(
            np.count_nonzero(simulation.source_profile),
            1,
        )
        self.assertIs(simulation.state.current, stepped_field)
        self.assertEqual(
            simulation.state.current[
                config.source.x,
                config.source.y,
            ],
            7.0,
        )

    def test_advance_reuses_the_precomputed_source_profile(self) -> None:
        simulation = Wave2DSimulation(create_default_config())
        original_profile = simulation.source_profile

        simulation.advance()
        simulation.advance()

        self.assertIs(simulation.source_profile, original_profile)


class SourceProfileTests(unittest.TestCase):
    """Verify construction and validation of spatial source profiles."""

    def setUp(self) -> None:
        self.config = create_default_config()

    def test_none_source_has_an_empty_profile(self) -> None:
        config = replace(
            self.config,
            source=replace(
                self.config.source,
                kind="none",
            ),
        )

        profile = create_source_profile(config)

        self.assertEqual(profile.shape, config.grid.shape)
        self.assertEqual(np.count_nonzero(profile), 0)
        self.assertFalse(profile.flags.writeable)

    def test_point_source_profile_has_one_unit_weight(self) -> None:
        profile = create_source_profile(self.config)
        source = self.config.source

        self.assertEqual(profile.shape, self.config.grid.shape)
        self.assertEqual(profile[source.x, source.y], 1.0)
        self.assertEqual(np.count_nonzero(profile), 1)
        self.assertFalse(profile.flags.writeable)

    def test_profile_shape_must_match_grid(self) -> None:
        profile = np.zeros((4, 5), dtype=float)

        with self.assertRaisesRegex(
            ValueError,
            "shape must match",
        ):
            validate_source_profile(
                profile,
                self.config.grid,
                active=False,
            )

    def test_active_profile_cannot_be_empty(self) -> None:
        profile = np.zeros(self.config.grid.shape, dtype=float)

        with self.assertRaisesRegex(
            ValueError,
            "at least one nonzero",
        ):
            validate_source_profile(
                profile,
                self.config.grid,
                active=True,
            )

    def test_profile_cannot_touch_the_boundary(self) -> None:
        profile = np.zeros(self.config.grid.shape, dtype=float)
        profile[0, 10] = 1.0

        with self.assertRaisesRegex(
            ValueError,
            "zero on the domain boundary",
        ):
            validate_source_profile(
                profile,
                self.config.grid,
                active=True,
            )

    def test_profile_values_must_be_finite(self) -> None:
        profile = np.zeros(self.config.grid.shape, dtype=float)
        profile[10, 10] = np.nan

        with self.assertRaisesRegex(
            ValueError,
            "must be finite",
        ):
            validate_source_profile(
                profile,
                self.config.grid,
                active=True,
            )

    def test_line_source_profile_uses_half_open_bounds(self) -> None:
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

        profile = create_source_profile(config)

        expected = np.zeros(config.grid.shape)
        expected[20, 30:40] = 1.0

        np.testing.assert_array_equal(profile, expected)
        self.assertEqual(np.count_nonzero(profile), 10)
        self.assertFalse(profile.flags.writeable)


class SourceEnvelopeTests(unittest.TestCase):
    """Verify smooth and backward-compatible source turn-on."""

    def setUp(self) -> None:
        self.config = create_default_config()

    def test_zero_ramp_cycles_returns_unit_envelope(self) -> None:
        for step_index in (0, 1, 10, 500):
            with self.subTest(step_index=step_index):
                self.assertEqual(
                    compute_source_envelope(
                        step_index,
                        self.config,
                    ),
                    1.0,
                )

    def test_ramp_starts_at_zero(self) -> None:
        config = replace(
            self.config,
            source=replace(
                self.config.source,
                ramp_cycles=2.0,
            ),
        )

        self.assertEqual(
            compute_source_envelope(0, config),
            0.0,
        )

    def test_ramp_matches_sine_squared_definition(self) -> None:
        config = replace(
            self.config,
            source=replace(
                self.config.source,
                frequency=0.05,
                ramp_cycles=2.0,
            ),
        )

        # Ramp duration = 2 / 0.05 = 40 time units.
        # dt = 0.4, so step 50 corresponds to t = 20:
        # exactly halfway through the ramp.
        envelope = compute_source_envelope(50, config)

        self.assertAlmostEqual(envelope, 0.5)

    def test_ramp_reaches_and_remains_at_one(self) -> None:
        config = replace(
            self.config,
            source=replace(
                self.config.source,
                frequency=0.05,
                ramp_cycles=2.0,
            ),
        )

        # Ramp duration is 40 and dt is 0.4, so it ends at step 100.
        self.assertEqual(
            compute_source_envelope(100, config),
            1.0,
        )
        self.assertEqual(
            compute_source_envelope(150, config),
            1.0,
        )


class LineSourceConfigTests(unittest.TestCase):
    """Verify line-source configuration validation."""

    def setUp(self) -> None:
        self.config = create_default_config()

    def create_line_config(self, **changes):
        source_values = {
            "kind": "line_sine",
            "x": 20,
            "y_start": 30,
            "y_stop": 40,
        }
        source_values.update(changes)

        return replace(
            self.config,
            source=replace(
                self.config.source,
                **source_values,
            ),
        )

    def test_valid_line_source_is_accepted(self) -> None:
        validate_config(self.create_line_config())

    def test_line_source_requires_both_bounds(self) -> None:
        for changes in (
            {"y_start": None},
            {"y_stop": None},
        ):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(
                    ValueError,
                    "require y_start and y_stop",
                ):
                    validate_config(
                        self.create_line_config(**changes)
                    )

    def test_line_source_rejects_invalid_bounds(self) -> None:
        for changes in (
            {"y_start": 0},
            {"y_start": 40, "y_stop": 40},
            {"y_start": 50, "y_stop": 40},
            {"y_stop": self.config.grid.ny},
        ):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(
                    ValueError,
                    "half-open interval",
                ):
                    validate_config(
                        self.create_line_config(**changes)
                    )

    def test_source_ramp_cycles_must_be_nonnegative(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "finite and nonnegative",
        ):
            validate_config(
                self.create_line_config(ramp_cycles=-1.0)
            )


if __name__ == "__main__":
    unittest.main()
