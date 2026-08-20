# 02 — Harmonic Response Analysis

> **Status:** Current technical reference through Phase 3.
>
> **Scope:** Single-frequency analysis of monitor histories, including
> controlled propagation and paired interface measurements.

## 1. Purpose of this note

The purpose of this note is to explain how the Photonics Simulator extracts a steady single-frequency amplitude and phase from a recorded scalar-field history.

Phase 3 introduces named field monitors. A monitor produces a sequence

```math
u_0,u_1,u_2,\ldots,u_{N-1},
```

sampled at the simulation times

```math
t_n=n\Delta t.
```

The harmonic-analysis problem is:

> Given a real sampled signal and a known source frequency, estimate the complex amplitude of the part of the signal oscillating at that frequency.

The implemented analysis is a **single-frequency discrete lock-in or Fourier projection**. It does not calculate a complete frequency spectrum.

The main concepts are:

* harmonic representation;
* complex amplitude;
* temporal sampling and Nyquist frequency;
* half-open analysis windows;
* mean removal;
* single-frequency projection;
* amplitude normalization;
* phase convention;
* phase wrapping;
* integer-cycle windows and spectral leakage;
* propagation phase;
* finite-difference numerical dispersion;
* complex ratios for propagation and scattering measurements.

---

## 2. Real harmonic signals

A real cosine with amplitude (A), frequency (f), and phase (\phi) is

```math
u(t)
=
A\cos(2\pi ft+\phi).
```

It is convenient to define the angular frequency

```math
\omega=2\pi f.
```

Then

```math
u(t)=A\cos(\omega t+\phi).
```

Using Euler's identity,

```math
e^{i\theta}
=
\cos\theta+i\sin\theta,
```

the real signal can be written as

```math
u(t)
=
\operatorname{Re}
\left[
Ae^{i\phi}e^{i\omega t}
\right].
```

The complex quantity

```math
\tilde u
=
Ae^{i\phi}
```

is the **complex harmonic amplitude**.

Its magnitude gives the ordinary amplitude,

```math
A=|\tilde u|,
```

while its argument gives the phase,

```math
\phi=\arg(\tilde u).
```

One complex number therefore stores both the amplitude and phase of a harmonic response.

This representation becomes particularly useful for propagation problems because amplitude changes and phase shifts can be compared using ordinary operations on complex numbers.

---

## 3. Discrete temporal samples

The simulator records a monitor after each completed time step.

The sample times are

```math
t_n=n\Delta t.
```

For a harmonic signal, the discrete samples are therefore

```math
u_n
=
A\cos(2\pi f n\Delta t+\phi).
```

The analysis assumes uniform temporal spacing. It reconstructs the sample times from the step indices and configured `dt` rather than from wall-clock time.

### 3.1 Temporal Nyquist limit

The temporal sampling frequency is

```math
f_s
=
\frac{1}{\Delta t}.
```

The Nyquist frequency is

```math
f_{\mathrm{Nyquist}}
=
\frac{f_s}{2}
=
\frac{1}{2\Delta t}.
```

The analyzed frequency must satisfy

```math
0<f<f_{\mathrm{Nyquist}}.
```

A frequency at or above the Nyquist frequency cannot be represented uniquely by the sampled history. The current implementation therefore rejects it.

Temporal Nyquist validation is separate from spatial wavelength resolution. A frequency may be perfectly valid in time while still being poorly resolved by the spatial finite-difference grid.

---

## 4. Selecting an analysis window

The complete simulation history normally contains several stages:

* the initial zero field;
* the smooth source turn-on;
* propagation delay from the source to the monitor;
* broadband startup transients;
* a later approximately steady harmonic response;
* possible late boundary reflections.

Only an appropriate interval should be used for steady harmonic analysis.

The implementation selects samples using the half-open convention

```python
samples[start_step:stop_step]
```

or mathematically,

```math
n_0\le n<n_1.
```

The sample count is

```math
N=n_1-n_0.
```

The analysis duration is

```math
T=N\Delta t.
```

