# 01 — The Wave Equation

## 1. Purpose of this note

The purpose of this note is to understand the physical meaning of the wave equation used in the first phase of the Photonics Simulator project.

In Phase 1, the simulator does not yet solve the full Maxwell equations. Instead, it solves a simplified scalar wave equation in two spatial dimensions. This is a useful first for introducing the ideas behind wave propagation, numerical discretization, boundary conditions, and visualization.

The scalar wave equation is not a complete electromagnetic model, but it captures one of the most important behaviors of light and electromagnetic fields.

---

## 2. The one-dimensional wave equation

The simplest wave equation is the one-dimensional scalar wave equation:

```math
\frac{\partial^2 u}{\partial t^2}
=
c^2
\frac{\partial^2 u}{\partial x^2}
```

where:

- $u(x,t)$ is the wave amplitude.
- $x$ is position.
- $t$ is time.
- $c$ is the wave propagation speed.

The left-hand side,

```math
\frac{\partial^2 u}{\partial t^2}
```

describes how the field accelerates in time.

The right-hand side,

```math
c^2
\frac{\partial^2 u}{\partial x^2}
```

describes how the spatial curvature of the field affects its motion.

In physical terms, the field changes in time because neighboring points in space interact through the field curvature.

---

## 3. The field variable

In this first simulation, the quantity `u` is a scalar field.That means that at every point in space, the field has only one value:

```math
u = u(x,y,t)
```

This is different from a full electromagnetic field, where the electric and magnetic fields are vector quantities ($\mathbf{E}(x,y,t)$ and $\mathbf{H}(x,y,z,t)$)

In Phase 1, `u` represents a simplified wave amplitude that behaves similarly to one component of an electromagnetic field.

---

## 4. The two-dimensional wave equation

For a two-dimensional simulation, the wave can vary in both the `x` and `y` directions.

The 2D scalar wave equation is:

```math
\frac{\partial^2 u}{\partial t^2}
=
c^2
\left(
\frac{\partial^2 u}{\partial x^2}
+
\frac{\partial^2 u}{\partial y^2}
\right)
```

This can also be written using the Laplacian operator:

```math
\frac{\partial^2 u}{\partial t^2}
=
c^2 \nabla^2 u
```

where in two dimensions:

```math
\nabla^2 u
=
\frac{\partial^2 u}{\partial x^2}
+
\frac{\partial^2 u}{\partial y^2}
```

The Laplacian measures the local spatial curvature of the field. If a point is much higher or lower than its neighbors, the Laplacian is large. This produces a stronger change in time. If the field is locally flat, the Laplacian is small. This means the field changes more slowly.

---

## 5. Why the wave equation produces propagation

The wave equation combines two effects:

1. Inertia in time.
2. Coupling between neighboring points in space.

The second time derivative means that the field has a kind of inertia. The field does not simply relax instantly. Instead, it overshoots, oscillates, and propagates.

The spatial second derivative means that each point is influenced by neighboring points.

Together, these effects create wave motion.

A local disturbance does not remain fixed. It spreads outward because each point affects its neighbors, and those neighbors affect their neighbors.

In two dimensions, a localized pulse spreads approximately as a circular wavefront if the medium is uniform.

---

## 6. Propagation speed

The parameter `c` controls how fast the wave propagates.

In the equation:

```math
\frac{\partial^2 u}{\partial t^2}
=
c^2 \nabla^2 u
```

larger values of `c` produce faster waves.

In electromagnetics, the wave speed in vacuum is the speed of light:

```math
c_0 \approx 3 \times 10^8 \ \text{m/s}
```

In a material medium, light travels more slowly:

```math
v = \frac{c_0}{n}
```

where:

- `v` is the speed of light in the medium,
- `c_0` is the speed of light in vacuum,
- `n` is the refractive index.

For the Phase 1, normalized units are used:

```text
c = 1
dx = 1
dy = 1
```

