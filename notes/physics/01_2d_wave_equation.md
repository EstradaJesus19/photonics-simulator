# 01 — The Two-Dimensional Wave Equation

## 1. Purpose of this note

The purpose of this note is to explain the physical meaning of the wave equation used in Phase 1 of the Photonics Simulator project.

The current simulator does not yet solve the complete Maxwell equations. Instead, it solves a simplified scalar wave equation in two spatial dimensions.

This model is a useful first step for introducing:

* wave propagation,
* spatial and temporal variation,
* initial conditions,
* continuous sources,
* boundary reflections,
* absorbing layers,
* wavelength and frequency,
* energy transport,
* and numerical wave behavior.

Although the scalar wave equation is not a complete electromagnetic model, it captures several fundamental behaviors associated with waves and provides a foundation for more advanced photonics simulations.

---

## 2. The one-dimensional wave equation

The simplest scalar wave equation is the one-dimensional equation:

```math
\frac{\partial^2 u}{\partial t^2}
=
c^2
\frac{\partial^2 u}{\partial x^2}.
```

Here:

* `u(x,t)` is the scalar wave amplitude,
* `x` is position,
* `t` is time,
* `c` is the wave propagation speed.

The left-hand side:

```math
\frac{\partial^2 u}{\partial t^2}
```

describes the temporal acceleration of the field.

The right-hand side:

```math
c^2
\frac{\partial^2 u}{\partial x^2}
```

describes how the spatial curvature of the field drives this temporal acceleration.

The equation states that the field changes in time according to how it differs from its neighboring spatial values.

---

## 3. The scalar field

The variable `u` in the current simulation is a scalar field:

```math
u=u(x,y,t).
```

At every point in space and time, the field is represented by one numerical value.

This differs from a complete electromagnetic description, where the electric and magnetic fields are vector quantities:

```math
\mathbf{E}(\mathbf{r},t)
```

and:

```math
\mathbf{H}(\mathbf{r},t).
```

A vector electromagnetic field contains multiple components and directions.

For example:

```math
\mathbf{E}
=
E_x\hat{\mathbf{x}}
+
E_y\hat{\mathbf{y}}
+
E_z\hat{\mathbf{z}}.
```

The scalar variable `u` does not independently represent all components of the electric or magnetic field.

Instead, it should be interpreted as a simplified wave amplitude. Under suitable assumptions, a scalar equation can resemble the behavior of one field component, but the Phase 1 model does not yet include:

* electromagnetic polarization,
* electric-magnetic field coupling,
* vector boundary conditions,
* or the complete material relations of electromagnetism.

The scalar model is being used to establish the fundamental behavior of numerical wave propagation before introducing those additional complexities.

---

## 4. The two-dimensional wave equation

In the two-dimensional model, the field varies in the x and y directions:

```math
u=u(x,y,t).
```

The wave equation is:

```math
\frac{\partial^2 u}{\partial t^2}
=
c^2
\left(
\frac{\partial^2 u}{\partial x^2}
+
\frac{\partial^2 u}{\partial y^2}
\right).
```

Using the Laplacian operator:

```math
\nabla^2u
=
\frac{\partial^2u}{\partial x^2}
+
\frac{\partial^2u}{\partial y^2},
```

the equation can be written compactly as:

```math
u_{tt}=c^2\nabla^2u.
```

The Laplacian measures how the value of the field at one point differs from the surrounding field.

If the field is locally flat:

```math
\nabla^2u\approx0,
```

then the local temporal acceleration is small.

If the field has strong spatial curvature:

```math
\left|\nabla^2u\right|\gg0,
```

then the local temporal acceleration is stronger.

---

## 5. Why the wave equation produces propagation

The wave equation combines two essential ideas:

1. temporal inertia,
2. spatial coupling.

The second derivative in time means that the field has inertia. It does not simply adjust instantaneously to its surroundings.

Instead, the field can:

* accelerate,
* overshoot,
* reverse direction,
* and oscillate.

The spatial Laplacian couples each point to its neighbors. A local disturbance creates curvature, and that curvature causes nearby points to begin changing in time.