Here, $T$ is the effective window duration used by the implementation for
cycle-count validation. Because the samples are indexed from $0$ through
$N-1$, the elapsed time between the first and last sample is
$(N-1)\Delta t$.

The number of analyzed cycles is therefore

```math
N_{\mathrm{cycles}}
=
Tf
=
N\Delta t f.
```

The current default requires at least three cycles.

Longer windows generally improve frequency selectivity and averaging. However, they also increase the chance of including late reflections or other changes that no longer belong to the desired steady-state response.

---

## 5. Removing the mean

A recorded signal may contain a constant offset:

```math
u_n
=
u_{\mathrm{DC}}
+
u_{\mathrm{osc},n}.
```

Before performing the harmonic projection, the implementation calculates the sample mean

```math
\bar u
=
\frac{1}{N}
\sum_{n=n_0}^{n_1-1}u_n
```

and forms the centered signal

```math
u'_n=u_n-\bar u.
```

This removes the zero-frequency or DC component from the selected analysis window.

Although an ideal constant signal is not part of the requested harmonic frequency, a finite analysis interval can allow some of this background to influence the projection. Mean removal reduces this effect.

The original monitor history is not modified. Mean removal is performed only on the copy used for harmonic analysis.

---

## 6. Single-frequency projection

The implemented complex response is

```math
\tilde u(f)
=
\frac{2}{N}
\sum_{n=n_0}^{n_1-1}
u'_n
e^{-i2\pi ft_n}.
```

This expression can be understood as asking:

> How much of the recorded signal oscillates exactly at the frequency (f), and what is the phase of that oscillation?

It is closely related to the Discrete Fourier Transform (DFT), but instead of calculating many frequencies, the simulator evaluates only the frequency of interest.

### 6.1 The complex reference oscillator

The factor

```math
e^{-i2\pi ft_n}
```

acts as a complex reference oscillator at the requested frequency.

To understand its role, suppose the recorded signal contains exactly

```math
u(t)
=
A\cos(2\pi ft+\phi).
```

Using the exponential representation of a cosine,

```math
u(t)
=
\frac{A}{2}
e^{i(2\pi ft+\phi)}
+
\frac{A}{2}
e^{-i(2\pi ft+\phi)}.
```

Multiplying by the reference oscillator gives

```math
u(t)e^{-i2\pi ft}
=
\frac{A}{2}e^{i\phi}
+
\frac{A}{2}e^{-i(4\pi ft+\phi)}.
```

The first term no longer oscillates in time:

```math
\frac{A}{2}e^{i\phi}.
```

It has been shifted from frequency (f) to **zero frequency**, or DC.

The second term continues to oscillate, now at frequency (2f).

When many samples are summed or averaged, the constant term accumulates coherently while the oscillating term tends to cancel.

The projection therefore isolates the part of the signal that evolves with the same frequency as the reference oscillator.

This is the same basic principle used by a lock-in amplifier.

### 6.2 Why the factor is `2/N`

For the ideal cosine above, averaging the projected signal gives approximately

```math
\frac{1}{N}
\sum_n
u_n e^{-i2\pi ft_n}
\approx
\frac{A}{2}e^{i\phi}.
```

The factor (1/N) converts the sum into an average.

The additional factor of (2) compensates for the fact that a real cosine contains equal positive- and negative-frequency components:

```math
A\cos(\omega t+\phi)
=
\frac{A}{2}e^{i(\omega t+\phi)}
+
\frac{A}{2}e^{-i(\omega t+\phi)}.
```

The positive-frequency component therefore contains only half of the real sinusoid amplitude.

For a window containing an integer number of cycles and a signal exactly at the analysis frequency,

```math
u_n
=
A\cos(2\pi ft_n+\phi),
```

the estimator returns

```math
\tilde u(f)
=
Ae^{i\phi}
```

up to floating-point and discretization effects.

Consequently,

```math
|\tilde u(f)|
\approx A
```

and

```math
\arg\left[\tilde u(f)\right]
\approx\phi.
```

