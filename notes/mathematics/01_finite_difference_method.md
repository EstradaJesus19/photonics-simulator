# 01 — Finite Difference Method

## 1. Purpose of this note

The purpose of this note is to understand how the continuous 2D wave equation can be transformed into a numerical algorithm that a computer can execute.

The physical equation used in Phase 1 is:

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

This equation is continuous in space and time. That means that, in theory, the field is defined for every possible value of:

```math
x, y, t
```

The finite difference method replaces derivatives with algebraic approximations using neighboring grid values.

---

## 2. From continuous space to a grid

In the continuous model, the wave field is written as:

```math
u(x,y,t)
```

In the numerical model, space is divided into a rectangular grid.

The grid points are:

```math
x_i = i \Delta x
```

```math
y_j = j \Delta y
```

where:

- $i$ is the grid index in the x direction,
- $j$ is the grid index in the y direction,
- $\Delta x$ is the grid spacing in x,
- $\Delta y$ is the grid spacing in y.

Instead of storing the field everywhere, the computer stores the field only at grid points:

```math
u(x_i, y_j, t)
```

This is written more compactly as:

```math
u_{i,j}(t)
```

In the Python code, this is represented by a 2D NumPy array:

```python
u_curr[i, j]
```

Each element of the array corresponds to one spatial point.

---

## 3. From continuous time to time steps

Time is also discretized.

The time points are:

```math
t^n = n \Delta t
```

where:

- `n` is the time-step index,
- `\Delta t` is the time step.

The numerical approximation of the field is then written as:

```math
u_{i,j}^n
```

This means, the value of the field at grid point `(i,j)` and time step `n`.

In the code, the time levels are stored as:

```python
u_prev
u_curr
u_next
```

which correspond to: $u_{i,j}^{n-1}$, $u_{i,j}^{n}$ and $u_{i,j}^{n+1}$, respectively.

---

## 4. Why finite differences are needed

The wave equation contains derivatives that cannot be directly evaluated. Instead, the finite difference method approximates derivatives using nearby values on the grid. For example, the spatial derivative in the x direction depends on the values $u_{i,j}^{n-1}$, $u_{i,j}^{n}$ and $u_{i,j}^{n+1}$.
So the derivative at one point is estimated using its neighboring points.

---

## 5. First derivative intuition

The first derivative of a function measures slope.

For a function `f(x)`, the derivative is defined as:

```math
\frac{df}{dx}
=
\lim_{\Delta x \to 0}
\frac{f(x+\Delta x)-f(x)}{\Delta x}
```

In a numerical grid, `\Delta x` is not zero. It is a small finite spacing.

So a simple finite difference approximation is:

```math
\frac{df}{dx}
\approx
\frac{f(x+\Delta x)-f(x)}{\Delta x}
```

This is called a forward difference.

Another possibility is:

```math
\frac{df}{dx}
\approx
\frac{f(x)-f(x-\Delta x)}{\Delta x}
```

This is called a backward difference.

A more symmetric approximation is:

```math
\frac{df}{dx}
\approx
\frac{f(x+\Delta x)-f(x-\Delta x)}{2\Delta x}
```

This is called a central difference.

For wave simulations, central differences are very common because they are more symmetric and usually more accurate.

---

## 6. Second derivative in one dimension

The wave equation uses second derivatives. The second derivative measures curvature. For one spatial dimension, the central finite difference approximation is:

```math
\frac{\partial^2 u}{\partial x^2}
\approx
\frac{
u_{i+1} - 2u_i + u_{i-1}
}{
\Delta x^2
}
```

This formula compares the value at the current point with the values at its two neighboring points. If the current point is larger than its neighbors, the curvature is negative. If the current point is smaller than its neighbors, the curvature is positive. If the field is locally linear or flat, the curvature is close to zero.

---

## 7. Second derivative in time

The same central difference idea is used for the second derivative in time. The second time derivative is approximated by:

```math
\frac{\partial^2 u}{\partial t^2}
\approx
\frac{
u_{i,j}^{n+1}
-
2u_{i,j}^{n}
+
u_{i,j}^{n-1}
}{
\Delta t^2
}
```

This expression uses three time levels:

- the future value,
- the current value,
- the previous value.

The wave equation is second order in time, so one current state is not enough. The numerical method needs information from the current and previous states to compute the next state.

---

## 8. The 2D Laplacian

In two dimensions, the Laplacian is:

