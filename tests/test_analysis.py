"""Tests for scalar harmonic-response analysis."""

import unittest

import numpy as np

from wavesim.analysis import estimate_harmonic_response


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