Those points then create curvature for their own neighbors.

This process causes a local disturbance to spread through the domain.

In a homogeneous and isotropic two-dimensional medium, a disturbance originating from a point expands approximately as a circular wavefront.

---

## 6. Propagation speed

The parameter `c` determines the wave propagation speed.

The equation is:

```math
u_{tt}=c^2\nabla^2u.
```

A larger value of `c` causes the disturbance to propagate faster through the domain.

In vacuum electromagnetism, the speed of light is approximately:

```math
c_0
\approx
3.00\times10^8\ \mathrm{m/s}.
```

In a homogeneous dielectric medium, the phase velocity can be written as:

```math
v=\frac{c_0}{n},
```

where:

* `v` is the propagation speed in the medium,
* `c_0` is the vacuum speed of light,
* `n` is the refractive index.

In the current simulation, normalized units are used:

```text
c = 1
dx = 1
dy = 1
```

Therefore, `c=1` means one simulation-length unit per simulation-time unit. It does not directly mean one meter per second.

The normalized model preserves the important relationships between:

* distance,
* time,
* speed,
* frequency,
* and wavelength.

---

## 7. Assumption of a homogeneous and isotropic medium

The current model assumes:

```math
c=\text{constant}.
```

This means the propagation speed is the same at every point in the domain.

The simulated medium is therefore homogeneous.

The propagation behavior is also assumed to be the same in every direction, so the medium is treated as isotropic.

As a result, a centered point disturbance produces approximately circular wavefronts.

More advanced photonics simulations may use a spatially varying wave speed:

```math
c=c(x,y),
```

or, equivalently, a refractive-index distribution:

```math
n=n(x,y).
```

Spatially varying material properties can produce:

* reflection,
* refraction,
* scattering,
* diffraction,
* focusing,
* guiding,
* resonance,
* and confinement.

These effects are reserved for later phases of the project.

---

## 8. Initial conditions

The wave equation is second order in time.

Therefore, a complete initial state requires both:

```math
u(x,y,0)
```

and:

```math
\left.
\frac{\partial u}{\partial t}
\right|_{t=0}.
```

The current simulator supports two initial-field configurations.

### 8.1 Gaussian initial pulse

The Gaussian initial condition is:

```math
u(x,y,0)
=
\exp
\left[
-\frac{
(x-x_0)^2+(y-y_0)^2
}{
2\sigma^2
}
\right].
```

Here:

* `(x_0,y_0)` is the pulse center,
* `\sigma` controls the pulse width.

The Gaussian is smooth and localized.

It is useful because abrupt initial profiles can contain strong high-spatial-frequency components and produce more numerical artifacts.

The initial velocity is assumed to be zero:

```math
\left.
\frac{\partial u}{\partial t}
\right|_{t=0}
=0.
```

This configuration represents a localized initial displacement released from rest.

It is useful for studying:

* free wave propagation,
* boundary reflections,
* sponge absorption,
* and the decay or conservation of an initial energy distribution.

The corresponding configuration is:

```python
initial_condition_type = "gaussian"
source_type = "none"
```

### 8.2 Zero initial field

The zero initial condition is:

```math
u(x,y,0)=0,
```

with:

```math
\left.
\frac{\partial u}{\partial t}
\right|_{t=0}
=0.
```

This means the domain begins completely at rest.

The zero initial condition is useful when a continuous source is active because all observed waves then originate from that source.

The corresponding configuration is:

```python
initial_condition_type = "zero"
source_type = "point_sine"
```

---

## 9. Continuous sinusoidal point source

The simulator supports a continuous sinusoidal source applied at one selected grid point.

Its temporal dependence is:

```math
s(t)
=
A\sin(2\pi ft),
```

where:

* `A` is the source amplitude,
* `f` is the source frequency.

The source is placed at:

```math
(x_s,y_s).
```

In the current implementation, its value is added directly to the field at that point during every time step.

A point-like source in a homogeneous and isotropic two-dimensional medium generates approximately circular outgoing wavefronts.

The source is continuous, meaning that it keeps injecting wave energy throughout the simulation.