This means the simulation is not using physical SI units. Instead, it is focused on the qualitative behavior of waves.

---

## 7. Assumption of a homogeneous medium

The first simulation assumes that the wave speed is the same everywhere:

```math
c = \text{constant}
```

This means the simulated medium is homogeneous.

A homogeneous medium has the same properties at every point in space. Because of this, the wavefront expands symmetrically.

In photonics, this is only the simplest case.

More interesting systems involve spatially varying material properties, for example $c = c(x,y)$ (or equivalently $n = n(x,y)$, where `n` is the refractive index).

When the refractive index varies in space, waves can:

- reflect,
- refract,
- scatter,
- interfere,
- become guided,
- or become confined.

## 8. Initial condition

To start a wave simulation, it is necessary to define the initial state of the field.

In the first simulation, the initial condition is a Gaussian pulse centered in the domain:

```math
u(x,y,0)
=
\exp
\left(
-\frac{(x-x_0)^2 + (y-y_0)^2}{2\sigma^2}
\right)
```

where:

- `(x0, y0)` is the center of the pulse,
- `\sigma` controls the width of the pulse.

A Gaussian pulse is useful because it is smooth and localized.

A sharp initial condition could create strong numerical artifacts. A smooth Gaussian is numerically better behaved and easier to visualize.

The pulse spreads outward because the wave equation converts the initial spatial curvature into time evolution.

---

## 9. Boundary conditions

The first simulation uses fixed zero boundary conditions:

```math
u = 0
```

on the edges of the simulation domain.

This means the field is forced to be zero at the boundary.

Physically, this behaves somewhat like a fixed wall. When the wave reaches the boundary, part of it reflects back into the domain.

This is not ideal if one wants to simulate open space, because in open space the wave should continue traveling outward instead of reflecting.

However, fixed boundaries are useful for a first simulation because they are simple to implement.

---

## 10. Energy intuition

For an ideal wave equation in an infinite or closed lossless domain, wave energy is conserved.

The energy is exchanged between:

- kinetic-like energy related to the time variation of the field,
- potential-like energy related to spatial gradients of the field.

A useful conceptual expression is:

```math
\text{Energy density}
\sim
\left(
\frac{\partial u}{\partial t}
\right)^2
+
c^2 |\nabla u|^2
```

The first term is associated with temporal motion.

The second term is associated with spatial deformation of the field.

In the simple numerical simulation, energy may not be perfectly conserved because of:

- numerical approximation errors,
- boundary reflections,
- finite grid resolution,
- time discretization.

---

## 11. What should be observed in the first simulation

For the first 2D simulation, the expected behavior is:

1. A localized pulse starts at the given coordinates (usually, the center).
2. The pulse expands outward.
3. The wavefront is approximately circular.
4. The amplitude changes as the wave spreads.
5. The wave eventually reaches the boundaries.
6. Reflections appear because of the fixed boundary conditions.

If the simulation becomes unstable, the field may grow rapidly without physical meaning. This usually means that the time step is too large for the chosen spatial grid.

---

## 12. Summary

The 2D scalar wave equation describes how a scalar disturbance propagates through space over time.

The equation used in Phase 1 is:

```math
\frac{\partial^2 u}{\partial t^2}
=
c^2
\left(
\frac{\partial^2 u}{\partial x^2}
+
\frac{\partial^2 u}{\partial y^2}
\right)
```

This equation states that the acceleration of the field is proportional to its spatial curvature.

In the current project, this equation is used as a simplified model for wave propagation. It does not yet represent the full electromagnetic behavior of light, but it provides an essential foundation for understanding numerical wave simulation.

The main ideas introduced by this model are:

- wave propagation,
- spatial curvature,
- finite propagation speed,
- initial conditions,
- boundary conditions,
- numerical time stepping,
- and the connection between physics and simulation.

This is the first physical layer of the Photonics Simulator project.