# Phase 3 — Controlled Sources and Field Monitors

**Date:** 2026-08-04

**Status:** Implementation, validation, documentation, technical audit, local milestone commit, and local tag complete; push pending

---

## 1. Objective

Phase 3 extends the validated Phase 2 scalar-wave solver with controlled
spatial excitation and reusable field measurements.

The phase goals are:

1. Preserve the exact Phase 2 continuous point-source behavior.
2. Separate source geometry from its temporal waveform.
3. Add a finite-aperture, plane-wave-like line source.
4. Suppress abrupt-start transients with a smooth source ramp.
5. Record the scalar field at named point and line monitors.
6. Estimate steady harmonic amplitude and phase from monitor histories.
7. Validate propagation through a uniform medium.
8. Use paired reference and interface runs to separate incident, reflected,
   and transmitted harmonic fields.
9. Visualize source apertures, monitors, histories, and analysis windows.

Phase 3 does not replace the scalar model with Maxwell FDTD and does not claim
that a finite-aperture line source is an exact infinite plane wave.

---

## 2. Phase 2 baseline

Phase 3 begins from commit:

```text
ca7f829 Validate and complete Phase 2 material infrastructure
```

and tag:

```text
phase-2-complete
```

The Phase 2 baseline contains 59 tests and establishes:

- the modular `wavesim` package;
- uniform and spatially varying material maps;
- reusable rectangular material geometry;
- maximum-speed CFL validation;
- point-source injection after the wave update;
- source-free scalar-wave energy validation;
- a stable package-level API;
- exact Phase 2.1 numerical regression values.

The Phase 2.1 regression remains the principal compatibility check throughout
Phase 3. Its expected values were not changed.

---

## 3. Checkpoint 3.1 — Source behavioral contract

Focused source tests were added before the source implementation was
refactored.

The protected behavior is:

```text
source = none
    field remains unchanged

source = point_sine
    exactly one configured cell is changed
    the source value is added rather than assigned
    time is evaluated at t = step_index * dt
```

The protected point-source expression is:

```math
s(t_n)
=
A\sin(2\pi f n\Delta t).
```

The solver ordering remains:

```text
finite-difference wave update
    -> source injection into the completed next field
    -> energy calculation
    -> state promotion
```

Checkpoint result:

```text
64 tests passed
```

---

## 4. Checkpoint 3.2 — Spatial source profiles

Source geometry was moved into:

```text
wavesim/sources.py
```

An active source now has a floating-point profile with:

```text
source_profile.shape == grid.shape
all values finite
outer boundary values equal to zero
at least one nonzero value for active sources
```

The point-source profile is:

```python
profile[source.x, source.y] = 1.0
```

`Wave2DSimulation` constructs the profile once during initialization and
reuses it on every step. The completed profile is marked read-only:

```python
profile.setflags(write=False)
```

Direct three-argument calls to:

```python
apply_source(field, step_index, config)
```

remain supported for compatibility. Active simulations pass their precomputed
profile explicitly.

Checkpoint result:

```text
71 tests passed
```

The Phase 2.1 numerical regression remained unchanged.

---

## 5. Checkpoint 3.3 — Ramped finite-aperture line source

The supported source kinds are now:

```text
none
point_sine
line_sine
```

The vertical line-source profile uses half-open bounds:

```python
profile[
    source.x,
    source.y_start:source.y_stop,
] = 1.0
```

Therefore the final occupied transverse index is:

```text
y_stop - 1
```

Line-source validation requires:

```text
1 <= x < nx - 1
1 <= y_start < y_stop <= ny - 1
finite amplitude
finite positive frequency below temporal Nyquist
finite nonnegative ramp_cycles
```

### Smooth turn-on

The configured ramp duration is:

```math
T_r
=
\frac{N_{\mathrm{ramp}}}{f}.
```

The envelope is:

```math
g(t)
=
\begin{cases}
\sin^2\left(\dfrac{\pi t}{2T_r}\right), & 0\le t<T_r,\\
1, & t\ge T_r.
\end{cases}
```