This differs from the Gaussian initial condition, which adds energy only at the beginning.

### 9.1 Source amplitude

The amplitude `A` controls the magnitude of the excitation.

Increasing the source amplitude generally increases the wave amplitude and the energy introduced into the domain.

Because the wave equation is linear in the current Phase 1 model, multiplying the source amplitude by a constant should approximately multiply the generated field amplitude by the same constant.

### 9.2 Source frequency

The frequency `f` represents the number of source cycles per simulation-time unit.

The corresponding period is:

```math
T=\frac{1}{f}.
```

The source can therefore also be written as:

```math
s(t)
=
A\sin
\left(
\frac{2\pi t}{T}
\right).
```

For the current typical frequency:

```text
f = 0.075
```

the period is:

```math
T
=
\frac{1}{0.075}
\approx
13.33
```

simulation-time units.

### 9.3 Frequency, speed, and wavelength

For a monochromatic wave in a homogeneous medium:

```math
c=f\lambda.
```

Therefore:

```math
\lambda=\frac{c}{f}.
```

For:

```text
c = 1
f = 0.075
```

the nominal wavelength is:

```math
\lambda
=
\frac{1}{0.075}
\approx
13.33
```

simulation-length units.

The relationship between speed, frequency, and wavelength is fundamental to interpreting the source.

The word *nominal* is used because the finite-difference discretization introduces numerical dispersion. The wavelength and propagation speed observed numerically may differ slightly from their continuous-equation values.

### 9.4 Simplified nature of the source

The current point source is a numerical excitation, not a complete physical model of an electromagnetic emitter.

It does not explicitly include:

* antenna geometry,
* electric or magnetic dipole orientation,
* polarization,
* source impedance,
* radiation resistance,
* or coupling between electric and magnetic fields.

It is sufficient for Phase 1 because its purpose is to generate a controlled wave and test the propagation and boundary behavior of the scalar solver.

---

## 10. Boundary conditions

The computational domain is finite, so the simulator must define what happens when waves reach its edges.

The current model supports two boundary configurations:

* fixed boundaries,
* sponge absorbing boundaries.

---

## 11. Fixed boundary condition

The fixed boundary imposes:

```math
u=0
```

at the outermost grid points.

This is a homogeneous Dirichlet boundary condition.

It behaves conceptually like a fixed wall.

When an outgoing wave reaches the boundary, it cannot continue beyond the domain. Instead, it reflects back into the computational region.

The fixed boundary is useful for:

* demonstrating reflection,
* observing standing-wave behavior,
* studying interference,
* testing energy retention,
* and validating the difference between reflective and absorbing boundaries.

It is not suitable for approximating an infinite or open domain because the reflections are artificial when the intended physical system is unbounded.

---

## 12. Sponge absorbing layer

The sponge boundary introduces a damping region near the edges of the domain.

Inside this region, the wave equation becomes:

```math
u_{tt}
+
\gamma(x,y)u_t
=
c^2\nabla^2u.
```

The damping coefficient `\gamma(x,y)` varies spatially.

In the central physical region:

```math
\gamma(x,y)=0.
```

Near the outer edges:

```math
\gamma(x,y)>0.
```

The damping strength increases smoothly toward the boundary.

As a wave enters the sponge:

1. the wave continues propagating,
2. its amplitude decreases,
3. part of its energy is removed,
4. a smaller wave reaches the fixed outer edge,
5. and the resulting reflection is reduced.

The outermost boundary is still fixed at zero. The sponge does not replace that boundary; it attenuates waves before they reach it.

### 12.1 Why the sponge must vary smoothly

An abrupt transition from zero damping to strong damping can itself create reflection.

A gradual increase reduces this mismatch.

The current damping profile follows a power-law shape of the form:

```math
\gamma(x,y)
=
\gamma_{\max}
d(x,y)^p,
```

where:

* `\gamma_{\max}` is the maximum damping coefficient,
* `d(x,y)` is a normalized depth inside the sponge,
* `p` is the damping exponent.

A larger damping width gives the wave more distance over which to decay.

A larger maximum damping removes energy more strongly.

