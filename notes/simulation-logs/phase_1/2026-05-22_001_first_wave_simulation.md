# 2026-05-22 — First 2D Wave Simulation

## 1. Goal

The goal of this session was to implement the first working 2D scalar wave equation simulation.

The simulation should show a localized pulse propagating outward on a two-dimensional grid.

---

## 2. Context

This work belongs to Phase 1 of the Photonics Simulator project.

The objective of Phase 1 is to build a simple finite-difference simulation based on the scalar wave equation:

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

This is a simplified model of wave propagation. It does not yet solve the full Maxwell equations, but it introduces the numerical structure needed for later electromagnetic simulations.

---

## 3. Files created or modified

The main file for this session is:

```text
simulations/wave2d_basic.py
```

Related documentation files:

```text
notes/physics/01_wave_equation.md
notes/mathematics/01_finite_differences.md
notes/simulation_logs/phase_1/2026-05-22_002_first_wave_simulation.md
```

---

## 4. Numerical model

The continuous equation is:

```math
\frac{\partial^2 u}{\partial t^2}
=
c^2 \nabla^2 u
```

The finite-difference update rule is:

```math
u_{i,j}^{n+1}
=
2u_{i,j}^{n}
-
u_{i,j}^{n-1}
+
c^2 \Delta t^2
\nabla^2 u_{i,j}^{n}
```

The discrete Laplacian is approximated by:

```math
\nabla^2 u_{i,j}^{n}
\approx
\frac{
u_{i+1,j}^{n}
-
2u_{i,j}^{n}
+
u_{i-1,j}^{n}
}{
\Delta x^2
}
+
\frac{
u_{i,j+1}^{n}
-
2u_{i,j}^{n}
+
u_{i,j-1}^{n}
}{
\Delta y^2
}
```

In Python, the core update is:

```python
u_next = 2 * u_curr - u_prev + (c * dt) ** 2 * laplacian
```

---

## 5. Parameters used

Initial parameters:

```text
nx = 150
ny = 150
dx = 1.0
dy = 1.0
c = 1.0
dt = 0.4
steps = 500
```

Initial condition:

```text
Gaussian pulse centered in the simulation domain.
```

Gaussian parameters:

```text
x0 = nx // 2
y0 = ny // 2
sigma = 8.0
```

Boundary condition:

```text
Fixed zero-value boundary condition.
```

This means:

```math
u = 0
```

at the edges of the simulation domain.

---

## 6. Stability check

The simulation uses a CFL stability check:

```math
c \Delta t
\sqrt{
\frac{1}{\Delta x^2}
+
\frac{1}{\Delta y^2}
}
\leq
1
```

For the initial parameters:

```math
c = 1.0
```

```math
\Delta t = 0.4
```

```math
\Delta x = \Delta y = 1.0
```

The Courant value is:

```math
1.0 \cdot 0.4 \cdot \sqrt{1 + 1}
=
0.4\sqrt{2}
\approx
0.566
```

Since:

```math
0.566 < 1
```

the simulation is expected to be stable.

---

## 7. Results observed

Expected observations:

1. The simulation starts with a smooth pulse at the center of the grid.
2. The pulse expands outward.
3. The wavefront is approximately circular.
4. Positive and negative field amplitudes appear as the wave evolves.
5. The wave eventually reaches the edges of the domain.
6. Reflections appear at the boundaries because the field is forced to zero there.

Actual observations:

```text
The pulse propagated outward from the center as expected. The wavefront remained approximately circular in the central region. When the wave reached the boundary, reflections appeared and traveled back into the domain.
```

---

## 8. Interpretation

The outward motion of the pulse confirms that the finite-difference update is producing wave-like behavior.

The circular wavefront is expected because the medium is homogeneous and the grid spacing is equal in both directions.

The boundary reflections are also expected because the simulation currently uses fixed zero-value boundaries.

This confirms that the simulation is qualitatively consistent with the scalar wave equation.

---

## 9. Problems or limitations

Current limitations:

1. The simulation uses a scalar field instead of vector electromagnetic fields.
2. The medium is homogeneous.
3. The wave speed is constant.
4. The boundaries are reflective.
5. The simulation uses normalized units.
6. The initial version does not include a continuous source.
7. The simulation does not include material interfaces.
8. The current implementation may need improved boundary handling.

Important numerical note:

Using `np.roll` is convenient, but it can introduce periodic-like behavior because array values wrap around at the edges. The boundary values are overwritten after the update, but a more careful implementation should compute the Laplacian only on interior points.

---

## 10. Decisions made

The following decisions were made:

1. Use a Gaussian pulse as the initial condition.
2. Use fixed zero-value boundary conditions for simplicity.
3. Use normalized units for the first implementation.
4. Use Matplotlib animation for visualization.
5. Start with a scalar wave model before implementing Maxwell/FDTD.
6. Keep the first simulation simple and readable.

---

## 11. Next steps

Possible next steps:

1. Replace the `np.roll` Laplacian with an explicit interior-grid Laplacian.
2. Add a damping layer near the boundaries.
3. Add parameter experiments for `dt`, `dx`, `c`, and `sigma`.
4. Add a continuous sinusoidal source.
5. Save example figures or animations.
6. Add a refractive-index region.
7. Compare behavior with expected wave propagation.

The immediate next step should be:

```text
Replace the np.roll-based Laplacian with an explicit finite-difference implementation using array slicing.
```