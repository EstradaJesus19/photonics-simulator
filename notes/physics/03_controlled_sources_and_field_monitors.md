# 03 — Controlled Sources and Field Monitors

> **Status:** Current technical reference through Phase 3.
>
> **Scope:** Controlled spatial source profiles, smooth source turn-on, field
> monitors, harmonic response, and approximate interface measurements.

## 1. Purpose of this note

The purpose of this note is to explain the physical and numerical meaning of
the controlled sources and field monitors introduced in Phase 3 of the
Photonics Simulator project.

Phase 2 established material maps and dielectric interfaces, but its active
experiments used a continuous point source. A point source produces circular
wavefronts that reach an interface over many incidence angles. That is useful
for qualitative scattering, but it is poorly controlled for measuring one
normal-incidence harmonic response.

Phase 3 adds:

- spatial source profiles;
- a finite-aperture vertical line source;
- a smooth sine-squared turn-on envelope;
- named point and vertical-line field monitors;
- coherent transverse averaging;
- paired uniform-reference and interface experiments;
- harmonic amplitude and phase analysis.

The goal is controlled and reproducible scalar-wave measurement. The result is
still not a full Maxwell, exact plane-wave, or complete flux-measurement
system.

---

## 2. Governing scalar model

The solver advances:

```math
\frac{\partial^2 E_z}{\partial t^2}
=
c(x,y)^2
\left(
\frac{\partial^2 E_z}{\partial x^2}
+
\frac{\partial^2 E_z}{\partial y^2}
\right).
```

The material speed is:

```math
c(x,y)=\frac{c_{\mathrm{ref}}}{n(x,y)}.
```

The selected interpretation is a two-dimensional, out-of-plane `E_z` field in
an isotropic, lossless, nondispersive, nonmagnetic dielectric.

Phase 3 does not alter this equation or the Phase 2 interface discretization.
It changes how the field is excited and observed.

---

## 3. Discrete additive source model

The source is applied after the ordinary finite-difference wave update.

The solver ordering is:

```text
-> calculate next field from previous and current fields
-> apply fixed outer boundary values
-> add the configured source
-> calculate energy
-> promote the next field to the current state
-> record field monitors
```

At an active source cell, the source performs an addition:

```python
field[source_cell] += source_value
```

rather than assigning a prescribed field value.

This is often described as a soft or additive source. It does not force the
total field at the source cells to equal a fixed waveform. Existing waves can
pass through and superpose with the newly injected value.

The source is a discrete numerical forcing rule. It is not currently written
as an independently discretized forcing term on the right-hand side of the
continuous differential equation.

The post-update ordering and exact point-source trajectory are protected by
the Phase 2.1 regression and focused Phase 3 tests.

---

## 4. Separating spatial and temporal source behavior

Phase 3 represents source geometry through a spatial profile:

```math
p(x,y).
```

The temporal waveform is calculated separately. The combined source is:

```math
s(x,y,t)
=
A\,g(t)\sin(2\pi ft)\,p(x,y),
```

where:

- `A` is the configured source amplitude;
- `f` is the temporal frequency;
- `g(t)` is the source envelope;
- `p(x,y)` is the spatial profile.

This separation permits different source geometries to share the same
time-harmonic waveform and ramp logic.

The profile is a floating-point array with:

```text
shape = grid.shape
finite values
zero values on the outer boundary
at least one nonzero cell for active sources
```

It is constructed once, validated, marked read-only, and reused during time
stepping.

---

## 5. Point-source profile

The established point source uses:

```python
profile[source.x, source.y] = 1.0
```

All other cells are zero.

In a uniform isotropic medium, this localized excitation generates
approximately circular outgoing wavefronts. It excites a broad range of
propagation directions and transverse wave numbers.

The point source remains useful for:

- general propagation demonstrations;
- qualitative interface scattering;
- diffraction from finite objects;
- regression testing;
- broad visual exploration.

It remains unsuitable for isolating a single normal-incidence plane-wave
coefficient.

---

## 6. Finite-aperture vertical line source

The Phase 3 line source occupies:

```python
profile[
    source.x,
    source.y_start:source.y_stop,
] = 1.0
```

The bounds are half open, so the occupied cells are:

```text
y_start through y_stop - 1
```