### 6.3 Application to a field monitor

For a single monitor, the projection converts a real time history

```math
u_0,u_1,\ldots,u_{N-1}
```

into one complex number

```math
\tilde u(f).
```

Instead of storing how the field oscillates at every instant, the complex response summarizes the steady harmonic behavior at the selected frequency.

If the same operation is performed at several monitor positions, their complex amplitudes can be compared to study propagation, phase accumulation, reflection, and transmission.

---

## 7. Phase convention

The project uses a cosine reference convention:

```math
A\cos(2\pi ft+\phi)
\quad\Longrightarrow\quad
\tilde u=Ae^{i\phi}.
```

The configured source instead uses a sine:

```math
s(t)
=
A\sin(2\pi ft).
```

Because

```math
\sin\theta
=
\cos\left(
\theta-\frac{\pi}{2}
\right),
```

an ideal sine has phase

```math
\phi
=
-\frac{\pi}{2}
```

under the implemented cosine convention.

The absolute phase observed at a monitor generally contains contributions from several effects:

* the source phase convention;
* the global reference time;
* propagation from the source to the monitor;
* material interfaces;
* reflections and interference;
* numerical dispersion.

For this reason, phase **differences** and complex **ratios** are often more useful than the absolute phase measured at a single point.

---

## 8. Phase wrapping

The phase of a complex number is periodic.

For example,

```math
30^\circ,
\qquad
390^\circ,
\qquad
-330^\circ
```

all describe the same direction in the complex plane because they differ by integer multiples of (360^\circ), or (2\pi).

In general,

```math
\phi
\equiv
\phi+2\pi m,
\qquad
m\in\mathbb Z.
```

A computer nevertheless needs to choose one numerical representation. `np.angle()` normally reports the complex argument on the principal interval

```math
-\pi<\phi\le\pi.
```

Therefore, a continuously increasing phase may appear numerically as

```text
150°, 170°, 179°, -179°, -170°, ...
```

The jump from (179^\circ) to (-179^\circ) does not represent a physical jump of almost (360^\circ). It only means that the phase crossed the boundary of the principal interval.

This behavior is called **phase wrapping**.

### 8.1 Why direct phase subtraction can fail

Suppose the expected phase is

```math
\phi_{\mathrm{expected}}
=
179^\circ
```

while the measured phase is

```math
\phi_{\mathrm{measured}}
=
-179^\circ.
```

Direct subtraction gives

```math
-179^\circ-179^\circ
=
-358^\circ.
```

However,

```math
-179^\circ
\equiv
181^\circ,
```

so the actual angular difference is only

```math
2^\circ.
```

A direct subtraction can therefore report an artificially large error near the (+\pi/-\pi) branch cut.

### 8.2 Wrapped phase difference

The wrapped difference is calculated using

```math
\Delta\phi_{\mathrm{wrapped}}
=
\arg
\left[
e^{i(
\phi_{\mathrm{measured}}
-
\phi_{\mathrm{expected}}
)}
\right].
```

The exponential automatically removes integer multiples of (2\pi), while `arg` returns the equivalent difference inside the principal interval.

In NumPy:

```python
phase_error = np.angle(
    np.exp(
        1.0j * (
            measured_phase
            - expected_phase
        )
    )
)
```

This can be interpreted as:

1. calculate the ordinary phase difference;
2. convert it into a complex direction;
3. return the equivalent angle between (-\pi) and (+\pi).

### 8.3 Phase difference directly from complex amplitudes

If two harmonic responses are

```math
\tilde u_1
=
A_1e^{i\phi_1}
```

and

```math
\tilde u_2
=
A_2e^{i\phi_2},
```

their ratio is

```math
\frac{\tilde u_2}{\tilde u_1}
=
\frac{A_2}{A_1}
e^{i(\phi_2-\phi_1)}.
```

Therefore,

```math
\arg
\left(
\frac{\tilde u_2}{\tilde u_1}
\right)
```

directly gives the wrapped phase difference.

In NumPy:

```python
phase_difference = np.angle(
    second.complex_amplitude
    / first.complex_amplitude
)
```

This is usually preferable to subtracting two values returned separately by `np.angle()`.

### 8.4 Wrapped phase versus unwrapped phase

A wrapped phase is always represented inside the principal interval.

An **unwrapped phase** instead attempts to reconstruct continuous phase accumulation by adding or subtracting multiples of (2\pi).

For example, a propagating wave might physically accumulate phase as

```math
0,
\frac{\pi}{2},
\pi,
\frac{3\pi}{2},
2\pi,
\frac{5\pi}{2},
\ldots
```

while the wrapped representation appears as

```math
0,
\frac{\pi}{2},
\pi,
-\frac{\pi}{2},
0,
\frac{\pi}{2},
\ldots
```

Wrapped phase differences are appropriate for comparing two phases or calculating a phase error.

Phase unwrapping can instead be useful when studying continuous phase accumulation across many monitor positions.

Phase also becomes unreliable when the harmonic amplitude is extremely small. Near zero complex amplitude, even small numerical perturbations can cause a large apparent change in phase.

---

## 9. Integer-cycle windows and spectral leakage

The single-frequency projection is exact for an ideal sampled sinusoid when the analysis window contains an integer number of cycles and the analyzed frequency is represented consistently.

Suppose the selected interval contains

```math
N_{\mathrm{cycles}}
=
N\Delta t f.
```

If this number is an integer, the sinusoid begins and ends at the same point in its cycle.

If the window instead cuts through a noninteger number of cycles, the two ends of the finite record do not match in phase. Mathematically, multiplying the infinite signal by a finite rectangular analysis window then spreads part of the signal into nearby frequencies.

This effect is called **spectral leakage**.

The Phase 3 scenarios deliberately use integer-cycle windows:

```text
Controlled uniform scenario
    250 samples
    dt = 0.4
    f = 0.05

    cycles
    = 250 * 0.4 * 0.05
    = 5


Paired interface scenario
    150 samples
    dt = 0.4
    f = 0.05

    cycles
    = 150 * 0.4 * 0.05
    = 3
```

The current estimator does not apply a Hann or other spectral window.

Adding such a window could reduce spectral leakage for noninteger-cycle intervals, but it would also require corresponding amplitude normalization and a clear choice about the desired frequency resolution.

---

## 10. Propagation phase

A right-propagating harmonic plane wave can be represented as

```math
u(x,t)
=
A\cos(
\omega t-kx+\phi_0
).
```

The phase at position (x) is therefore

```math
\phi(x)
=
-kx+\phi_0.
```

At two monitor positions (x_1) and (x_2),

```math
\phi_2-\phi_1
=
-k(x_2-x_1).
```

For a nondispersive continuum medium,

```math
k
=
\frac{\omega}{c}
=
\frac{2\pi f}{c}.
```

Thus, in the exact continuous wave equation, the phase accumulated over a distance

```math
\Delta x_{\mathrm{monitor}}
=
x_2-x_1
```

would be

```math
\Delta\phi
=
-\frac{\omega}{c}
\Delta x_{\mathrm{monitor}}.
```

However, the simulator does not solve the continuous derivatives exactly. It solves their finite-difference approximations.

The resulting numerical wave therefore has a slightly different relationship between frequency and wave number.

This effect is called **numerical dispersion**.

---

## 11. Numerical dispersion relation

For a wave that is uniform in (y), the 2D wave equation reduces locally to

```math
u_{tt}
=
c^2u_{xx}.
```

The centered second-order finite-difference approximation is

```math
\frac{
u_i^{n+1}
-
2u_i^n
+
u_i^{n-1}
}{
\Delta t^2
}
=
c^2
\frac{
u_{i+1}^n
-
2u_i^n
+
u_{i-1}^n
}{
\Delta x^2
}.
```

To determine how a harmonic wave propagates through this discrete grid, assume a numerical solution of the form

```math
u_i^n
=
A
e^{i(
k_h i\Delta x
-
\omega n\Delta t
)}.
```

