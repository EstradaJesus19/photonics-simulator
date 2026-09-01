"""Frequency-domain analysis of scalar simulation histories."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HarmonicResponse:
    """Complex response measured at one temporal frequency."""

    complex_amplitude: complex
    frequency: float
    start_step: int
    stop_step: int
    sample_count: int
    duration: float
    cycle_count: float

    @property
    def amplitude(self) -> float:
        """Return the magnitude of the complex response."""
        return float(abs(self.complex_amplitude))

    @property
    def phase(self) -> float:
        """Return the response phase in radians."""
        return float(np.angle(self.complex_amplitude))


def estimate_harmonic_response(
    samples,
    dt: float,
    frequency: float,
    *,
    start_step: int = 0,
    stop_step: int | None = None,
    minimum_cycles: float = 3.0,
) -> HarmonicResponse:
    """Estimate one complex harmonic response from scalar samples."""
    sample_array = np.asarray(samples, dtype=float)

    if sample_array.ndim != 1:
        raise ValueError("samples must be one-dimensional.")

    if sample_array.size == 0:
        raise ValueError("samples cannot be empty.")

    if not np.all(np.isfinite(sample_array)):
        raise ValueError("samples must contain only finite values.")

    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive.")

    if not np.isfinite(frequency) or frequency <= 0:
        raise ValueError(
            "frequency must be finite and positive."
        )

    nyquist_frequency = 1.0 / (2.0 * dt)

    if frequency >= nyquist_frequency:
        raise ValueError(
            "frequency must be below the temporal Nyquist frequency."
        )

    if (
        not isinstance(start_step, (int, np.integer))
        or isinstance(start_step, (bool, np.bool_))
    ):
        raise TypeError("start_step must be an integer.")

    selected_stop = (
        sample_array.size
        if stop_step is None
        else stop_step
    )

    if (
        not isinstance(selected_stop, (int, np.integer))
        or isinstance(selected_stop, (bool, np.bool_))
    ):
        raise TypeError("stop_step must be an integer.")

    if not (0 <= start_step < selected_stop <= sample_array.size):
        raise ValueError(
            "Analysis bounds must define a nonempty half-open "
            "interval inside the sample history."
        )

    if (
        not np.isfinite(minimum_cycles)
        or minimum_cycles <= 0
    ):
        raise ValueError(
            "minimum_cycles must be finite and positive."
        )

    window = sample_array[start_step:selected_stop]
    sample_count = window.size
    duration = sample_count * dt
    cycle_count = duration * frequency

    if cycle_count < minimum_cycles:
        raise ValueError(
            "Analysis window must contain at least "
            f"{minimum_cycles:g} source cycles."
        )

    step_indices = np.arange(
        start_step,
        selected_stop,
        dtype=float,
    )
    times = step_indices * dt

    centered_window = window - np.mean(window)

    phasor = np.exp(
        -2.0j * np.pi * frequency * times
    )

    complex_amplitude = (
        2.0
        / sample_count
        * np.sum(centered_window * phasor)
    )

    return HarmonicResponse(
        complex_amplitude=complex(complex_amplitude),
        frequency=float(frequency),
        start_step=int(start_step),
        stop_step=int(selected_stop),
        sample_count=int(sample_count),
        duration=float(duration),
        cycle_count=float(cycle_count),
    )


@dataclass(frozen=True)
class AveragePower:
    """Time-windowed average of signed scalar-wave power."""

    mean_power: float
    start_step: int
    stop_step: int
    sample_count: int
    duration: float
    frequency: float | None
    cycle_count: float | None

    @property
    def transported_energy(self) -> float:
        """Return signed energy transported during the window."""
        return self.mean_power * self.duration


def estimate_average_power(
    samples,
    dt: float,
    *,
    start_step: int = 0,
    stop_step: int | None = None,
    frequency: float | None = None,
    minimum_cycles: float | None = None,
) -> AveragePower:
    """Average signed power over one half-open sample window."""
    sample_array = np.asarray(samples, dtype=float)

    if sample_array.ndim != 1:
        raise ValueError(
            "Power samples must be one-dimensional."
        )

    if sample_array.size == 0:
        raise ValueError("Power samples cannot be empty.")

    if not np.all(np.isfinite(sample_array)):
        raise ValueError(
            "Power samples must contain only finite values."
        )

    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive.")

    if (
        not isinstance(start_step, (int, np.integer))
        or isinstance(start_step, (bool, np.bool_))
    ):
        raise TypeError("start_step must be an integer.")

    selected_stop = (
        sample_array.size
        if stop_step is None
        else stop_step
    )

    if (
        not isinstance(selected_stop, (int, np.integer))
        or isinstance(selected_stop, (bool, np.bool_))
    ):
        raise TypeError("stop_step must be an integer.")

    if not (
        0
        <= start_step
        < selected_stop
        <= sample_array.size
    ):
        raise ValueError(
            "Analysis bounds must define a nonempty "
            "half-open interval inside the power history."
        )

    if frequency is None:
        if minimum_cycles is not None:
            raise ValueError(
                "minimum_cycles requires a frequency."
            )

        selected_frequency = None
        cycle_count = None

    else:
        if not np.isfinite(frequency) or frequency <= 0:
            raise ValueError(
                "frequency must be finite and positive."
            )

        nyquist_frequency = 1.0 / (2.0 * dt)

        if frequency >= nyquist_frequency:
            raise ValueError(
                "frequency must be below the temporal "
                "Nyquist frequency."
            )

        selected_frequency = float(frequency)

    if minimum_cycles is not None:
        if (
            not np.isfinite(minimum_cycles)
            or minimum_cycles <= 0
        ):
            raise ValueError(
                "minimum_cycles must be finite and positive."
            )

    window = sample_array[start_step:selected_stop]
    sample_count = window.size
    duration = sample_count * dt

    if selected_frequency is not None:
        cycle_count = duration * selected_frequency

        if (
            minimum_cycles is not None
            and cycle_count < minimum_cycles
        ):
            raise ValueError(
                "Analysis window must contain at least "
                f"{minimum_cycles:g} source cycles."
            )

    mean_power = float(np.mean(window))

    return AveragePower(
        mean_power=mean_power,
        start_step=int(start_step),
        stop_step=int(selected_stop),
        sample_count=int(sample_count),
        duration=float(duration),
        frequency=selected_frequency,
        cycle_count=(
            None
            if cycle_count is None
            else float(cycle_count)
        ),
    )