Every active line cell receives the same temporal phase and amplitude. In the
central region, this preferentially launches wavefronts that are approximately
constant in `y` and propagate along positive and negative `x`.

The source does not select only the positive `x` direction. A simple additive
line excites waves on both sides of the source.

---

## 7. Finite aperture versus an exact plane wave

An ideal two-dimensional plane wave is uniform over an infinite transverse
extent:

```math
E_z(x,y,t)
=
A\cos(\omega t-kx),
```

with no `y` dependence.

The numerical source has finite transverse length. Its ends are discontinuities
in the spatial profile and therefore generate diffraction.

The controlled source is best described as:

```text
finite-aperture line source
```

or:

```text
plane-wave-like source in its central region
```

It should not be described as an exact infinite plane wave.

The central region becomes more plane-wave-like when:

- the aperture is wide relative to the wavelength;
- measurements are taken away from the aperture ends;
- source and monitors are outside the sponge;
- the domain is wide enough to delay transverse boundary influence;
- the analysis window avoids late reflected fields.

---

## 8. Why an abrupt sinusoid is undesirable

An infinite-duration sinusoid contains one temporal frequency. A sinusoid that
is switched on abruptly does not.

An abrupt source can be written as:

```math
s(t)=H(t)A\sin(2\pi ft),
```

where `H(t)` is a step function.

Multiplication by a sharp step in time broadens the frequency content. The
result contains a startup transient in addition to the desired harmonic.

Those extra frequencies:

- propagate at different numerical phase velocities;
- complicate monitor histories;
- delay steady harmonic behavior;
- contaminate reflection and transmission estimates;
- can interact with boundaries before the desired analysis window.

Phase 3 therefore introduces a smooth turn-on envelope.

---

## 9. Sine-squared source envelope

If the configured ramp contains `N_ramp` source cycles, its duration is:

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

At the start:

```math
g(0)=0.
```

At the end of the ramp:

```math
g(T_r)=1.
```

The derivative also approaches zero at both ends of the ramp, so the envelope
joins the zero and constant-amplitude regions smoothly.

This does not create a perfectly monochromatic finite-duration signal, but it
reduces the broadband startup content substantially compared with an abrupt
step.

The default is:

```text
ramp_cycles = 0
```

which returns a unit envelope and preserves the established point source.

---

## 10. Propagation and ramp-arrival timing

The source ramp is defined at the source location. A monitor does not see the
fully ramped signal until both the propagation delay and the ramp duration
have passed.

For a path divided into material segments, an approximate arrival time is:

```math
t_{\mathrm{arrival}}
=
T_r
+
\sum_m\frac{L_m}{c_m}.
```

This distinction was important in the paired interface experiment. The
uniform and interface runs have different downstream travel times because the
transmitted wave is slower in the higher-index material.

An analysis window that begins after the reference field becomes fully ramped
can still begin too early for the interface field. The Phase 3 paired window
was moved later so both signals contain the completed ramp.

---

## 11. Field monitors

A field monitor observes the numerical `E_z` field without modifying it.

Phase 3 supports:

```text
point monitor
vertical-line monitor
```

Monitor configuration is frozen, while `FieldMonitorState` stores the evolving
history.

Every monitor has a unique nonempty name. Its runtime state records:

```text
steps
times
values
```

The initial field is recorded at:

```text
step = 0
time = 0
```

Subsequent samples are recorded after source injection and state promotion.
Therefore the sample at step `n` represents the completed field at:

```math
t_n=n\Delta t.
```

---

## 12. Point monitor

A point monitor records one grid value:

```python
value = field[monitor.x, monitor.y]
```

It provides the most localized measurement, but it can be sensitive to:

- local interference;
- grid-scale variation;
- diffraction fringes;
- exact placement relative to a material interface;
- numerical anisotropy.

Point monitors are useful when a local field value is the quantity of
interest.

---

## 13. Coherent vertical-line monitor

A vertical-line monitor selects:

```python
samples = field[
    monitor.x,
    monitor.y_start:monitor.y_stop,
]
```

and calculates:

```math
\bar E_z(x,t)
=
\frac{1}{N_y}
\sum_j E_z(x,y_j,t).
```

This is a coherent mean: signed field values are averaged before any
magnitude is taken.