Here (k_h) is the **numerical wave number**.

It plays the same role for the finite-difference scheme that

```math
k=\frac{\omega}{c}
```

plays for the continuous wave equation.

Substituting the harmonic form into the discrete equation gives

```math
\sin^2
\left(
\frac{\omega\Delta t}{2}
\right)
=
\left(
\frac{c\Delta t}{\Delta x}
\right)^2
\sin^2
\left(
\frac{k_h\Delta x}{2}
\right).
```

The sine functions appear because the centered second differences act on discrete complex exponentials.

For example,

```math
u_{i+1}
-
2u_i
+
u_{i-1}
```

contains the factor

```math
e^{ik_h\Delta x}
-
2
+
e^{-ik_h\Delta x},
```

which can be reduced using trigonometric identities to

```math
-4
\sin^2
\left(
\frac{k_h\Delta x}{2}
\right).
```

An analogous expression appears for the time derivative.

### 11.1 Numerical wave number

Solving the discrete dispersion relation for (k_h) gives

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

In general,

```math
k_h
\neq
\frac{\omega}{c}.
```

The numerical phase velocity is therefore

```math
v_{p,\mathrm{num}}
=
\frac{\omega}{k_h},
```

which is generally slightly different from the physical wave speed (c).

This discrepancy is **numerical dispersion**.

It is not necessarily an implementation error. It is a property of the finite-difference approximation.

### 11.2 Phase between two monitors

Because the simulated harmonic wave propagates according to (k_h), the expected numerical phase difference between monitors separated by

```math
\Delta x_{\mathrm{monitor}}
```

is

```math
\Delta\phi_h
=
-k_h\Delta x_{\mathrm{monitor}}.
```

Therefore, the appropriate validation comparison is not only

```math
\Delta\phi_{\mathrm{measured}}
\overset{?}{\approx}
-\frac{\omega}{c}
\Delta x_{\mathrm{monitor}},
```

but more importantly

```math
\Delta\phi_{\mathrm{measured}}
\overset{?}{\approx}
-k_h
\Delta x_{\mathrm{monitor}}.
```

If the measured phase differs slightly from the continuum prediction but agrees with the discrete prediction, the simulator is behaving as expected.

If it also disagrees with the discrete prediction, then possible implementation issues should be investigated, such as:

* incorrect monitor positions;
* source phase handling;
* incorrect sample times;
* time-indexing errors;
* errors in harmonic projection;
* unintended reflections.

### 11.3 Relation to grid refinement

For sufficiently small arguments,

```math
\sin\theta
\approx
\theta.
```

When (\Delta x) and (\Delta t) become sufficiently small, the discrete relation approaches

```math
\omega^2
\approx
c^2k_h^2,
```

so that

```math
k_h
\approx
\frac{\omega}{c}.
```

The numerical wave therefore approaches the continuum wave as the discretization is refined.

This is one reason why sufficient spatial resolution in points per wavelength is important in wave simulations.

### 11.4 Extension to general 2D propagation

The relation above assumes the field is uniform in (y), so that (k_y=0).

For a general 2D harmonic wave, both spatial directions contribute to the numerical dispersion relation. The uniform-(y) case is used in the controlled Phase 3 experiment because it provides a simple one-dimensional propagation scenario for validation.

---

## 12. Complex ratios for propagation and scattering analysis

Suppose a harmonic measurement produces complex incident, reflected, and transmitted responses

```math
\tilde u_i,
\qquad
\tilde u_r,
\qquad
\tilde u_t.
```

Field-amplitude ratios can be defined as

```math
r
=
\frac{\tilde u_r}{\tilde u_i}
```

and

```math
t
=
\frac{\tilde u_t}{\tilde u_i}.
```

Because these quantities are complex, they retain both relative amplitude and relative phase.

Their magnitudes,

```math
|r|,
\qquad
|t|,
```

describe field-amplitude ratios, while

```math
\arg(r),
\qquad
\arg(t)
```