```math
\nabla^2 u
=
\frac{\partial^2 u}{\partial x^2}
+
\frac{\partial^2 u}{\partial y^2}
```

Using finite differences:

```math
\frac{\partial^2 u}{\partial x^2}
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
```

and

```math
\frac{\partial^2 u}{\partial y^2}
\approx
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

Therefore:

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

This is the discrete Laplacian used in the simulation.

---

## 9. The finite-difference update rule

The continuous 2D wave equation is:

```math
\frac{\partial^2 u}{\partial t^2}
=
c^2 \nabla^2 u
```

Substitute the finite-difference approximations:

```math
\frac{
u_{i,j}^{n+1}
-
2u_{i,j}^{n}
+
u_{i,j}^{n-1}
}{
\Delta t^2
}
=
c^2
\nabla^2 u_{i,j}^{n}
```

Now solve for the future value:

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

This is the central update rule of the simulation.

In the Python code, this appears as:

```python
u_next = 2 * u_curr - u_prev + (c * dt) ** 2 * laplacian
```

This line is the numerical version of the wave equation.

It computes the next field using:

- the current field,
- the previous field,
- the spatial curvature of the current field,
- the wave speed,
- and the time step.

---

## 10. Interpretation of the update rule

The update rule is:

```math
u^{n+1}
=
2u^n
-
u^{n-1}
+
c^2 \Delta t^2 \nabla^2 u^n
```

The term:

```math
2u^n - u^{n-1}
```

continues the current temporal motion of the field.

The term:

```math
c^2 \Delta t^2 \nabla^2 u^n
```

adds the effect of spatial curvature.

So the next state is determined by two ideas:

1. The field has inertia in time.
2. The field is affected by spatial curvature.

This is why a local pulse propagates outward instead of simply disappearing.

---

## 11. Connection to the code implementation

The discrete Laplacian is implemented as:

```python
laplacian = (
    (np.roll(u_curr, 1, axis=0) - 2 * u_curr + np.roll(u_curr, -1, axis=0)) / dx**2
    + (np.roll(u_curr, 1, axis=1) - 2 * u_curr + np.roll(u_curr, -1, axis=1)) / dy**2
)
```

The terms:

```python
np.roll(u_curr, 1, axis=0)
np.roll(u_curr, -1, axis=0)
```

represent neighbors in the x direction.

The terms:

```python
np.roll(u_curr, 1, axis=1)
np.roll(u_curr, -1, axis=1)
```

represent neighbors in the y direction.

Together, these terms approximate:

```math
\frac{\partial^2 u}{\partial x^2}
+
\frac{\partial^2 u}{\partial y^2}
```

Then the next field is calculated with:

```python
u_next = 2 * u_curr - u_prev + (c * dt) ** 2 * laplacian
```

Finally, the time states are shifted:

```python
u_prev, u_curr = u_curr, u_next.copy()
```

This means:

- the old current field becomes the previous field,
- the newly calculated field becomes the current field,
- the simulation advances by one time step.

---

## 12. Important note about `np.roll`

Using `np.roll` is convenient because it shifts the array automatically. However, `np.roll` has an important behavior: It wraps values from one side of the array to the opposite side. For example, when shifting an array to the right, values from the right edge reappear on the left edge. This is similar to a periodic boundary condition. In the current code, the boundaries are manually overwritten afterward:

```python
u_next[0, :] = 0
u_next[-1, :] = 0
u_next[:, 0] = 0
u_next[:, -1] = 0
```

This reduces the unwanted wraparound effect at the edges for the updated field. However, for future simulations, it is better to compute the Laplacian only on the interior points and handle boundaries explicitly.

---

## 13. Grid resolution

The grid spacing `\Delta x` and `\Delta y` control the spatial resolution. A smaller grid spacing gives a more detailed simulation, but it requires more grid points and more computation. If the grid is too coarse, the wave may appear distorted. This is called _numerical dispersion_.

Numerical dispersion means that the simulated wave speed depends incorrectly on wavelength or direction because of discretization errors. A good rule of thumb is to use many grid points per wavelength.

---

## 14. Time step and stability

The time step `\Delta t` controls how far the simulation advances in each update. A larger time step makes the simulation faster, but it can make the simulation unstable. For the 2D wave equation, the time step must satisfy a stability condition called the _CFL condition_.

For equal grid spacing:

```math
\Delta x = \Delta y
```

a common condition is:

```math
\frac{c \Delta t}{\Delta x}
\leq
\frac{1}{\sqrt{2}}
```

More generally:

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

The quantity:

```math
S =
c \Delta t
\sqrt{
\frac{1}{\Delta x^2}
+
\frac{1}{\Delta y^2}
}
```

is related to the Courant number. If this number is too large, the simulation becomes unstable.

In the code:

```python
courant = c * dt * np.sqrt(1 / dx**2 + 1 / dy**2)