For a field that is nearly uniform across the aperture, the mean reinforces
the common plane-wave-like component. Transverse variations and some
diffraction structure tend to cancel.

An RMS field would be:

```math
E_{\mathrm{RMS}}
=
\sqrt{
\frac{1}{N_y}
\sum_j E_z^2
}.
```

RMS is nonnegative and discards the instantaneous sign and phase. It is
therefore not the selected reduction for harmonic complex-amplitude analysis.

---

## 14. Monitor aperture is not complete flux

A line-mean monitor records a coherent field amplitude over a selected
transverse interval. It does not integrate the complete wave-energy flux over
the domain.

The scalar-wave energy density is:

```math
\mathcal E
=
\frac{1}{2c^2}E_{z,t}^2
+
\frac{1}{2}|\nabla E_z|^2.
```

For the source-free scalar equation, the associated flux has the form:

```math
\mathbf S
=
-E_{z,t}\nabla E_z.
```

A complete time-averaged flux measurement would require temporal and spatial
derivatives and integration across the full transverse measurement surface.

The current line monitor instead records:

```math
\bar E_z(t).
```

Field outside the monitor aperture is not included. Diffraction can therefore
reduce the measured amplitude without implying that the complete simulated
energy has disappeared.

---

## 15. Controlled uniform-medium experiment

The uniform Phase 3 scenario uses a ramped line source and two central line
monitors.

Its purposes are:

1. Verify that both monitors record finite nonzero harmonic responses.
2. Check that the central amplitudes remain reasonably consistent.
3. Measure phase advance over a known separation.
4. Compare that phase with the finite-difference numerical dispersion
   relation.

The experiment validates the source, monitor, time-indexing, and harmonic
analysis chain before a material interface is introduced.

Because the source aperture is finite, the amplitude comparison uses a broad
physical tolerance rather than asserting exact equality.

---

## 16. Paired reference and interface experiments

One interface run alone cannot directly separate the upstream incident and
reflected fields because they overlap in space and time.

Phase 3 therefore performs two matched simulations:

```text
Reference run
    uniform material

Interface run
    identical configuration with one dielectric interface
```

The runs share:

- grid and time step;
- source position, profile, phase, amplitude, and ramp;
- boundary configuration;
- monitor geometry;
- analysis window.

Only the material map changes.

Let:

```math
\tilde E_{\mathrm{ref,u}}
```

be the upstream reference response and:

```math
\tilde E_{\mathrm{int,u}}
```

be the upstream interface response.

The incident response is identified as:

```math
\tilde E_i
=
\tilde E_{\mathrm{ref,u}}.
```

Linearity permits the reflected response to be isolated through subtraction:

```math
\tilde E_r
=
\tilde E_{\mathrm{int,u}}
-
\tilde E_{\mathrm{ref,u}}.
```

The transmitted interface response is compared with the downstream reference
response.

This method depends on deterministic matched forcing. Any change in source
timing, profile, grid, boundary, or monitor position would invalidate the
simple subtraction.

---

## 17. Analytical scalar interface coefficients

Consider a harmonic plane wave normally incident on a flat interface between two homogeneous media.

Let the interface be located at (x=0), with medium 1 on the left and medium 2 on the right. The corresponding wave numbers are

```math
k_1=\frac{\omega}{c_1},
\qquad
k_2=\frac{\omega}{c_2}.
```

The total field consists of an incident wave, a reflected wave, and a transmitted wave. Using complex harmonic notation,

```math
\tilde E_i(x)
=
A_i e^{ik_1x},
```

```math
\tilde E_r(x)
=
A_r e^{-ik_1x},
```

and

```math
\tilde E_t(x)
=
A_t e^{ik_2x}.
```

The reflected wave has the opposite spatial phase evolution because it propagates in the opposite direction.

At the interface, the scalar model imposes continuity of both (E_z) and its normal derivative.

### 17.1 Continuity of the field

At (x=0),

```math
E_i+E_r=E_t.
```

Using the interface amplitudes,

```math
A_i+A_r=A_t.
```

Define the complex field-amplitude coefficients

```math
r=\frac{A_r}{A_i},
\qquad
t=\frac{A_t}{A_i}.
```

Dividing the continuity condition by (A_i) gives

```math
1+r=t.
```

### 17.2 Continuity of the normal derivative

The second interface condition is