The complete spatially distributed source is:

```math
s(x,y,t)
=
A\,g(t)\sin(2\pi ft)\,p(x,y),
```

where `p(x,y)` is the source profile.

The default remains:

```text
ramp_cycles = 0
```

so the legacy point source receives a unit envelope and retains its exact
Phase 2 behavior.

Checkpoint result:

```text
81 tests passed
```

---

## 6. Checkpoint 3.4 — Field monitors

Monitor configuration is represented by:

```python
FieldMonitorConfig
```

Supported monitor kinds are:

```text
point
vertical_line
```

Monitor runtime history is represented by:

```python
FieldMonitorState
```

Each history stores:

```text
steps
times
values
```

### Point monitor

A point monitor records:

```python
field[monitor.x, monitor.y]
```

### Vertical-line monitor

A vertical-line monitor uses the half-open interval:

```python
field[
    monitor.x,
    monitor.y_start:monitor.y_stop,
]
```

The initial reduction is a coherent spatial mean:

```math
\bar E_z(x,t)
=
\frac{1}{N_y}
\sum_j E_z(x,j,t).
```

An RMS reduction was intentionally not used because it would discard sign and
phase information needed for harmonic analysis.

### Sampling convention

Monitor histories include the initial state:

```text
step = 0
time = 0
```

For every call to `advance()`, sampling occurs after source injection and state
promotion:

```text
wave update
    -> source injection
    -> energy calculation
    -> state promotion
    -> monitor sampling
```

Consequently monitor sample `n` represents the completed field at:

```math
t_n=n\Delta t.
```

After `N` simulation advances:

```text
monitor history length = N + 1
energy history length = N + 1
```

Monitor names must be nonempty and unique.

Checkpoint result:

```text
94 tests passed
```

---

## 7. Checkpoint 3.5 — Harmonic-response analysis

Frequency-domain analysis was added in:

```text
wavesim/analysis.py
```

The primary function is:

```python
estimate_harmonic_response(...)
```

and its result is represented by:

```python
HarmonicResponse
```

The estimator removes the mean of the selected window and calculates:

```math
\tilde E_z(f)
=
\frac{2}{N}
\sum_{n=n_0}^{n_1-1}
\left(E_{z,n}-\bar E_z\right)
e^{-i2\pi f t_n}.
```

Analysis bounds use the half-open convention:

```text
[start_step, stop_step)
```

The result reports:

```text
complex amplitude
amplitude magnitude
phase
frequency
start and stop steps
sample count
duration
cycle count
```

The phase convention is cosine based:

```math
A\cos(2\pi ft+\phi)
\quad\Longrightarrow\quad
\tilde E_z=Ae^{i\phi}.
```

Therefore:

```math
A\sin(2\pi ft)
=
A\cos\left(2\pi ft-\frac{\pi}{2}\right)
```

has phase:

```math
-\frac{\pi}{2}.
```

Validation covers dimensionality, finite values, positive time step, positive
frequency, temporal Nyquist, valid bounds, and a minimum number of cycles.

---

## 8. Checkpoint 3.6 — Controlled uniform-medium scenario

The scenario is defined in:

```text
simulations/wave2d_controlled_line_source.py
```

### Parameters

```text
Grid
    nx = 260
    ny = 180
    dx = 1
    dy = 1

Time
    dt = 0.4
    steps = 700

Material
    n = 1
    c = 1

Source
    kind = line_sine
    x = 45
    y interval = [35, 145)
    amplitude = 0.5
    frequency = 0.05
    ramp = 4 cycles

First monitor
    x = 90
    y interval = [60, 120)

Second monitor
    x = 125
    y interval = [60, 120)

Boundary
    kind = sponge
    width = 25

Analysis window
    steps = [450, 700)
    samples = 250
    duration = 100
    cycles = 5
```

The nominal wavelength is:

```math
\lambda
=
\frac{c}{f}
=
\frac{1}{0.05}
=
20.
```

The two monitors are separated by:

```text
35 cells = 1.75 nominal wavelengths
```

This avoids a trivial zero wrapped phase difference.

### Numerical phase validation

For propagation that is uniform in `y`, the finite-difference dispersion
relation is:

```math
\sin^2\left(\frac{\omega\Delta t}{2}\right)
=
\left(\frac{c\Delta t}{\Delta x}\right)^2
\sin^2\left(\frac{k_h\Delta x}{2}\right).
```

The measured monitor phase difference is compared with the numerical wave
number `k_h`, rather than assuming a dispersion-free continuum solver.

The automated scenario validation confirms:

- finite monitor histories;
- nonzero harmonic responses at both monitors;
- reasonably consistent finite-aperture amplitudes;
- phase advance consistent with numerical dispersion;
- source and monitors outside the sponge;
- CFL stability;
- at least ten points per wavelength.

The interactive visualization was inspected and behaved as expected.

### Measured controlled-propagation result

A fresh headless run of the final controlled scenario produced:

```text
First amplitude          9.491553785397
First phase              1.627033534650 rad
Second amplitude         8.533041616772
Second phase            -3.087287928309 rad
Amplitude ratio          0.899014198276
Wrapped phase advance    1.568863844220 rad
Analysis cycles          5.0
```

The finite-difference dispersion relation predicts:

```text
Numerical wave number    0.315256488702
Wrapped phase advance    1.532393509776 rad
Wrapped phase error      0.036470334444 rad
```

The measured amplitude ratio remains close to unity despite finite-aperture
diffraction. The small phase error remains well inside the protected scenario
tolerance and supports the configured time-level, monitor-separation, and
harmonic-phase conventions.

The interactive scenario remains reproducible through:

```powershell
python -m simulations.wave2d_controlled_line_source
```

and should be inserted here before final Phase 3 tagging.

---

## 9. Checkpoint 3.7 — Paired dielectric-interface experiment

The paired experiment is defined in:

```text
simulations/wave2d_interface_measurement.py
```

It performs:

1. A uniform reference run.
2. A run with a planar interface between `n=1.0` and `n=1.5`.

Both runs use the same:

```text
configuration
grid
time step
source profile
source ramp
monitor geometry
boundary configuration
analysis window
```

Only the material map changes.

### Parameters

```text
Grid
    nx = 340
    ny = 180

Time
    dt = 0.4
    steps = 900

Source
    x = 45
    y interval = [35, 145)
    frequency = 0.05
    ramp = 4 cycles

Upstream monitor
    x = 110
    y interval = [60, 120)

Interface
    x index = 180
    n_left = 1.0
    n_right = 1.5

Downstream monitor
    x = 225
    y interval = [60, 120)

Analysis window
    steps = [750, 900)
    samples = 150
    duration = 60
    cycles = 3
```

The analysis window begins after the fully ramped field reaches both monitors.
The earlier window `[600, 850)` was rejected because the reference and
interface signals contained unequal portions of the propagating source ramp.

### Field separation

The incident response is taken from the upstream reference monitor:

```math
\tilde E_i
=
\tilde E_{\mathrm{reference,upstream}}.
```

The reflected response is isolated through matched-run subtraction:

```math
\tilde E_r
=
\tilde E_{\mathrm{interface,upstream}}
-
\tilde E_{\mathrm{reference,upstream}}.
```

The transmitted response is measured by the downstream interface monitor.
The downstream reference response normalizes source strength, propagation,
and finite-aperture behavior in the uniform case.

The measured field ratios are:

```math
r_{\mathrm{measured}}
=
\frac{\tilde E_r}{\tilde E_i},
```

and:

```math
t_{\mathrm{measured}}
=
\frac{\tilde E_{\mathrm{interface,downstream}}}
{\tilde E_{\mathrm{reference,downstream}}}.
```

### Analytical scalar coefficients

