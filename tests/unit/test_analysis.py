"""Tests for scalar harmonic-response analysis."""

import unittest

import numpy as np

from wavesim.analysis import (
    estimate_average_power,
    estimate_harmonic_response,
)


class HarmonicResponseTests(unittest.TestCase):
    """Verify amplitude and phase estimation."""

    def setUp(self) -> None:
        self.dt = 0.05
        self.frequency = 0.5

        # The signal period is 2 time units or 40 samples.
        # 400 samples therefore contain exactly 10 cycles.
        self.sample_count = 400
        self.times = np.arange(self.sample_count) * self.dt

    def create_signal(
        self,
        amplitude: float,
        phase: float,
        offset: float = 0.0,
    ) -> np.ndarray:
        return (
            offset
            + amplitude
            * np.cos(
                2.0
                * np.pi
                * self.frequency
                * self.times
                + phase
            )
        )

    def test_recovers_known_amplitude(self) -> None:
        samples = self.create_signal(
            amplitude=2.5,
            phase=0.0,
        )

        response = estimate_harmonic_response(
            samples,
            self.dt,
            self.frequency,
        )

        self.assertAlmostEqual(response.amplitude, 2.5, places=12)

    def test_recovers_known_phase(self) -> None:
        expected_phase = 0.7
        samples = self.create_signal(
            amplitude=2.5,
            phase=expected_phase,
        )

        response = estimate_harmonic_response(
            samples,
            self.dt,
            self.frequency,
        )

        self.assertAlmostEqual(
            response.phase,
            expected_phase,
            places=12,
        )

    def test_constant_offset_does_not_change_response(self) -> None:
        without_offset = self.create_signal(
            amplitude=1.75,
            phase=-0.4,
        )
        with_offset = self.create_signal(
            amplitude=1.75,
            phase=-0.4,
            offset=12.0,
        )

        first = estimate_harmonic_response(
            without_offset,
            self.dt,
            self.frequency,
        )
        second = estimate_harmonic_response(
            with_offset,
            self.dt,
            self.frequency,
        )

        self.assertAlmostEqual(
            first.complex_amplitude.real,
            second.complex_amplitude.real,
            places=12,
        )
        self.assertAlmostEqual(
            first.complex_amplitude.imag,
            second.complex_amplitude.imag,
            places=12,
        )

    def test_reports_analysis_metadata(self) -> None:
        samples = self.create_signal(
            amplitude=1.0,
            phase=0.0,
        )

        response = estimate_harmonic_response(
            samples,
            self.dt,
            self.frequency,
            start_step=80,
            stop_step=320,
        )

        self.assertEqual(response.start_step, 80)
        self.assertEqual(response.stop_step, 320)
        self.assertEqual(response.sample_count, 240)
        self.assertAlmostEqual(response.duration, 12.0)
        self.assertAlmostEqual(response.cycle_count, 6.0)

    def test_stop_step_defaults_to_history_length(self) -> None:
        samples = self.create_signal(
            amplitude=1.0,
            phase=0.0,
        )

        response = estimate_harmonic_response(
            samples,
            self.dt,
            self.frequency,
            start_step=80,
        )

        self.assertEqual(response.stop_step, len(samples))
        self.assertEqual(response.sample_count, 320)

    def test_sine_signal_has_negative_half_pi_phase(self) -> None:
        samples = 2.0 * np.sin(
            2.0
            * np.pi
            * self.frequency
            * self.times
        )

        response = estimate_harmonic_response(
            samples,
            self.dt,
            self.frequency,
        )

        self.assertAlmostEqual(response.amplitude, 2.0, places=12)
        self.assertAlmostEqual(
            response.phase,
            -0.5 * np.pi,
            places=12,
        )


class HarmonicResponseValidationTests(unittest.TestCase):
    """Verify invalid analysis inputs are rejected."""

    def test_samples_must_be_one_dimensional(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "one-dimensional",
        ):
            estimate_harmonic_response(
                np.zeros((10, 10)),
                dt=0.1,
                frequency=0.5,
            )

    def test_samples_must_be_finite(self) -> None:
        samples = np.zeros(100)
        samples[50] = np.nan

        with self.assertRaisesRegex(
            ValueError,
            "finite",
        ):
            estimate_harmonic_response(
                samples,
                dt=0.1,
                frequency=0.5,
            )

    def test_frequency_must_be_below_nyquist(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Nyquist",
        ):
            estimate_harmonic_response(
                np.zeros(100),
                dt=0.1,
                frequency=5.0,
            )

    def test_bounds_must_be_valid(self) -> None:
        samples = np.zeros(100)

        for start_step, stop_step in (
            (-1, 50),
            (50, 50),
            (60, 50),
            (0, 101),
        ):
            with self.subTest(
                start_step=start_step,
                stop_step=stop_step,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "half-open interval",
                ):
                    estimate_harmonic_response(
                        samples,
                        dt=0.1,
                        frequency=0.5,
                        start_step=start_step,
                        stop_step=stop_step,
                    )

    def test_window_must_contain_enough_cycles(self) -> None:
        samples = np.zeros(100)

        # 20 samples × 0.1 = 2 time units.
        # At 0.5 Hz, this contains only one cycle.
        with self.assertRaisesRegex(
            ValueError,
            "at least 3 source cycles",
        ):
            estimate_harmonic_response(
                samples,
                dt=0.1,
                frequency=0.5,
                start_step=0,
                stop_step=20,
            )