if courant > 1:
    raise ValueError("Simulation unstable: reduce dt or increase dx/dy.")
```

This prevents the simulation from running with parameters that are likely unstable.

---

## 15. What numerical instability looks like

When the stability condition is violated, the simulation does not simply become slightly inaccurate. Usually, the field amplitude grows rapidly and artificially. Signs of numerical instability include:

- amplitudes increasing without physical reason,
- the plot becoming dominated by extreme values,
- checkerboard-like patterns,
- overflow warnings,
- `nan` or `inf` values in the array,
- the animation becoming meaningless.

This happens because the numerical update amplifies errors instead of propagating the wave correctly. Stability is one of the most important concepts in time-domain simulations.

---

## 16. Accuracy versus stability

Stability and accuracy are related but not identical. A simulation can be stable but still inaccurate. A stable simulation does not blow up, but it may still have:

- numerical dispersion,
- phase errors,
- artificial anisotropy,
- boundary artifacts,
- insufficient resolution.

Accuracy improves when:

- the grid spacing is smaller,
- the time step is chosen carefully,
- the boundary conditions are appropriate,
- the numerical scheme matches the physical problem,
- the results are validated against known solutions.

Therefore, satisfying the CFL condition is necessary, but not sufficient for a high-quality simulation.

---

## 17. Boundary treatment in finite differences

Finite-difference formulas need neighboring points.

For an interior point, this is easy because all neighbors exist:

```text
u[i+1,j]
u[i-1,j]
u[i,j+1]
u[i,j-1]
```

At a boundary, some neighbors are outside the simulation domain. For example, at the left boundary, `u[i-1,j]` does not exist. Therefore, boundary conditions are needed. Common boundary types include:

- Dirichlet boundary condition: the field value is fixed.
- Neumann boundary condition: the field derivative is fixed.
- Periodic boundary condition: one edge connects to the opposite edge.
- Absorbing boundary condition: waves are damped to reduce reflections.
- Perfectly matched layer: advanced absorbing boundary used in electromagnetic simulations.

In the first simulation, a simple Dirichlet boundary is used:

```math
u = 0
```

at the edges.

This is easy to implement, but it creates reflections.

---

## 18. Normalized units

The first simulation uses normalized units.

For example:

```python
c = 1.0
dx = 1.0
dy = 1.0
dt = 0.4
```

Normalized units are useful because they simplify the first implementation. Later, the simulation can be connected to physical units by defining:

- real spatial dimensions,
- real time scales,
- wavelength,
- frequency,
- refractive index,
- physical speed of light.

For the first phase, normalized units are acceptable because the main goal is to understand wave propagation and numerical behavior.

---

## 19. Computational cost

The simulation stores the field as arrays of size:

```math
N_x \times N_y
```

For example, a grid with:

```python
nx = 150
ny = 150
```

contains:

```math
150 \times 150 = 22500
```

grid points.

At every time step, the code updates all grid points.

Therefore, the computational cost per time step is approximately proportional to:

```math
N_x N_y
```

If the grid size doubles in both directions:

```math
N_x \to 2N_x
```

```math
N_y \to 2N_y
```

then the number of grid points increases by a factor of four.

This is important because higher resolution improves accuracy but increases computation time.

---

## 20. Summary

The finite difference method transforms the continuous wave equation into a numerical update rule. The continuous equation is:

```math
\frac{\partial^2 u}{\partial t^2}
=
c^2 \nabla^2 u
```

The discrete update rule is:

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

The discrete Laplacian is:

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

In code, this becomes:

```python
u_next = 2 * u_curr - u_prev + (c * dt) ** 2 * laplacian
```

This line is the core of the first numerical solver.

The method works by repeatedly computing the next state of the wave field from the current state, the previous state, and the spatial curvature.

The main concepts introduced are:

- grid discretization,
- time stepping,
- central differences,
- the discrete Laplacian,
- CFL stability,
- boundary handling,
- numerical accuracy,
- and the connection between mathematical equations and executable code.

This finite-difference method is the mathematical foundation of Phase 1 of the Photonics Simulator project.