For the selected scalar interface model at normal incidence:

```math
r
=
\frac{k_1-k_2}{k_1+k_2}
=
\frac{n_1-n_2}{n_1+n_2},
```

and:

```math
t
=
\frac{2k_1}{k_1+k_2}
=
\frac{2n_1}{n_1+n_2}.
```

For:

```text
n1 = 1.0
n2 = 1.5
```

the infinite-plane-wave scalar predictions are:

```text
r = -0.2
|r| = 0.2
t = 0.8
R = 0.04
T = 0.96
R + T = 1.0
```

### Measured finite-aperture result

The same fresh headless run produced:

```text
|r|      0.155401652520
|t|      0.637482577515
R        0.024149673606
T        0.609576054953
R + T    0.633725728559
```

The measured value of `R + T` is not treated as a conservation measurement.
The source has a finite aperture and the monitors average only a central
transverse interval. Diffraction redistributes field outside the monitor
aperture, the wavelength changes across the interface, and the sponge removes
part of the diffracted field.

Consequently:

```text
the analytical infinite-plane-wave coefficients must conserve flux
the finite-aperture measurements must be finite, positive, and physically
scaled
the aperture estimate is not required to sum to one
```

A complete quantitative flux measurement would require full transverse flux
integration, periodic transverse boundaries, a total-field/scattered-field
source, or direct time-averaged flux sampling using temporal and spatial field
derivatives.

Checkpoint result before the visualization and final API tests:

```text
130 tests passed
```

---

## 10. Checkpoint 3.8 — Visualization

Visualization remains isolated in:

```text
wavesim/visualization.py
```

The animation now displays:

- point sources as star markers;
- line sources as solid aperture lines;
- point monitors as outlined markers;
- vertical-line monitors as dotted lines;
- material interfaces and measurement geometry in one legend.

Monitor-history figures display:

- one time history per named monitor;
- simulation time on the horizontal axis;
- monitored `E_z` on the vertical axis;
- an optional shaded half-open harmonic-analysis window.

The controlled-source interactive simulation was inspected manually. The
source aperture, monitor lines, histories, legend, and analysis-window shading
appeared as configured.

Matplotlib remains outside the solver, source, monitor, and analysis modules.

---

## 11. Stable Phase 3 public API

The intended stable Phase 3 additions are:

```text
FieldMonitorConfig
FieldMonitorState
HarmonicResponse
estimate_harmonic_response
```

They are available through the package-level namespace:

```python
from wavesim import (
    FieldMonitorConfig,
    FieldMonitorState,
    HarmonicResponse,
    estimate_harmonic_response,
)
```

The following remain implementation or scenario details:

```text
create_source_profile
validate_source_profile
apply_source
sample_field_monitor
record_monitor_samples
ScatteringResponse
```

The Phase 3 API is protected by:

```text
tests/test_phase3_validation.py
```

The Phase 2 public-API test remains a historical subset test for the Phase 2
contract.

---

## 12. Phase 3 test coverage

Phase 3 adds focused coverage for:

```text
legacy source behavior
source ordering
spatial source-profile construction
source-profile validation and immutability
line-source half-open geometry
sine-squared ramp behavior
point monitor sampling
vertical-line coherent means
monitor naming and geometry validation
monitor time indexing
source-injected sampling order
harmonic amplitude and phase recovery
DC-offset removal
Nyquist and analysis-window validation
controlled uniform propagation
finite-difference numerical phase advance
paired reference/interface construction
incident/reflected field separation
finite-aperture transmission measurement
analytical scalar coefficients
source and monitor overlays
monitor-history plots
analysis-window visualization
Phase 3 public API
cross-feature scenario construction
```

The final complete suite result is:

```text
Ran 139 tests in 9.946s

OK
```

The suite includes the visualization and Phase 3 public-API validation tests.
The temporary diagnostic printing used while selecting controlled-scenario
tolerances was removed before this final run.

---

## 13. Repository audit result