```math
\frac{\partial E_z}{\partial x}\bigg|_{1}
=
\frac{\partial E_z}{\partial x}\bigg|_{2}.
```

Differentiating the three harmonic waves gives, at the interface,

```math
ik_1A_i
-
ik_1A_r
=
ik_2A_t.
```

After cancelling (i) and dividing by (A_i),

```math
k_1(1-r)
=
k_2t.
```

The two interface conditions are therefore

```math
1+r=t,
```

and

```math
k_1(1-r)=k_2t.
```

Solving them gives the scalar reflection coefficient

```math
r
=
\frac{k_1-k_2}{k_1+k_2},
```

and the scalar transmission coefficient

```math
t
=
\frac{2k_1}{k_1+k_2}.
```

These coefficients describe **field amplitudes at the interface**.

### 17.3 Expression in terms of refractive index

For the normalized nonmagnetic materials used in the simulator,

```math
c_m=\frac{1}{n_m}.
```

Therefore,

```math
k_m
=
\frac{\omega}{c_m}
=
\omega n_m.
```

Substituting

```math
k_1=\omega n_1,
\qquad
k_2=\omega n_2
```

into the interface coefficients causes the common factor (\omega) to cancel, giving

```math
r
=
\frac{n_1-n_2}{n_1+n_2},
```

and

```math
t
=
\frac{2n_1}{n_1+n_2}.
```

For

```text
n1 = 1.0
n2 = 1.5
```

the scalar predictions are

```math
r
=
\frac{1.0-1.5}{1.0+1.5}
=
-0.2,
```

and

```math
t
=
\frac{2(1.0)}{1.0+1.5}
=
0.8.
```

Thus,

```text
r = -0.2
t = 0.8
```

The magnitude of the reflected field is therefore

```math
|r|=0.2.
```

The negative sign does not represent a negative physical amplitude. Instead, it indicates a phase reversal of

```math
\pi
```

between the reflected and incident fields.

Equivalently,

```math
-0.2
=
0.2e^{i\pi}.
```

The transmitted coefficient is positive, so the interface itself introduces no additional (\pi)-phase reversal in the transmitted field.

These values are field-amplitude coefficients, not directly reflected and transmitted power fractions. In addition, they describe the fields at the interface. Complex responses measured by monitors located away from the interface also contain propagation phase and must be interpreted accordingly.


---

## 18. Scalar energy-flux coefficients

The reflection and transmission coefficients derived above,

```math
r=\frac{A_r}{A_i},
\qquad
t=\frac{A_t}{A_i},
```

describe **field amplitudes**.

To determine how much wave energy is reflected and transmitted, the corresponding energy flux must be considered.

### 18.1 Energy flux of the scalar wave

Inside a homogeneous medium, the scalar wave equation can be written as

```math
\frac{1}{c_m^2}
\frac{\partial^2 E_z}{\partial t^2}
=
\frac{\partial^2 E_z}{\partial x^2}.
```

Multiplying by $\partial E_z/\partial t$ and applying the product rule gives a local conservation equation of the form

```math
\frac{\partial \mathcal E}{\partial t}
+
\frac{\partial S_x}{\partial x}
=
0,
```

where the scalar energy flux is proportional to

```math
S_x
\propto
-
\frac{\partial E_z}{\partial t}
\frac{\partial E_z}{\partial x}.
```

This quantity plays a role analogous to the Poynting flux in electromagnetic theory: its sign indicates the direction in which wave energy propagates.

For a harmonic right-propagating plane wave,

```math
E_z(x,t)
=
A\cos(\omega t-kx+\phi),
```

the derivatives are

```math
\frac{\partial E_z}{\partial t}
=
-\omega A
\sin(\omega t-kx+\phi),
```

and

```math
\frac{\partial E_z}{\partial x}
=
kA
\sin(\omega t-kx+\phi).
```

Therefore,

```math
S_x
\propto
\omega k |A|^2
\sin^2(\omega t-kx+\phi).
```

Averaging over one oscillation period and using

```math
\left\langle\sin^2(\cdot)\right\rangle
=
\frac{1}{2},
```

gives

```math
\boxed{
\langle S_x\rangle
\propto
\frac{1}{2}\omega k|A|^2
}.
```

