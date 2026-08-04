# 02 — Harmonic Response Analysis

## 1. Purpose of this note

The purpose of this note is to explain how the Photonics Simulator extracts a
steady single-frequency amplitude and phase from a recorded scalar-field
history.

Phase 3 introduces named field monitors. A monitor produces a sequence:

```math
u_0,u_1,u_2,\ldots,u_{N-1},
```

sampled at the simulation times:

```math
t_n=n\Delta t.
```

The harmonic-analysis problem is:

> Given a real sampled signal and a known source frequency, estimate the
> complex amplitude of the part of the signal oscillating at that frequency.

The implemented analysis is a single-frequency discrete lock-in or Fourier
projection. It does not calculate a complete spectrum.

The main concepts are:

- harmonic representation;
- complex amplitude;
- temporal sampling and Nyquist frequency;
- half-open analysis windows;
- mean removal;
- amplitude normalization;
- phase convention;
- phase wrapping;
- integer-cycle windows and spectral leakage;
- propagation phase;
- finite-difference numerical dispersion.

---

## 2. Real harmonic signals

A real cosine with amplitude `A`, frequency `f`, and phase `phi` is:

```math
u(t)
=
A\cos(2\pi ft+\phi).
```

It is convenient to define the angular frequency:

```math
\omega=2\pi f.
```

Then:

```math
u(t)=A\cos(\omega t+\phi).
```

Using Euler's identity:

```math
e^{i\theta}=\cos\theta+i\sin\theta,
```

the real signal can be written as:

```math
u(t)
=
\operatorname{Re}
\left[
Ae^{i\phi}e^{i\omega t}
\right].
```

The complex quantity:

```math
\tilde u=Ae^{i\phi}
```

is the complex harmonic amplitude.

Its magnitude gives the ordinary amplitude:

```math
A=|\tilde u|,
```

and its argument gives the phase:

```math
\phi=\arg(\tilde u).
```

One complex number therefore stores both amplitude and phase.

---

## 3. Discrete temporal samples

The simulator records a monitor after each completed time step.

The sample times are:

```math
t_n=n\Delta t.
```

For a harmonic signal, the discrete samples are:

```math
u_n
=
A\cos(2\pi f n\Delta t+\phi).
```

The analysis assumes uniform temporal spacing. It reconstructs the sample
times from the step indices and configured `dt` rather than from wall-clock
time.

### 3.1 Temporal Nyquist limit

The temporal sampling frequency is:

```math
f_s=\frac{1}{\Delta t}.
```

The Nyquist frequency is:

```math
f_{\mathrm{Nyquist}}
=
\frac{f_s}{2}
=
\frac{1}{2\Delta t}.
```

The analyzed frequency must satisfy:

```math
0<f<f_{\mathrm{Nyquist}}.
```

A frequency at or above Nyquist cannot be represented uniquely by the sampled
history. The current implementation rejects it.

Temporal Nyquist validation is separate from spatial wavelength resolution.
A temporally valid frequency can still be poorly resolved by the spatial
grid.

---

## 4. Selecting an analysis window

The full simulation history normally contains:

- the initial zero field;
- the smooth source turn-on;
- propagation delay from the source to the monitor;
- broadband startup transients;
- a later approximately steady harmonic response;
- possible late boundary reflections.

Only an appropriate interval should be used for steady harmonic analysis.

The implementation selects samples using the half-open convention:

```python
samples[start_step:stop_step]
```

or mathematically:

```math
n_0\le n<n_1.
```

The sample count is:

```math
N=n_1-n_0.
```

The analysis duration is defined by the sampled intervals:

```math
T=N\Delta t.
```

The number of analyzed cycles is:

```math
N_{\mathrm{cycles}}
=
Tf
=
N\Delta t f.
```

The current default requires at least three cycles. Longer windows generally
improve frequency selectivity, but they also increase the chance of including
late boundary reflections or slow changes in the experiment.

---

## 5. Removing the mean

A recorded signal may contain a constant offset:

```math
u_n=u_{\mathrm{DC}}+u_{\mathrm{osc},n}.
```

Before projection, the implementation calculates:

```math
\bar u
=
\frac{1}{N}
\sum_{n=n_0}^{n_1-1}u_n
```

and forms the centered signal:

```math
u'_n=u_n-\bar u.
```

This prevents a constant background from contributing to the requested
harmonic through a finite analysis window.