The final Phase 3 technical audit produced:

```text
Complete test suite
    Ran 139 tests in 9.946s
    OK

In-memory compilation
    Compiled 28 Python files successfully

Headless construction
    wavesim imported successfully
    controlled line-source scenario constructed successfully
    paired interface scenario constructed successfully

Repository quality
    git diff --check passed
    no unresolved TODO, FIXME, XXX, or HACK markers in source or tests
```

The duplicate NumPy import, trailing whitespace, and temporary automated-test
diagnostic prints identified during the pre-closeout review were removed
before the final run.

Documentation contains intentional occurrences of work-marker names while
describing the audit procedure and historical Phase 2 result. These are not
unresolved implementation markers.

Git reported normal LF-to-CRLF notices for tracked text files on Windows. They
are line-ending normalization notices, not whitespace or code failures.

---

## 14. Known limitations

The completed implementation retains these scientific and software limits:

1. The solver advances a scalar `E_z` wave equation, not the complete Maxwell
   field set.
2. The line source has a finite aperture and is only plane-wave-like in its
   central region.
3. The source launches waves in both positive and negative `x` directions.
4. No Gaussian beam, angled phase profile, or total-field/scattered-field
   source is implemented.
5. Vertical-line monitors currently support a coherent mean only.
6. Field monitors do not directly calculate time-averaged spatial flux.
7. Finite-aperture monitor ratios do not integrate energy across the complete
   transverse domain.
8. The sponge is not a PML.
9. The material model remains lossless, nondispersive, isotropic, and
   nonmagnetic.
10. The interface update uses the existing pointwise variable-speed scalar
    discretization rather than a conservative flux-form interface operator.
11. Harmonic analysis measures one configured temporal frequency and requires
    the caller to select an appropriate steady-state window.
12. Monitor histories are stored in memory as Python lists.
13. Scenario parameters remain encoded in Python modules.
14. Results are not saved automatically.

These limitations bound the conclusions that can be drawn from the Phase 3
experiments.

---

## 15. Phase 3 definition of done

```text
[x] Legacy point-source behavior protected by focused tests
[x] Phase 2.1 numerical regression retained
[x] Spatial source profiles implemented
[x] Active source profiles validated
[x] Simulation source profiles made read-only
[x] Finite-aperture line source implemented
[x] Half-open line-source bounds validated
[x] Sine-squared source ramp implemented
[x] Point field monitors implemented
[x] Vertical-line coherent-mean monitors implemented
[x] Monitor histories aligned with simulation time levels
[x] Harmonic amplitude and phase estimator implemented
[x] Controlled uniform propagation scenario implemented
[x] Numerical-dispersion phase validation implemented
[x] Paired reference/interface scenario implemented
[x] Incident and reflected harmonic responses separated
[x] Analytical scalar interface coefficients tested
[x] Finite-aperture measurement limitations documented
[x] Source and monitor animation overlays implemented
[x] Monitor-history visualization implemented
[x] Analysis-window visualization implemented
[x] Controlled-source visualization inspected manually
[x] Stable Phase 3 public API selected
[x] Phase 3 public-API validation added
[x] Comprehensive Phase 3 simulation log written
[x] Duplicate NumPy import removed
[x] Trailing whitespace removed
[x] Final full test suite rerun and exact count recorded
[x] All Python files compiled successfully
[x] Official Phase 3 scenarios imported and executed headlessly
[x] `git diff --check` passes
[x] Unresolved-marker scan passes
[x] Exact controlled-scenario measurements recorded
[x] Exact paired-interface measurements recorded
[x] README updated with Phase 3 implementation and closeout status
[x] Phase 3 changes committed
[ ] Phase 3 changes pushed
[x] Phase 3 milestone tag created
[ ] Phase 3 milestone tag pushed
```

Phase 3 implementation, scientific validation, documentation, technical
repository audit, local milestone commit, and local tag are complete. Only the
branch and tag push remain before the milestone is recorded on the remote.