describe the corresponding relative phase shifts.

### 12.1 Why monitor position matters

Suppose the incident field is measured at an upstream monitor while the transmitted field is measured at a downstream monitor.

Even if there were no interface between them, the two complex responses would not normally be identical because the wave accumulates propagation phase while traveling between the monitor positions.

For example, a numerical harmonic wave may behave approximately as

```math
\tilde u(x)
\propto
e^{-ik_hx}.
```

Two monitors separated by distance (L) therefore differ by a propagation factor

```math
e^{-ik_hL}.
```

Consequently, the direct ratio

```math
\frac{
\tilde u_{\mathrm{downstream}}
}{
\tilde u_{\mathrm{upstream}}
}
```

contains both the physical effect being studied and the phase accumulated while propagating between the two monitor positions.

For interface measurements, it is therefore useful to perform a separate **reference simulation**.

### 12.2 Paired reference experiment

The Phase 3 interface analysis uses two otherwise identical simulations.

#### Reference run

The first simulation contains the uniform reference medium without the interface.

At the downstream monitor, the harmonic response is approximately

```math
\tilde u_{\mathrm{ref,down}}
\sim
A_s
P_{\mathrm{ref}},
```

where:

* (A_s) represents the effective source amplitude and source phase;
* (P_{\mathrm{ref}}) represents propagation from the source to the downstream monitor, including numerical phase accumulation.

#### Interface run

The second simulation contains the material interface.

At the same downstream monitor,

```math
\tilde u_{\mathrm{interface,down}}
```

contains the corresponding source and propagation effects together with the modification caused by the interface.

A normalized downstream response can therefore be formed as

```math
t_{\mathrm{measured}}
=
\frac{
\tilde u_{\mathrm{interface,down}}
}{
\tilde u_{\mathrm{ref,down}}
}.
```

The important point is that the numerator and denominator are evaluated at the **same downstream position**.

Effects common to both experiments can then cancel or be strongly reduced.

Schematically, if

```math
\tilde u_{\mathrm{ref,down}}
\sim
A_sP
```

and

```math
\tilde u_{\mathrm{interface,down}}
\sim
A_sPt,
```

then

```math
\frac{
\tilde u_{\mathrm{interface,down}}
}{
\tilde u_{\mathrm{ref,down}}
}
\sim
t.
```

This is analogous to performing a reference or calibration measurement before inserting a sample in a physical experiment.

### 12.3 Why not normalize only by an upstream monitor?

If the downstream response were divided directly by an upstream incident response, the ratio could contain a factor such as

```math
t
e^{-ik_h(
x_{\mathrm{down}}
-
x_{\mathrm{up}}
)}.
```

The resulting phase would then contain both

```math
\arg(t)
```

and the propagation phase between the two monitor positions.

Using the paired downstream reference helps isolate what changed because of the interface rather than what changed simply because the wave propagated farther.

### 12.4 Why the compensation is only partial

Reference normalization does not guarantee that every numerical or physical effect cancels exactly.

Introducing an interface changes the propagation environment and may introduce:

* reflections;
* interference;
* a different wave number in the transmitted medium;
* interaction with the source;
* interaction with finite boundaries;
* residual numerical effects.

For this reason, the reference normalization is best understood as a calibration procedure that removes **common** source and propagation effects rather than as an exact mathematical isolation of the interface coefficient in every configuration.

### 12.5 Field amplitude is not automatically power

The quantities

```math
|r|
```

and

```math
|t|
```

are **field-amplitude ratios**.

They are not automatically reflection and transmission power coefficients.

In general,

```math
R
\neq
|r|
```

and

```math
T
\neq
|t|.
```

Even expressions such as

```math
R=|r|^2,
\qquad
T=|t|^2
```

require assumptions about the governing physical field and the relationship between field amplitude and energy flux.

The correct power or flux relationship depends on:

* the governing wave equation;
* the physical meaning and normalization of (u);
* propagation direction;
* material properties;
* wave impedance or equivalent quantities;
* measurement aperture.