However, very strong or abrupt damping can produce additional reflections. Therefore, wider and smoother damping is often preferable to a very narrow and strong layer.

### 12.2 The sponge is not a PML

The sponge boundary reduces reflections, but it does not eliminate them completely.

It is not a perfectly matched layer.

A PML is designed so that, in the ideal continuous formulation, waves enter the layer without seeing an impedance mismatch at the interface.

A simple sponge does not have this exact matching property.

Therefore, partial reflections remain expected in the current simulation.

---

## 13. Expected behavior of the Gaussian pulse

### 13.1 Gaussian pulse with fixed boundaries

For:

```python
initial_condition_type = "gaussian"
source_type = "none"
boundary_type = "fixed"
```

the expected behavior is:

1. A localized Gaussian profile begins near the selected position.
2. The initial profile evolves into an outward-propagating wave.
3. The wavefront is approximately circular.
4. The amplitude changes as the disturbance spreads.
5. The wave reaches the fixed boundaries.
6. Strong reflected waves return to the center.
7. Most of the wave energy remains inside the domain.

The reflected field may interfere with itself and generate complex patterns.

### 13.2 Gaussian pulse with sponge boundaries

For:

```python
initial_condition_type = "gaussian"
source_type = "none"
boundary_type = "sponge"
```

the expected behavior is:

1. The Gaussian pulse expands outward.
2. It reaches the sponge region.
3. Its amplitude decreases progressively.
4. Much of its energy is removed.
5. Only a smaller residual reflection returns to the interior.

This configuration is the clearest current test of sponge performance because no new energy is added after initialization.

---

## 14. Expected behavior of the continuous source

### 14.1 Point source with fixed boundaries

For:

```python
initial_condition_type = "zero"
source_type = "point_sine"
boundary_type = "fixed"
```

the expected behavior is:

1. Circular waves are generated continuously.
2. Each wavefront reaches the outer boundary.
3. Strong reflections return toward the source.
4. New outgoing waves overlap with reflected waves.
5. Constructive and destructive interference occur.
6. Standing-wave-like patterns may appear.
7. The total energy stored in the domain may increase significantly.

The behavior depends on:

* source frequency,
* domain size,
* boundary geometry,
* and whether the source frequency is close to a resonant pattern of the domain.

### 14.2 Point source with sponge boundaries

For:

```python
initial_condition_type = "zero"
source_type = "point_sine"
boundary_type = "sponge"
```

the expected behavior is:

1. The source continuously generates circular wavefronts.
2. The waves propagate outward.
3. They enter the sponge region.
4. Their amplitude decreases near the edges.
5. Partial reflections remain visible.
6. Reflected waves may still interfere with new outgoing waves.
7. The total stored energy depends on the balance between source injection and sponge absorption.

This configuration demonstrates that the sponge acts as an approximate open boundary rather than a perfectly reflectionless one.

---

## 15. Energy of the scalar wave

For an ideal undamped scalar wave equation, a useful energy expression is:

```math
E(t)
=
\int_{\Omega}
\left[
\frac{1}{2}
\left(
\frac{\partial u}{\partial t}
\right)^2
+
\frac{1}{2}c^2
\left|
\nabla u
\right|^2
\right]
\,dA.
```

Here, `\Omega` is the two-dimensional domain.

The energy density is:

```math
\mathcal{E}
=
\frac{1}{2}u_t^2
+
\frac{1}{2}c^2|\nabla u|^2.
```

The first term:

```math
\frac{1}{2}u_t^2
```

is kinetic-like. It is associated with the temporal variation of the field.

The second term:

```math
\frac{1}{2}c^2|\nabla u|^2
```

is potential-like. It is associated with the spatial deformation of the field.

The gradient magnitude is:

```math
|\nabla u|^2
=
\left(
\frac{\partial u}{\partial x}
\right)^2
+
\left(
\frac{\partial u}{\partial y}
\right)^2.
```

---

## 16. Energy in the Gaussian-pulse simulation

For a Gaussian initial condition with no continuous source, the system begins with a finite initial energy.

No additional energy is deliberately added after the start.

The useful diagnostic is therefore:

```math
\frac{E(t)}{E(0)}.
```

This represents the energy remaining relative to the initial value.

### 16.1 Fixed boundary

With fixed boundaries, most energy remains in the domain.

The energy changes form and location, but it is repeatedly returned by reflection.

The numerical energy may not remain perfectly constant because of:

* finite-difference approximation,
* discrete derivative estimates,
* finite precision,
* and boundary implementation.

### 16.2 Sponge boundary

With a sponge boundary, energy decreases as the wave enters the damped region.

The damping term removes energy from the scalar field.

Therefore, the normalized energy curve provides a useful quantitative comparison between fixed and sponge boundaries.

---

## 17. Energy in the continuous-source simulation

For a zero initial field:

```math
E(0)=0.
```

A continuous source then injects energy at every time step.

Normalizing the energy using `E(0)` is impossible because it would require division by zero.

Normalizing using the first small nonzero value is also misleading because that reference is arbitrary.

Therefore, continuously driven simulations display the absolute total energy:

```math
E(t).
```

This energy may:

* increase while the domain fills with waves,
* oscillate because the source is sinusoidal,
* fluctuate because of interference,
* approach a long-term oscillatory regime,
* or continue increasing if injection exceeds absorption.

An increasing energy curve does not automatically imply numerical instability.

For a continuously driven system, increasing energy can be a physically consistent result of ongoing source excitation.

---

## 18. Energy balance in the sponge layer

The damped wave equation is:

```math
u_{tt}
+
\gamma u_t
=
c^2\nabla^2u.
```

The damping term:

```math
\gamma u_t
```

opposes temporal variation and removes energy from the wave.

Conceptually, the energy balance includes:

* energy stored in the field,
* energy transported through the domain,
* energy added by a source,
* and energy dissipated by the sponge.

For a continuously driven sponge simulation, the long-term behavior depends on the competition between:

```text
source injection
```

and:

```text
sponge dissipation.
```

If they approximately balance, the energy may fluctuate around a bounded average.

If the source adds energy faster than the sponge removes it, the stored energy may continue increasing.

---

## 19. Wave spreading in two dimensions

A point-like source in two dimensions generates expanding circular wavefronts.

As the circumference of the wavefront increases, the same wave energy is distributed over a larger spatial region.

This causes the amplitude to decrease with distance even in a lossless medium.

For an ideal outgoing cylindrical wave, the far-field amplitude approximately behaves as:

```math
|u(r)|
\propto
\frac{1}{\sqrt{r}},
```

where `r` is the radial distance from the source.

This differs from a three-dimensional spherical wave, whose amplitude typically decreases approximately as:

```math
\frac{1}{r}.
```

The current simulation is two-dimensional, so its spreading behavior should not be interpreted directly as the radiation of a three-dimensional point emitter.

---

## 20. Interference

Because the scalar wave equation is linear, multiple waves add through superposition.

If two waves overlap:

```math
u_{\mathrm{total}}
=
u_1+u_2.
```

When the waves have the same sign at a point, they interfere constructively.

When they have opposite signs, they interfere destructively.

In the current simulator, interference occurs between:

* successive wavefronts from the continuous source,
* outgoing and reflected waves,
* and reflections from different sides of the domain.

The complex patterns observed with fixed boundaries are therefore not random. They result from the superposition of multiple coherent wave contributions.

---

## 21. Standing-wave-like behavior and resonances

When waves are reflected repeatedly inside a finite domain, some frequency patterns can reinforce themselves.

A standing wave can be represented conceptually as the superposition of two waves traveling in opposite directions:

```math
u_1(x,t)
=
A\cos(kx-\omega t),
```

and:

```math
u_2(x,t)
=
A\cos(kx+\omega t).
```

Their sum is:

```math
u(x,t)
=
2A\cos(kx)\cos(\omega t).
```

This pattern oscillates in time while retaining fixed spatial nodes and antinodes.

The two-dimensional square domain has more complicated modal patterns, but the same principle applies.

A continuously driven fixed-boundary simulation may excite cavity-like modes, especially when the source frequency overlaps with one of the natural numerical-domain resonances.