Mean removal does not change the stored monitor history. It is performed only
on the selected analysis copy.

---

## 6. Single-frequency projection

The implemented complex response is:

```math
\tilde u(f)
=
\frac{2}{N}
\sum_{n=n_0}^{n_1-1}
u'_n
e^{-i2\pi ft_n}.
```

The exponential:

```math
e^{-i2\pi ft_n}
```

is the complex reference oscillator. Multiplying by it shifts the requested
frequency toward zero phase. Summing reinforces signal content at that
frequency while content with different phase evolution tends to cancel.

### 6.1 Why the factor is `2/N`

A real cosine contains equal positive- and negative-frequency components:

```math
A\cos(\omega t+\phi)
=
\frac{A}{2}e^{i(\omega t+\phi)}
+
\frac{A}{2}e^{-i(\omega t+\phi)}.
```

Projection onto the positive-frequency component produces approximately
`A/2`. Multiplication by `2` restores the real sinusoid amplitude. Division by
`N` normalizes the sum by the number of samples.

For a window containing an integer number of cycles and a signal exactly at
the analysis frequency:

```math
u_n=A\cos(2\pi ft_n+\phi)
```

the estimator returns:

```math
\tilde u(f)=Ae^{i\phi}
```

up to floating-point rounding.

---

## 7. Phase convention

The project uses a cosine reference convention:

```math
A\cos(2\pi ft+\phi)
\quad\Longrightarrow\quad
\tilde u=Ae^{i\phi}.
```

The configured source uses a sine:

```math
s(t)=A\sin(2\pi ft).
```

Because:

```math
\sin\theta
=
\cos\left(\theta-\frac{\pi}{2}\right),
```

an ideal sine has phase:

```math
\phi=-\frac{\pi}{2}
```

under the implemented convention.

The absolute phase of a propagated signal includes:

- the source convention;
- source-to-monitor propagation;
- material interfaces;
- numerical dispersion;
- the global reference time.

For many measurements, a phase difference or complex ratio is more useful
than either absolute phase.

---

## 8. Phase wrapping

The complex argument is normally reported on the principal interval:

```math
-\pi<\phi\le\pi.
```

Phases that differ by an integer multiple of `2*pi` represent the same complex
direction:

```math
\phi
\equiv
\phi+2\pi m,
\qquad m\in\mathbb Z.
```

A direct subtraction can therefore report an artificially large error near
the branch cut. The wrapped difference between a measured and expected phase
is calculated as:

```math
\Delta\phi_{\mathrm{wrapped}}
=
\arg
\left[
e^{i(\phi_{\mathrm{measured}}-\phi_{\mathrm{expected}})}
\right].
```

In NumPy:

```python
phase_error = np.angle(
    np.exp(
        1.0j * (measured_phase - expected_phase)
    )
)
```

A stable phase difference can also be obtained directly from two complex
responses:

```python
phase_difference = np.angle(
    second.complex_amplitude
    / first.complex_amplitude
)
```

---

## 9. Integer-cycle windows and spectral leakage

The single-frequency projection is exact for an ideal sampled sinusoid when
the analysis window contains an integer number of cycles and the frequency is
represented consistently.

If the window cuts through a noninteger number of cycles, the endpoints do not
join at the same phase. The finite rectangular window then spreads signal
content into nearby frequencies. This is spectral leakage.

The Phase 3 scenarios deliberately use integer-cycle windows:

```text
Controlled uniform scenario
    250 samples
    dt = 0.4
    f = 0.05
    cycles = 250 * 0.4 * 0.05 = 5

Paired interface scenario
    150 samples
    dt = 0.4
    f = 0.05
    cycles = 150 * 0.4 * 0.05 = 3
```

The current estimator does not apply a Hann or other spectral window. Adding a
window function would require corresponding amplitude normalization and a
clear choice about the desired frequency resolution.

---

## 10. Propagation phase

A right-propagating harmonic plane wave can be represented as:

```math
u(x,t)
=
A\cos(\omega t-kx+\phi_0).
```

At two monitor positions `x1` and `x2`, the continuum phase difference is:

```math
\phi_2-\phi_1
=
-k(x_2-x_1).
```

For a nondispersive continuum medium:

```math
k=\frac{\omega}{c}
=
\frac{2\pi f}{c}.
```

However, a finite-difference solver is numerically dispersive. The numerical
wave number generally differs from the continuum value.

---

## 11. Numerical dispersion relation