class AveragePowerTests(unittest.TestCase):
    """Verify signed time-windowed power averaging."""

    def test_constant_power_is_preserved(self) -> None:
        result = estimate_average_power(
            np.full(100, 4.5),
            dt=0.1,
        )

        self.assertEqual(result.mean_power, 4.5)
        self.assertEqual(result.sample_count, 100)
        self.assertAlmostEqual(result.duration, 10.0)
        self.assertAlmostEqual(
            result.transported_energy,
            45.0,
        )

    def test_negative_power_remains_negative(self) -> None:
        result = estimate_average_power(
            [-2.0, -4.0, -6.0],
            dt=0.5,
        )

        self.assertEqual(result.mean_power, -4.0)
        self.assertEqual(
            result.transported_energy,
            -6.0,
        )

    def test_selected_window_is_used(self) -> None:
        samples = np.array(
            [100.0, 100.0, 1.0, 2.0, 3.0, 100.0]
        )

        result = estimate_average_power(
            samples,
            dt=0.25,
            start_step=2,
            stop_step=5,
        )

        self.assertEqual(result.mean_power, 2.0)
        self.assertEqual(result.start_step, 2)
        self.assertEqual(result.stop_step, 5)
        self.assertEqual(result.sample_count, 3)
        self.assertAlmostEqual(result.duration, 0.75)

    def test_integer_cycle_window_recovers_power_offset(
        self,
    ) -> None:
        dt = 0.05
        frequency = 0.5
        times = np.arange(400) * dt

        samples = (
            3.0
            + 2.0
            * np.cos(
                2.0 * np.pi * frequency * times
            )
        )

        result = estimate_average_power(
            samples,
            dt,
            frequency=frequency,
            minimum_cycles=3.0,
        )

        self.assertAlmostEqual(
            result.mean_power,
            3.0,
            places=12,
        )
        self.assertAlmostEqual(
            result.cycle_count,
            10.0,
        )


class AveragePowerValidationTests(unittest.TestCase):
    """Verify rejection of invalid power-analysis inputs."""

    def test_samples_must_be_one_dimensional_and_nonempty(self) -> None:
        for samples in (np.zeros((2, 2)), np.array([])):
            with self.subTest(shape=samples.shape):
                with self.assertRaises(ValueError):
                    estimate_average_power(samples, dt=0.1)

    def test_samples_must_be_finite(self) -> None:
        for invalid_value in (np.nan, np.inf):
            samples = np.zeros(10)
            samples[3] = invalid_value

            with self.subTest(invalid_value=invalid_value):
                with self.assertRaisesRegex(ValueError, "finite"):
                    estimate_average_power(samples, dt=0.1)

    def test_dt_must_be_finite_and_positive(self) -> None:
        for invalid_dt in (0.0, -0.1, np.nan, np.inf):
            with self.subTest(invalid_dt=invalid_dt):
                with self.assertRaisesRegex(ValueError, "dt"):
                    estimate_average_power(np.zeros(10), invalid_dt)

    def test_bounds_must_be_integers(self) -> None:
        for arguments in (
            {"start_step": 1.5},
            {"start_step": True},
            {"stop_step": 5.5},
            {"stop_step": False},
        ):
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(TypeError, "integer"):
                    estimate_average_power(
                        np.zeros(10),
                        dt=0.1,
                        **arguments,
                    )

    def test_bounds_must_define_nonempty_window(self) -> None:
        for start_step, stop_step in (
            (-1, 5),
            (5, 5),
            (6, 5),
            (0, 11),
        ):
            with self.subTest(
                start_step=start_step,
                stop_step=stop_step,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "half-open interval",
                ):
                    estimate_average_power(
                        np.zeros(10),
                        dt=0.1,
                        start_step=start_step,
                        stop_step=stop_step,
                    )

    def test_frequency_must_be_valid_and_below_nyquist(self) -> None:
        for frequency in (0.0, -1.0, np.nan, np.inf, 5.0):
            with self.subTest(frequency=frequency):
                with self.assertRaises(ValueError):
                    estimate_average_power(
                        np.zeros(100),
                        dt=0.1,
                        frequency=frequency,
                    )

    def test_minimum_cycles_requires_frequency(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires a frequency"):
            estimate_average_power(
                np.zeros(100),
                dt=0.1,
                minimum_cycles=3.0,
            )

    def test_minimum_cycles_must_be_finite_and_positive(self) -> None:
        for minimum_cycles in (0.0, -1.0, np.nan, np.inf):
            with self.subTest(minimum_cycles=minimum_cycles):
                with self.assertRaisesRegex(ValueError, "minimum_cycles"):
                    estimate_average_power(
                        np.zeros(100),
                        dt=0.1,
                        frequency=0.5,
                        minimum_cycles=minimum_cycles,
                    )

    def test_window_must_contain_requested_cycles(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 3"):
            estimate_average_power(
                np.zeros(20),
                dt=0.1,
                frequency=0.5,
                minimum_cycles=3.0,
            )