Since the factor $1/2$ is common to all waves being compared, it can be omitted when forming flux ratios. Thus,

```math
\boxed{
|\langle S_x\rangle|
\propto
\omega k|A|^2
}.
```

This explains why a field-amplitude ratio alone is not always sufficient to determine the transmitted energy fraction: the flux also depends on the wave number of the medium.

### 18.2 Reflected fraction

The incident and reflected waves both propagate in medium 1, so they have the same wave-number magnitude $k_1$.

Their flux magnitudes are proportional to

```math
|\langle S_i\rangle|
\propto
\omega k_1|A_i|^2,
```

and

```math
|\langle S_r\rangle|
\propto
\omega k_1|A_r|^2.
```

The reflected energy-flux fraction is therefore

```math
R
=
\frac{
|\langle S_r\rangle|
}{
|\langle S_i\rangle|
}.
```

The common factors cancel:

```math
R
=
\frac{|A_r|^2}{|A_i|^2}.
```

Since

```math
r=\frac{A_r}{A_i},
```

the reflected fraction is

```math
\boxed{
R=|r|^2
}.
```

The reflected flux itself travels in the negative (x) direction, but (R) is defined as a positive fraction using its magnitude.

### 18.3 Transmitted fraction

The transmitted wave propagates in medium 2, so its wave number is (k_2).

Its flux magnitude is

```math
|\langle S_t\rangle|
\propto
\omega k_2|A_t|^2.
```

Dividing by the incident flux gives

```math
T
=
\frac{
\omega k_2|A_t|^2
}{
\omega k_1|A_i|^2
}.
```

Therefore,

```math
T
=
\frac{k_2}{k_1}
\frac{|A_t|^2}{|A_i|^2}.
```

Using

```math
t=\frac{A_t}{A_i},
```

the transmitted energy-flux fraction is

```math
\boxed{
T
=
\frac{k_2}{k_1}|t|^2
}.
```

Unlike reflection, the wave number does not cancel because the incident and transmitted waves propagate in different media.

### 18.4 Expression in terms of refractive index

For the normalized nonmagnetic materials used in the simulator,

```math
c_m=\frac{1}{n_m}.
```

Since

```math
k_m
=
\frac{\omega}{c_m},
```

this gives

```math
k_m=\omega n_m.
```

Consequently,

```math
\frac{k_2}{k_1}
=
\frac{n_2}{n_1}.
```

The transmitted fraction can therefore be written as

```math
\boxed{
T
=
\frac{n_2}{n_1}|t|^2
}.
```

### 18.5 Example

For

```text
n1 = 1.0
n2 = 1.5
```

the analytical field-amplitude coefficients are

```text
r = -0.2
t = 0.8
```

The reflected fraction is

```math
R
=
|-0.2|^2
=
0.04.
```

Thus,

```text
R = 0.04
```

or (4%) of the incident scalar energy flux.

For transmission,

```math
T
=
\frac{1.5}{1.0}
|0.8|^2
=
1.5(0.64)
=
0.96.
```

Therefore,

```text
T = 0.96
```

or (96%) of the incident scalar energy flux.

The total is

```math
R+T
=
0.04+0.96
=
1.
```

Hence,

```text
R = 0.04
T = 0.96
R + T = 1.0
```

The fact that (t=0.8) but (T=0.96) illustrates the difference between **field amplitude** and **energy flux**. The transmitted field amplitude is only (80%) of the incident amplitude, but the transmitted medium has a different wave number, which changes the amount of flux associated with a given field amplitude.

### 18.6 Ideal balance and numerical monitor measurements

The exact relation

```math
R+T=1
```

applies to the ideal lossless infinite scalar plane-wave problem.

It follows from energy conservation: with no absorption or other loss mechanisms, all incident energy must leave the interface either as reflected or transmitted flux.

The current simulation, however, estimates scattering using finite field monitors rather than integrating the complete flux of an infinite plane wave.

In particular, a finite-aperture line monitor samples only part of the transverse field. It may therefore miss some energy because of:

* finite monitor extent;
* diffraction or nonuniform transverse fields;
* interference near the interface;
* numerical reflections;
* incomplete separation of incident and reflected waves;
* finite-domain and boundary effects.

For this reason, a flux estimate constructed from the current finite monitor aperture is **not required to satisfy exactly**