For a harmonic wave that is uniform in `y`, the centered second-order scheme
obeys:

```math
\sin^2\left(\frac{\omega\Delta t}{2}\right)
=
\left(\frac{c\Delta t}{\Delta x}\right)^2
\sin^2\left(\frac{k_h\Delta x}{2}\right).
```

Solving for the numerical wave number gives:

```math
k_h
=
\frac{2}{\Delta x}
\arcsin
\left[
\frac{
\sin(\omega\Delta t/2)
}{
c\Delta t/\Delta x
}
\right].
```

The expected numerical phase advance between two monitors is:

```math
\Delta\phi_h
=
-k_h\Delta x_{\mathrm{monitor}}.
```

Phase 3 validates the controlled uniform scenario against this discrete
relation. Comparing with the discrete prediction distinguishes ordinary
finite-difference dispersion from a source, monitor, or time-indexing bug.

---

## 12. Complex ratios for scattering analysis

If `incident`, `reflected`, and `transmitted` are complex harmonic responses,
field-amplitude ratios are:

```math
r=\frac{\tilde u_r}{\tilde u_i}
```

and:

```math
t=\frac{\tilde u_t}{\tilde u_i}.
```

The complex ratios retain amplitude and phase. Their magnitudes are:

```math
|r|,
\qquad
|t|,
```

while their arguments give relative phase shifts.

In the paired Phase 3 experiment, the downstream interface response is
normalized by a downstream reference response rather than by the upstream
incident response. This compensates partly for source strength and propagation
through the finite reference experiment.

Field-amplitude ratios are not automatically power or flux coefficients. The
physical flux relationship depends on the governing equation, propagation
direction, material, and measurement aperture.

---

## 13. Implementation mapping

The implementation is in:

```text
wavesim/analysis.py
```

The primary call is:

```python
response = estimate_harmonic_response(
    samples,
    dt,
    frequency,
    start_step=start_step,
    stop_step=stop_step,
)
```

The returned `HarmonicResponse` contains:

```text
complex_amplitude
frequency
start_step
stop_step
sample_count
duration
cycle_count
```

and calculated properties:

```text
amplitude
phase
```

The function accepts any one-dimensional scalar sequence. It does not depend
on `Wave2DSimulation` or `FieldMonitorState`.

This separation allows the same analysis to be used for:

- live monitor histories;
- synthetic validation signals;
- saved data in a future result format;
- compatible external scalar histories.

---

## 14. Validation contract

The harmonic-analysis tests verify:

1. Recovery of a known cosine amplitude.
2. Recovery of a known cosine phase.
3. The `-pi/2` phase of a sine under the cosine convention.
4. Invariance to a constant offset.
5. Correct analysis metadata.
6. Default use of the remaining history after `start_step`.
7. Rejection of multidimensional samples.
8. Rejection of empty or non-finite samples.
9. Rejection of invalid `dt` or frequency.
10. Rejection of frequencies at or above Nyquist.
11. Rejection of invalid half-open bounds.
12. Rejection of windows containing too few cycles.

The controlled propagation scenario additionally validates measured phase
advance against the finite-difference dispersion relation.

---

## 15. Limitations

The current single-frequency estimator assumes:

- uniform temporal sample spacing;
- a known target frequency;
- a sufficiently steady response inside the selected window;
- a finite one-dimensional scalar history;
- enough cycles for a meaningful estimate.

It does not currently provide:

- a broadband spectrum;
- automatic steady-state detection;
- automatic arrival-time detection;
- phase unwrapping over many monitors;
- spectral window functions;
- uncertainty estimates;
- confidence intervals;
- direct power or energy-flux calculation.

These are future analysis features rather than hidden properties of the
current estimator.

---

## 16. Summary

Phase 3 estimates a harmonic response by projecting a mean-centered scalar
history onto a complex reference oscillator:

```math
\tilde u(f)
=
\frac{2}{N}
\sum_n
(u_n-\bar u)e^{-i2\pi ft_n}.
```

The result stores amplitude and phase in one complex number. Analysis windows
use half-open bounds and are chosen after the source ramp and propagation
transient. Integer-cycle windows reduce leakage. Phase differences are wrapped
through complex arguments, and propagation is compared with the numerical
rather than ideal continuum dispersion relation.

This analysis provides the mathematical bridge between recorded field-monitor
histories and the controlled propagation and scattering measurements used in
Phase 3.