The current Phase 3 analysis therefore treats these quantities explicitly as **complex field-amplitude ratios**, not as general power coefficients.

---

## 13. Implementation mapping

The implementation is located in

```text
wavesim/analysis.py
```

The primary call is

```python
response = estimate_harmonic_response(
    samples,
    dt,
    frequency,
    start_step=start_step,
    stop_step=stop_step,
)
```

The returned `HarmonicResponse` contains

```text
complex_amplitude
frequency
start_step
stop_step
sample_count
duration
cycle_count
```

and calculated properties

```text
amplitude
phase
```

with

```math
\text{amplitude}
=
|\tilde u|
```

and

```math
\text{phase}
=
\arg(\tilde u).
```

The function accepts any one-dimensional scalar sequence. It does not depend directly on `Wave2DSimulation` or `FieldMonitorState`.

This separation allows the same harmonic-analysis procedure to be applied to:

* live monitor histories;
* synthetic validation signals;
* saved data in a future result format;
* compatible external scalar histories.

---

## 14. Validation contract

The harmonic-analysis tests verify:

1. Recovery of a known cosine amplitude.
2. Recovery of a known cosine phase.
3. The (-\pi/2) phase of a sine under the cosine convention.
4. Invariance to a constant offset.
5. Correct analysis metadata.
6. Default use of the remaining history after `start_step`.
7. Rejection of multidimensional samples.
8. Rejection of empty or non-finite samples.
9. Rejection of invalid `dt` or frequency.
10. Rejection of frequencies at or above Nyquist.
11. Rejection of invalid half-open bounds.
12. Rejection of windows containing too few cycles.

The controlled propagation scenario additionally validates the measured phase difference against the finite-difference numerical dispersion relation.

The paired interface scenario uses reference normalization to test harmonic amplitude and phase changes associated with an interface while reducing common source and propagation effects.

---

## 15. Limitations

The current single-frequency estimator assumes:

* uniform temporal sample spacing;
* a known target frequency;
* a sufficiently steady response inside the selected window;
* a finite one-dimensional scalar history;
* enough cycles for a meaningful estimate.

It does not currently provide:

* a broadband frequency spectrum;
* automatic steady-state detection;
* automatic arrival-time detection;
* phase unwrapping over many monitors;
* spectral window functions;
* uncertainty estimates;
* confidence intervals;
* direct power or energy-flux calculation.

It also does not guarantee meaningful phase values when the harmonic amplitude is close to zero.

These are future analysis features rather than hidden properties of the current estimator.

---

## 16. Summary

Phase 3 estimates a harmonic response by projecting a mean-centered scalar history onto a complex reference oscillator:

```math
\tilde u(f)
=
\frac{2}{N}
\sum_n
(u_n-\bar u)
e^{-i2\pi ft_n}.
```

Multiplication by the reference oscillator shifts the component at the requested frequency to zero frequency. Averaging then preserves that coherent component while oscillations at other frequencies tend to cancel.

The resulting complex number

```math
\tilde u
=
Ae^{i\phi}
```

stores both amplitude and phase.

Analysis windows use half-open bounds and are chosen after source turn-on and initial propagation transients. Integer-cycle windows reduce spectral leakage.

Because phase is periodic, phase differences must be interpreted modulo (2\pi). Complex ratios provide a convenient and stable way to calculate relative amplitude and wrapped phase.

For propagation validation, the simulator is compared with the **finite-difference numerical dispersion relation**, not only with the ideal continuum relation. The discrete scheme generally propagates harmonic waves with a numerical wave number

```math
k_h
\neq
\frac{\omega}{c},
```

and the resulting phase difference between monitors must reflect this numerical dispersion.

For interface experiments, a downstream measurement with the interface is normalized by a downstream reference measurement from an otherwise equivalent uniform simulation. This reduces common source-strength and propagation effects and better isolates the change produced by the interface.

Together, these tools provide the mathematical bridge between recorded field-monitor histories and the controlled propagation and scattering measurements used in Phase 3.