The current Phase 1 solver does not explicitly calculate eigenmodes, but standing-wave-like interference may appear visually.

---

## 22. Frequency and temporal sampling

The continuous source is evaluated at discrete time steps.

The time interval is:

```math
\Delta t.
```

The temporal sampling frequency is:

```math
f_s=\frac{1}{\Delta t}.
```

The Nyquist frequency is:

```math
f_{\mathrm{Nyquist}}
=
\frac{1}{2\Delta t}.
```

The source frequency must remain below the Nyquist frequency to avoid temporal aliasing:

```math
f<f_{\mathrm{Nyquist}}.
```

For:

```text
dt = 0.4
```

the Nyquist frequency is:

```math
f_{\mathrm{Nyquist}}
=
\frac{1}{0.8}
=
1.25.
```

The current typical value:

```text
f = 0.075
```

is well below that limit.

The number of time steps per source period is:

```math
N_T
=
\frac{1}{f\Delta t}.
```

For:

```text
f = 0.075
dt = 0.4
```

this gives:

```math
N_T
\approx
33.33.
```

Therefore, each oscillation is represented by approximately 33 time steps.

---

## 23. Spatial wavelength resolution

A continuous wave must also be resolved by enough spatial grid points.

The nominal wavelength is:

```math
\lambda=\frac{c}{f}.
```

The number of x-grid points per wavelength is:

```math
N_{\lambda,x}
=
\frac{\lambda}{\Delta x}.
```

The number of y-grid points per wavelength is:

```math
N_{\lambda,y}
=
\frac{\lambda}{\Delta y}.
```

For the typical values:

```text
c = 1
f = 0.075
dx = 1
dy = 1
```

the number of points per wavelength is approximately:

```math
N_{\lambda,x}
=
N_{\lambda,y}
\approx
13.33.
```

This is usable for the current Phase 1 simulations.

However, it does not eliminate numerical dispersion.

Using fewer points per wavelength can cause:

* incorrect propagation speed,
* phase error,
* distorted wavefronts,
* artificial directional dependence,
* and inaccurate interference patterns.

The current program warns when the source wavelength has fewer than 10 grid points.

This is a practical heuristic rather than a strict universal threshold.

---

## 24. Numerical dispersion and anisotropy

The continuous equation predicts a propagation speed `c` that is independent of wavelength and direction in the homogeneous medium.

The numerical grid only approximates the continuous equation.

As a result, the simulated propagation speed can depend slightly on:

* wavelength,
* grid spacing,
* time step,
* and direction relative to the Cartesian grid.

This effect is called numerical dispersion.

A related effect is numerical anisotropy.

Although the physical medium is isotropic, the square numerical grid has preferred axis and diagonal directions.

Therefore, a nominally circular wavefront may develop small grid-related distortions.

These errors are reduced by:

* increasing the number of points per wavelength,
* using smaller spatial steps,
* using an appropriate time step,
* and eventually using higher-order or alternative numerical methods.

---

## 25. Stability and physical interpretation

The explicit finite-difference method requires a stable relationship between:

* propagation speed,
* time step,
* and grid spacing.

For the current two-dimensional method:

```math
c\Delta t
\sqrt{
\frac{1}{\Delta x^2}
+
\frac{1}{\Delta y^2}
}
\leq1.
```

If this condition is violated, the numerical field can grow rapidly without physical meaning.

Signs of instability include:

* uncontrolled amplitude growth,
* checkerboard patterns,
* overflow,
* `nan` values,
* and `inf` values.

A source-driven simulation requires careful interpretation because its energy can grow physically due to continuous excitation.

The distinction is that numerical instability normally causes rapid, unstructured growth unrelated to the expected source-generated wave pattern.

---

## 26. Normalized units

The Phase 1 simulator uses normalized units.

Typical parameters are:

```python
c = 1.0
dx = 1.0
dy = 1.0
dt = 0.4
```

These values do not correspond directly to SI units.

The model should therefore be interpreted through dimensionless or normalized relationships.

For example:

```math
\lambda=\frac{c}{f}
```

remains valid.

Likewise:

```math
\text{distance}
=
c\times\text{time}
```

remains meaningful in simulation units.

Normalized units allow the project to focus first on the numerical and physical structure of the model.

A future physical-unit implementation would require a consistent definition of:

* length units,
* time units,
* physical frequency,
* propagation speed,
* wavelength,
* refractive index,
* and material properties.

---

## 27. Relationship to electromagnetic waves

In a homogeneous, source-free, nonconducting medium, Maxwell's equations can lead to wave equations for electric and magnetic field components.

For example, under suitable assumptions:

```math
\nabla^2\mathbf{E}
-
\mu\epsilon
\frac{\partial^2\mathbf{E}}{\partial t^2}
=
0.
```

This can be rearranged as:

```math
\frac{\partial^2\mathbf{E}}{\partial t^2}
=
\frac{1}{\mu\epsilon}
\nabla^2\mathbf{E}.
```

The corresponding wave speed is:

```math
v
=
\frac{1}{\sqrt{\mu\epsilon}}.
```

This resembles the scalar equation:

```math
u_{tt}=c^2\nabla^2u.
```

However, the scalar model does not automatically reproduce the full content of Maxwell's equations.

A complete electromagnetic solver must account for:

* vector components,
* curl relations,
* divergence constraints,
* electric and magnetic coupling,
* material permittivity,
* material permeability,
* conductivity,
* polarization,
* and electromagnetic boundary conditions.

Therefore, the Phase 1 scalar model should be understood as preparation for electromagnetic simulation, not as a substitute for it.

---

## 28. Current physical limitations

The Phase 1 wave model has the following intentional limitations:

* The field is scalar.
* The medium is homogeneous.
* The medium is isotropic.
* The wave speed is constant.
* No material interfaces are included.
* No refractive-index map is included.
* No polarization is represented.
* Electric and magnetic fields are not evolved separately.
* The source is a simplified numerical point excitation.
* The fixed boundary is strongly reflective.
* The sponge is not perfectly matched.
* The simulation uses normalized units.
* Numerical dispersion remains present.
* Two-dimensional spreading differs from physical three-dimensional radiation.
* No nonlinear effects are included.
* No frequency-dependent material dispersion is included.

These limitations are appropriate for Phase 1 because the objective is to establish and validate the basic wave-simulation framework.

---

## 29. What Phase 1 currently demonstrates

The current Phase 1 simulator successfully demonstrates:

* propagation from a localized initial disturbance,
* circular waves from a continuous point source,
* the relationship between speed, frequency, and wavelength,
* strong reflection from fixed boundaries,
* reduced reflection using a sponge layer,
* interference between outgoing and reflected waves,
* energy retention in a reflective domain,
* energy loss in a damped domain,
* continuous energy injection by a source,
* wavelength-resolution requirements,
* and the distinction between stable and unstable numerical behavior.

These results provide both physical and numerical evidence that the solver is behaving consistently with its intended model.

---

## 30. Summary

The two-dimensional scalar wave equation used in Phase 1 is:

```math
\frac{\partial^2u}{\partial t^2}
=
c^2
\left(
\frac{\partial^2u}{\partial x^2}
+
\frac{\partial^2u}{\partial y^2}
\right).
```

It describes how the temporal acceleration of a scalar field is determined by its spatial curvature.

The current simulator supports:

* a Gaussian initial pulse,
* a zero initial field,
* a continuous sinusoidal point source,
* fixed reflective boundaries,
* a sponge absorbing layer,
* field animation,
* and energy diagnostics.

For a Gaussian pulse without a source, normalized energy:

```math
\frac{E(t)}{E(0)}
```

measures how much of the initial energy remains.

For a continuously driven source, absolute energy:

```math
E(t)
```

is more meaningful because the source keeps injecting energy.

The source frequency and nominal wavelength are related by:

```math
c=f\lambda.
```

The fixed boundary produces strong reflections, while the sponge reduces them by gradually damping outgoing waves.

The model is not yet a complete electromagnetic solver. It is a simplified physical layer designed to establish the essential concepts needed for later photonics and Maxwell-equation simulations.