```math
R+T=1.
```

The analytical value provides the ideal reference, while deviations in the numerical experiment must be interpreted together with the finite geometry and measurement procedure.

---

## 19. Measured finite-aperture interpretation

The Phase 3 paired scenario recorded approximately:

```text
|r| = 0.155402
|t| = 0.637483
R = 0.024150
T = 0.609576
R + T = 0.633726
```

These values have the expected qualitative scale, but the measured sum is not
a conservation failure. The experiment includes:

- a finite source aperture;
- diffraction from the aperture ends;
- central rather than full-domain monitor apertures;
- different wavelengths and transverse spreading in the two materials;
- sponge removal of outgoing and diffracted field;
- the existing non-conservative pointwise interface discretization.

The automated simulation tests therefore require finite, positive, physically
scaled responses. Exact conservation is tested only for the analytical scalar
coefficients.

---

## 20. Source and monitor placement

Controlled experiments should place active components outside the sponge.

The general ordering for right-going interface measurement is:

```text
left sponge
    source
        upstream monitor
            interface
                downstream monitor
                    right sponge
```

The source aperture and monitor apertures should also remain away from the top
and bottom sponge layers.

Distances must allow:

1. the source ramp to complete;
2. the fully ramped wave to reach every analyzed monitor;
3. the desired reflected or transmitted signal to arrive;
4. the analysis window to contain several cycles;
5. significant outer-boundary reflections to remain outside the window.

These requirements are temporal as well as geometric.

---

## 21. Implementation mapping

Source infrastructure is implemented in:

```text
wavesim/sources.py
```

Monitor infrastructure is implemented in:

```text
wavesim/monitors.py
```

Configuration and validation are defined in:

```text
wavesim/config.py
```

Solver ownership and sampling order are defined in:

```text
wavesim/solver.py
```

Harmonic estimation is implemented in:

```text
wavesim/analysis.py
```

Source and monitor visualization is implemented in:

```text
wavesim/visualization.py
```

The official Phase 3 scenarios are:

```text
simulations/wave2d_controlled_line_source.py
simulations/wave2d_interface_measurement.py
```

---

## 22. Validation contract

The Phase 3 tests protect:

1. Exact legacy point-source behavior.
2. Post-update additive source ordering.
3. Source-profile shape, values, boundary exclusion, and immutability.
4. Half-open line-source bounds.
5. Sine-squared envelope values and continuity endpoints.
6. Monitor names, types, and half-open bounds.
7. Step-0 monitor initialization.
8. Sampling of the completed source-injected field.
9. Equal monitor and energy-history lengths.
10. Harmonic amplitude and phase conventions.
11. Controlled uniform propagation and numerical phase advance.
12. Matched reference/interface construction.
13. Incident and reflected response separation.
14. Analytical scalar interface coefficients and flux balance.
15. Finite-aperture measurement limitations.
16. Source, monitor, history, and analysis-window visualization.

---

## 23. Future controlled-source work

Possible extensions include:

- tapered transverse apertures;
- Gaussian beam profiles;
- phased line sources for angled propagation;
- one-way or total-field/scattered-field injection;
- periodic transverse boundaries;
- automatic propagation-delay estimation;
- full transverse flux monitors;
- direct time-averaged scalar flux;
- conservative interface discretization;
- PML boundaries;
- TE and TM Maxwell FDTD sources and flux monitors.

Each extension should preserve the separation between source geometry,
temporal waveform, solver evolution, field observation, and offline analysis.

---

## 24. Summary

Phase 3 replaces source-specific solver branching with reusable spatial source
profiles and adds a finite-aperture vertical line source. A sine-squared
envelope reduces abrupt startup transients while `ramp_cycles = 0` preserves
the verified point source.

Named point and coherent vertical-line monitors record the completed field at
well-defined simulation time levels. Their histories feed a separate
single-frequency harmonic estimator.

Matched reference and interface simulations permit incident and reflected
harmonic fields to be separated through linear subtraction. The resulting
finite-aperture measurements support controlled scalar-wave comparisons, but
they are not complete transverse flux integrals or exact electromagnetic
Fresnel measurements.

This distinction is central to the Phase 3 scientific contract: the project
now has controlled excitation and reproducible field measurement while keeping
its remaining physical and numerical limitations explicit.
