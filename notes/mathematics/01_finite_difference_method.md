# 01 — Finite Difference Method

> **Status:** Foundational Phase 1 note, with discrete-energy implementation
> details verified through Phase 5.1.
>
> **Scope:** The core derivation uses the homogeneous scalar wave equation.
> Later phases retain the same finite-difference stencil while adding spatial
> material maps, controlled sources, field and flux monitors, harmonic
> analysis, and a leapfrog-consistent energy diagnostic.

## 1. Purpose of this note

The purpose of this note is to explain how the continuous two-dimensional scalar wave equation is transformed into a numerical algorithm that a computer can execute.

The physical equation used in Phase 1 of the Photonics Simulator project is:

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

Equivalently:

```math
u_{tt}=c^2\nabla^2u.
```

The current solver also supports a time-independent spatial wave-speed map
$c(x,y)$. Its governing update is discussed below, and the physical dielectric
interpretation is developed in the
[$E_z$ interface note](../physics/02_ez_dielectric_interface_model.md).

This equation is continuous in space and time. In principle, the field is defined for every possible value of: $x, y, t.$

A computer cannot store or evaluate an infinite number of spatial and temporal points. The finite difference method replaces the continuous domain with a discrete grid and approximates derivatives using neighboring grid values.

The main numerical concepts introduced in this note are:

* spatial discretization,
* temporal discretization,
* centered finite differences,
* the discrete Laplacian,
* explicit time stepping,
* numerical initialization,
* sponge-layer damping,
* source discretization,
* CFL stability,
* wavelength resolution,
* and discrete energy diagnostics.

---

## 2. From continuous space to a grid

In the continuous model, the scalar wave field is written as: $u(x,y,t)$.

In the numerical model, the spatial domain is divided into a rectangular grid.

The grid coordinates are:

```math
x_i=i\Delta x,
```

and:

```math
y_j=j\Delta y,
```

where:

* `i` is the grid index in the x direction,
* `j` is the grid index in the y direction,
* `\Delta x` is the grid spacing in x,
* `\Delta y` is the grid spacing in y.

Instead of storing the field at every possible position, the computer stores it only at the grid points:

```math
u(x_i,y_j,t).
```

This is written more compactly as:

```math
u_{i,j}(t).
```

In Python, the field is represented by a two-dimensional NumPy array:

```python
field[i, j]
```

In the current convention:

* array axis `0` corresponds to the x direction,
* array axis `1` corresponds to the y direction.

A field array therefore has shape:

```text
(nx, ny)
```

where `nx` and `ny` are the numbers of grid points in the x and y directions.

---

## 3. From continuous time to discrete time steps

Time is also discretized.

The discrete time levels are:

```math
t^n=n\Delta t,
```

where:

* `n` is the time-step index,
* `\Delta t` is the time step.

The numerical approximation of the field is written as:

```math
u_{i,j}^n.
```

This means the field value at spatial point `(i,j)` and time level `n`.

The current solver stores three conceptual time levels:

```python
u_prev
u_curr
u_next
```

These correspond to:

```math
u_{i,j}^{n-1},
\qquad
u_{i,j}^{n},
\qquad
u_{i,j}^{n+1}.
```

The solver uses the previous and current fields to calculate the next field.

---

## 4. Why finite differences are needed

The wave equation contains derivatives that cannot be evaluated directly from a finite set of stored values.

The finite difference method approximates these derivatives using nearby grid points.

For example, a spatial derivative in the x direction uses neighboring positions at the same time level:

```math
u_{i-1,j}^{n},
\qquad
u_{i,j}^{n},
\qquad
u_{i+1,j}^{n}.
```

By contrast, a time derivative uses the same spatial point at different time levels:

```math
u_{i,j}^{n-1},
\qquad
u_{i,j}^{n},
\qquad
u_{i,j}^{n+1}.
```

This distinction is essential:

* changing `i` or `j` moves through space,
* changing `n` moves through time.

---

## 5. First-derivative approximations

The first derivative of a function represents its local slope.

For a one-dimensional function `f(x)`, the derivative is defined by:

```math
\frac{df}{dx}
=
\lim_{\Delta x\rightarrow0}
\frac{f(x+\Delta x)-f(x)}{\Delta x}.
```

On a numerical grid, `\Delta x` is finite rather than infinitesimal.

### 5.1 Forward difference

A forward finite difference is:

```math
\frac{df}{dx}
\approx
\frac{f(x+\Delta x)-f(x)}{\Delta x}.
```

At index `i`:

```math
f'(x_i)
\approx
\frac{f_{i+1}-f_i}{\Delta x}.
```

### 5.2 Backward difference

A backward finite difference is:

```math
\frac{df}{dx}
\approx
\frac{f(x)-f(x-\Delta x)}{\Delta x}.
```

At index `i`:

```math
f'(x_i)
\approx
\frac{f_i-f_{i-1}}{\Delta x}.
```

### 5.3 Centered difference

A centered finite difference is:

```math
\frac{df}{dx}
\approx
\frac{f(x+\Delta x)-f(x-\Delta x)}{2\Delta x}.
```

At index `i`:

```math
f'(x_i)
\approx
\frac{f_{i+1}-f_{i-1}}{2\Delta x}.
```

Centered differences are symmetric around the evaluation point and are generally more accurate than simple forward or backward differences for smooth functions.

The current solver uses centered first derivatives in the energy diagnostic.

---

## 6. Second spatial derivative in one dimension

The wave equation contains second spatial derivatives.

The centered approximation of the second derivative is:

```math
\frac{\partial^2u}{\partial x^2}
\approx
\frac{
u_{i+1}-2u_i+u_{i-1}
}{
\Delta x^2
}.
```

At a two-dimensional grid point and time level `n`:

```math
\left.
\frac{\partial^2u}{\partial x^2}
\right|_{i,j}^{n}
\approx
\frac{
u_{i+1,j}^{n}
-
2u_{i,j}^{n}
+
u_{i-1,j}^{n}
}{
\Delta x^2
}.
```

This expression measures the local curvature in the x direction.

If the central value is larger than both neighboring values, the curvature tends to be negative.

If the central value is smaller than both neighboring values, the curvature tends to be positive.

If the field is locally linear or constant, the second derivative is approximately zero.

---

## 7. Second derivative in time

The centered finite difference approximation of the second time derivative is:

```math
\frac{\partial^2u}{\partial t^2}
\approx
\frac{
u_{i,j}^{n+1}
-
2u_{i,j}^{n}
+
u_{i,j}^{n-1}
}{
\Delta t^2
}.
```

This expression uses:

* one future value,
* one current value,
* one previous value.

Because the wave equation is second order in time, one stored field state is not sufficient. The solver requires two known time levels to calculate the next one.

---

## 8. The two-dimensional discrete Laplacian

In two dimensions, the Laplacian is:

```math
\nabla^2u
=
\frac{\partial^2u}{\partial x^2}
+
\frac{\partial^2u}{\partial y^2}.
```

The x-direction contribution is approximated by:

```math
\frac{\partial^2u}{\partial x^2}
\approx
\frac{
u_{i+1,j}^{n}
-
2u_{i,j}^{n}
+
u_{i-1,j}^{n}
}{
\Delta x^2
}.
```

The y-direction contribution is approximated by:

```math
\frac{\partial^2u}{\partial y^2}
\approx
\frac{
u_{i,j+1}^{n}
-
2u_{i,j}^{n}
+
u_{i,j-1}^{n}
}{
\Delta y^2
}.
```

Therefore, the discrete Laplacian is:

```math
\nabla^2u_{i,j}^{n}
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
}.
```

This five-point stencil uses:

* the central point,
* the forward x neighbor,
* the backward x neighbor,
* the forward y neighbor,
* the backward y neighbor.

A schematic representation is:

```text
              u[i,j+1]
                  |
                  |
u[i-1,j] ——— u[i,j] ——— u[i+1,j]
                  |
                  |
              u[i,j-1]
```

---

## 9. NumPy slicing implementation of the Laplacian

The current code computes the Laplacian only on the interior grid points.

The slice:

```python
field[1:-1, 1:-1]
```

selects:

* all rows except the first and last,
* all columns except the first and last.

For an array of shape:

```text
(nx, ny)
```

the interior slice has shape:

```text
(nx - 2, ny - 2)
```

### 9.1 Central values

The interior central values are:

```python
field[1:-1, 1:-1]
```

These represent:

```math
u_{i,j}.
```

### 9.2 Forward x neighbors

The slice:

```python
field[2:, 1:-1]
```

represents:

```math
u_{i+1,j}.
```

It starts from array index `2` and continues to the final row.

### 9.3 Backward x neighbors

The slice:

```python
field[:-2, 1:-1]
```

represents:

```math
u_{i-1,j}.
```

It starts from index `0` and stops two positions before the end.

### 9.4 Forward y neighbors

The slice:

```python
field[1:-1, 2:]
```

represents:

```math
u_{i,j+1}.
```

### 9.5 Backward y neighbors

The slice:

```python
field[1:-1, :-2]
```

represents:

```math
u_{i,j-1}.
```

All five arrays have the same shape, so NumPy can combine them element by element.

The implementation is:

```python
def compute_laplacian(field):
    """Compute the finite-difference Laplacian on interior points."""
    laplacian = np.zeros_like(field)

    laplacian[1:-1, 1:-1] = (
        (
            field[2:, 1:-1]
            - 2.0 * field[1:-1, 1:-1]
            + field[:-2, 1:-1]
        )
        / dx**2
        +
        (
            field[1:-1, 2:]
            - 2.0 * field[1:-1, 1:-1]
            + field[1:-1, :-2]
        )
        / dy**2
    )

    return laplacian
```

This is equivalent to the explicit-loop implementation:

```python
for i in range(1, nx - 1):
    for j in range(1, ny - 1):
        laplacian[i, j] = (
            (
                field[i + 1, j]
                - 2.0 * field[i, j]
                + field[i - 1, j]
            )
            / dx**2
            +
            (
                field[i, j + 1]
                - 2.0 * field[i, j]
                + field[i, j - 1]
            )
            / dy**2
        )
```

The vectorized NumPy version is normally faster because the operations are executed by optimized array routines rather than by Python loops.

---

## 10. The undamped finite-difference update rule

The continuous two-dimensional wave equation is:

```math
u_{tt}=c^2\nabla^2u.
```

Substituting the centered time approximation gives:

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
c^2\nabla^2u_{i,j}^{n}.
```

Multiplying by `\Delta t^2`:

```math
u_{i,j}^{n+1}
-
2u_{i,j}^{n}
+
u_{i,j}^{n-1}
=
c^2\Delta t^2\nabla^2u_{i,j}^{n}.
```

Solving for the future state:

```math
u_{i,j}^{n+1}
=
2u_{i,j}^{n}
-
u_{i,j}^{n-1}
+
c^2\Delta t^2\nabla^2u_{i,j}^{n}.
```

In code:

```python
next_field[1:-1, 1:-1] = (
    2.0 * current[1:-1, 1:-1]
    - previous[1:-1, 1:-1]
    + time.dt**2
    * wave_speed**2
    * laplacian[1:-1, 1:-1]
)
```

Here, `wave_speed` is the interior slice of the material wave-speed map. In
the homogeneous Phase 1 case, every entry equals the same constant $c$. This
is the core update equation for the fixed-boundary simulation.

---

## 11. Interpretation of the update rule

The update rule is:

```math
u^{n+1}
=
2u^n
-
u^{n-1}
+
c^2\Delta t^2\nabla^2u^n.
```

The term:

```math
2u^n-u^{n-1}
```

continues the temporal evolution of the field.

The term:

```math
c^2\Delta t^2\nabla^2u^n
```

adds the effect of spatial curvature.

The field therefore evolves through a combination of:

1. temporal inertia,
2. spatial coupling between neighboring points.

A localized disturbance propagates because the curvature at one point changes that point in time, which then changes the curvature experienced by neighboring points.

---

## 12. Initializing the two required time levels

Because the wave equation is second order in time, the solver needs two initial states:

```math
u^0
\qquad\text{and}\qquad
u^{-1}.
```

For the Gaussian initial condition, the field at `t=0` is:

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

The initial velocity is assumed to be zero:

```math
\left.
\frac{\partial u}{\partial t}
\right|_{t=0}
=0.
```

A Taylor expansion around `t=0` gives:

```math
u(-\Delta t)
=
u(0)
-
\Delta t\,u_t(0)
+
\frac{\Delta t^2}{2}u_{tt}(0)
+
O(\Delta t^3).
```

Because:

```math
u_t(0)=0,
```

and:

```math
u_{tt}(0)=c^2\nabla^2u(0),
```

the previous field is approximated by:

```math
u^{-1}
=
u^0
+
\frac{c^2\Delta t^2}{2}
\nabla^2u^0.
```

In code:

```python
current = create_gaussian_pulse(grid, initial)
initial_laplacian = compute_laplacian(current, grid)

previous = (
    current
    + 0.5
    * time.dt**2
    * material_map.wave_speed**2
    * initial_laplacian
)
```

The material wave-speed array is constant in the Phase 1 configuration and
spatially varying in later material scenarios.

This is more accurate than simply setting:

```python
previous = current.copy()
```

when the intended initial velocity is zero.

For a zero initial condition, both states are initialized as zero:

```python
current = np.zeros((nx, ny))
previous = np.zeros((nx, ny))
```

This is useful when the simulation is driven entirely by a continuous source.

---

## 13. Finite-difference update for the sponge layer

The sponge layer is modeled using the damped wave equation:

```math
u_{tt}
+
\gamma(x,y)u_t
=
c^2\nabla^2u.
```

Here, `\gamma(x,y)` is a spatially varying damping coefficient.

The second time derivative is approximated by:

```math
u_{tt}
\approx
\frac{
u^{n+1}
-
2u^n
+
u^{n-1}
}{
\Delta t^2
}.
```

The first time derivative in the damping term is approximated using a centered difference:

```math
u_t
\approx
\frac{
u^{n+1}
-
u^{n-1}
}{
2\Delta t
}.
```

Substitution into the damped equation gives:

```math
\frac{
u^{n+1}
-
2u^n
+
u^{n-1}
}{
\Delta t^2
}
+
\gamma
\frac{
u^{n+1}
-
u^{n-1}
}{
2\Delta t
}
=
c^2\nabla^2u^n.
```

Multiplying by `\Delta t^2`:

```math
u^{n+1}
-
2u^n
+
u^{n-1}
+
\frac{\gamma\Delta t}{2}
\left(
u^{n+1}
-
u^{n-1}
\right)
=
c^2\Delta t^2\nabla^2u^n.
```

Collecting the future-state terms:

```math
\left(
1+\frac{\gamma\Delta t}{2}
\right)
u^{n+1}
=
2u^n
-
\left(
1-\frac{\gamma\Delta t}{2}
\right)
u^{n-1}
+
c^2\Delta t^2\nabla^2u^n.
```

Therefore:

```math
u^{n+1}
=
\frac{
2u^n
-
\left(
1-\frac{\gamma\Delta t}{2}
\right)
u^{n-1}
+
c^2\Delta t^2\nabla^2u^n
}{
1+\frac{\gamma\Delta t}{2}
}.
```

In the code:

```python
gamma = damping_profile[1:-1, 1:-1]
wave_speed = material_map.wave_speed[1:-1, 1:-1]

next_field[1:-1, 1:-1] = (
    2.0 * current[1:-1, 1:-1]
    - (1.0 - gamma * time.dt / 2.0)
    * previous[1:-1, 1:-1]
    + time.dt**2
    * wave_speed**2
    * laplacian[1:-1, 1:-1]
) / (1.0 + gamma * time.dt / 2.0)
```

When:

```math
\gamma=0,
```

the expression reduces to the ordinary undamped wave-equation update.

The sponge layer reduces outgoing wave amplitudes, but it is not perfectly reflectionless.

---

## 14. Constructing the damping profile

The sponge profile depends on the distance of each grid point from the nearest domain edge.

First, one-dimensional distance arrays are created.

For the x direction:

```python
x_indices = np.arange(nx)

distance_x = np.minimum(
    x_indices,
    nx - 1 - x_indices,
)
```

For the y direction:

```python
y_indices = np.arange(ny)

distance_y = np.minimum(
    y_indices,
    ny - 1 - y_indices,
)
```

For example, with five points:

```text
indices:     [0, 1, 2, 3, 4]
distance:    [0, 1, 2, 1, 0]
```

The outermost points have distance zero, while points farther inside have larger distances.

### 14.1 Adding new axes

The expression:

```python
distance_x[:, np.newaxis]
```

changes the shape of `distance_x` from:

```text
(nx,)
```

to:

```text
(nx, 1)
```

It becomes a column array.

The expression:

```python
distance_y[np.newaxis, :]
```

changes the shape of `distance_y` from:

```text
(ny,)
```

to:

```text
(1, ny)
```

It becomes a row array.

### 14.2 Broadcasting into a two-dimensional array

NumPy broadcasts these arrays when evaluating:

```python
distance_to_edge = np.minimum(
    distance_x[:, np.newaxis],
    distance_y[np.newaxis, :],
)
```

The resulting shape is:

```text
(nx, ny)
```

At every point `(i,j)`:

```math
d_{i,j}
=
\min
\left(
d_{x,i},
d_{y,j}
\right).
```

This gives the distance to the nearest of the four domain edges.

### 14.3 Normalized sponge depth

The normalized depth inside the sponge is:

```python
normalized_depth = np.clip(
    (damping_width - distance_to_edge)
    / damping_width,
    0.0,
    1.0,
)
```

At the inner edge of the sponge:

```math
\text{normalized depth}=0.
```

At the outer domain edge:

```math
\text{normalized depth}=1.
```

Outside the sponge region, negative values are clipped to zero.

### 14.4 Damping coefficient

The final damping profile is:

```python
gamma = (
    max_damping
    * normalized_depth**damping_exponent
)
```

Mathematically:

```math
\gamma(x,y)
=
\gamma_{\max}
d(x,y)^p,
```

where:

* `\gamma_{\max}` is the maximum damping coefficient,
* `d(x,y)` is the normalized sponge depth,
* `p` is the damping exponent.

A larger exponent creates a gentler damping onset near the interior and a steeper increase near the outer edge.

---

## 15. Discrete representation of the sinusoidal source

The continuous sinusoidal source has the form:

```math
s(t)
=
A\sin(2\pi ft),
```

where:

* `A` is the source amplitude,
* `f` is the source frequency.

At time step `n`:

```math
t^n=n\Delta t.
```

Therefore, the discrete source value is:

```math
s^n
=
A\sin
\left(
2\pi fn\Delta t
\right).
```

In the code:

```python
time = step_index * dt

source_value = source_amplitude * np.sin(
    2.0 * np.pi * source_frequency * time
)
```

The source frequency is measured in:

```text
cycles per simulation-time unit
```

rather than cycles per time step.

In the Phase 1 implementation, the source was applied directly to one grid
point:

```python
field[source_x, source_y] += source_value
```

This produces an approximately circular wave in a homogeneous and isotropic
medium.

The source is applied after the normal wave update:

```python
u_next = step_wave(u_prev, u_curr)
apply_source(u_next, frame + 1)
```

This is a simple additive numerical source. It is not represented as a
separate forcing term in the continuous differential equation.

The current source system generalizes the same operation to a spatial profile
$P_{i,j}$ and an optional smooth ramp $R(t)$:

```math
s_{i,j}^{n}
=
P_{i,j} A R(t^n)\sin(2\pi f t^n).
```

The profile may select one point or a finite vertical line. The source remains
additive and is still injected after the ordinary wave update. See
[Controlled Sources and Field Monitors](../physics/03_controlled_sources_and_field_monitors.md)
for the complete Phase 3 source contract.

---

## 16. Connection to the solver implementation

The solver advances the field using the following sequence:

```python
laplacian = compute_laplacian(current, config.grid)
wave_speed = material_map.wave_speed[1:-1, 1:-1]
```

Then either the undamped or damped update is evaluated.

For fixed boundaries:

```python
next_field[1:-1, 1:-1] = (
    2.0 * current[1:-1, 1:-1]
    - previous[1:-1, 1:-1]
    + time.dt**2
    * wave_speed**2
    * laplacian[1:-1, 1:-1]
)
```

For sponge boundaries:

```python
gamma = damping_profile[1:-1, 1:-1]

next_field[1:-1, 1:-1] = (
    2.0 * current[1:-1, 1:-1]
    - (1.0 - gamma * time.dt / 2.0)
    * previous[1:-1, 1:-1]
    + time.dt**2
    * wave_speed**2
    * laplacian[1:-1, 1:-1]
) / (1.0 + gamma * time.dt / 2.0)
```

The uniform Phase 1 update is recovered when every entry of `wave_speed` is
the same constant $c$.

The outer boundary is then forced to zero:

```python
apply_fixed_boundaries(next_field)
```

A source may then be applied:

```python
apply_source(next_field, step_index)
```

The current implementation supplies a validated, precomputed point or line
source profile to this operation. Source injection is completed before energy
is calculated.

Finally, the stored time levels are shifted:

```python
u_prev, u_curr = u_curr, u_next
```

No array copy is required because `step_wave()` creates a new array for `u_next`.

After promotion, each configured field monitor records the completed current
field. This ordering ensures that monitors observe the same source-injected
state whose energy was appended for that step.

---

## 17. Why `np.roll` was replaced

An earlier version of the solver used `np.roll` to obtain neighboring grid values.

For example:

```python
np.roll(field, 1, axis=0)
```

shifts the array along one axis.

However, `np.roll` wraps values from one side of the array to the opposite side. This behavior naturally resembles a periodic boundary condition.

The current implementation instead uses explicit interior slices:

```python
field[2:, 1:-1]
field[:-2, 1:-1]
field[1:-1, 2:]
field[1:-1, :-2]
```

This has several advantages:

* no implicit wraparound occurs,
* the finite-difference stencil is easier to identify,
* the boundary points are excluded explicitly,
* boundary conditions can be handled separately,
* and the implementation is safer for nonperiodic simulations.

---

## 18. Boundary treatment

Finite-difference formulas require neighboring values.

At an interior point, all four neighboring values exist:

```text
field[i+1, j]
field[i-1, j]
field[i, j+1]
field[i, j-1]
```

At the domain boundaries, one or more of these neighbors would lie outside the computational grid.

The current solver computes the Laplacian only for interior points and handles the boundary separately.

The outermost values are set to zero:

```python
def apply_fixed_boundaries(field):
    field[0, :] = 0.0
    field[-1, :] = 0.0
    field[:, 0] = 0.0
    field[:, -1] = 0.0
```

This is a homogeneous Dirichlet boundary condition:

```math
u=0.
```

For the fixed-boundary mode, this produces strong reflections.

For the sponge mode, outgoing waves should be attenuated before reaching the outer fixed boundary, reducing the reflected amplitude.

Other possible boundary treatments include:

* Neumann boundaries,
* periodic boundaries,
* analytical absorbing boundary conditions,
* sponge layers,
* and perfectly matched layers.

---

## 19. Grid and wavelength resolution

The grid spacing determines the spatial resolution of the simulation.

A smaller value of `\Delta x` or `\Delta y` provides more grid points over the same physical distance, improving the representation of spatial variations.

For a sinusoidal source, the nominal wavelength is:

```math
\lambda_{\text{nominal}}
=
\frac{c}{f}.
```

The number of grid points per wavelength is:

```math
N_{\lambda,x}
=
\frac{\lambda_{\text{nominal}}}{\Delta x},
```

and:

```math
N_{\lambda,y}
=
\frac{\lambda_{\text{nominal}}}{\Delta y}.
```

For the current typical parameters:

```text
c = 1
f = 0.075
dx = 1
dy = 1
```

the nominal wavelength is:

```math
\lambda_{\text{nominal}}
=
\frac{1}{0.075}
\approx
13.33.
```

Therefore:

```math
N_{\lambda,x}
\approx
13.33,
```

and:

```math
N_{\lambda,y}
\approx
13.33.
```

The current code prints a warning when fewer than 10 grid points per wavelength are available.

This threshold is a practical heuristic rather than a universal guarantee of accuracy.

A simulation may remain stable with fewer than 10 points per wavelength but still show significant:

* phase error,
* numerical dispersion,
* directional distortion,
* and incorrect wave speed.

---

## 20. Numerical dispersion

Numerical dispersion means that the simulated propagation speed depends artificially on:

* wavelength,
* direction,
* grid spacing,
* and time step.

The continuous homogeneous wave equation has a constant propagation speed `c`.

The discrete solver only approximates the continuous equation, so its numerical wave speed may differ slightly from `c`.

Short wavelengths are generally affected more strongly because they are represented by fewer grid points.

In a two-dimensional Cartesian grid, waves traveling along the grid axes may also propagate somewhat differently from waves traveling diagonally. This is called numerical anisotropy.

Numerical dispersion can be reduced by:

* decreasing `\Delta x` and `\Delta y`,
* using more points per wavelength,
* choosing an appropriate time step,
* and using higher-order numerical methods.

---

## 21. Time step and CFL stability

The time step controls how far the simulation advances during each update.

A larger `\Delta t` reduces the number of required steps, but it can make the explicit scheme unstable.

For the two-dimensional variable-speed wave equation, the current CFL
condition uses the fastest material speed in the domain:

```math
c_{\max}\Delta t
\sqrt{
\frac{1}{\Delta x^2}
+
\frac{1}{\Delta y^2}
}
\leq1.
```

The code defines:

```python
courant = maximum_wave_speed * dt * np.sqrt(
    1.0 / dx**2
    + 1.0 / dy**2
)
```

and checks:

```python
if courant > 1.0:
    raise ValueError(
        "Simulation unstable: reduce dt or increase dx and/or dy."
    )
```

where

```math
c_{\max}=\max_{i,j} c_{i,j}.
```

Using the maximum is necessary because every material cell must satisfy the
explicit stability bound. For a uniform medium, $c_{\max}=c$ and the Phase 1
condition is recovered.

For equal spatial spacing:

```math
\Delta x=\Delta y=\Delta,
```

the condition becomes:

```math
\frac{c_{\max}\Delta t}{\Delta}
\leq
\frac{1}{\sqrt{2}}.
```

For the typical parameters:

```text
c_max = 1
dt = 0.4
dx = dy = 1
```

the Courant value is:

```math
S
=
0.4\sqrt{2}
\approx
0.566.
```

Because:

```math
0.566<1,
```

the selected configuration satisfies the stability condition.

---

## 22. Temporal sampling of the source

The continuous source is sampled at discrete time intervals `\Delta t`.

The temporal sampling frequency is:

```math
f_s=\frac{1}{\Delta t}.
```

The corresponding Nyquist frequency is:

```math
f_{\text{Nyquist}}
=
\frac{1}{2\Delta t}.
```

The sinusoidal source must satisfy:

```math
f<f_{\text{Nyquist}}.
```

For:

```text
dt = 0.4
```

the Nyquist frequency is:

```math
f_{\text{Nyquist}}
=
\frac{1}{0.8}
=
1.25.
```

The current source frequency:

```text
f = 0.075
```

is well below this limit.

Remaining below the Nyquist frequency prevents temporal aliasing, but good accuracy normally requires more than two samples per period.

The number of time steps per source period is:

```math
N_T
=
\frac{T}{\Delta t}
=
\frac{1}{f\Delta t}.
```

For the current parameters:

```math
N_T
=
\frac{1}{0.075\cdot0.4}
\approx
33.33.
```

Therefore, each source oscillation is represented by approximately 33 time steps.

---

## 23. What numerical instability looks like

When the CFL condition is violated, the field usually does not become only slightly inaccurate.

Instead, numerical errors can be amplified during each update.

Typical signs of instability include:

* rapidly increasing amplitudes,
* extreme values without a physical cause,
* checkerboard-like patterns,
* overflow warnings,
* `nan` values,
* `inf` values,
* and a meaningless animation.

A continuously driven source naturally increases the amount of energy in the domain, so increasing energy alone is not necessarily instability.

The distinction is that physical source-driven growth should remain connected to the source and wave pattern, while numerical instability normally produces uncontrolled and rapidly diverging values throughout the grid.

---

## 24. Accuracy versus stability

Stability and accuracy are related but different.

A stable simulation does not diverge numerically, but it can still be inaccurate.

Possible errors in a stable simulation include:

* numerical dispersion,
* phase errors,
* artificial anisotropy,
* boundary reflections,
* insufficient wavelength resolution,
* and inaccurate source representation.

Satisfying the CFL condition is therefore necessary but not sufficient.

Accuracy improves when:

* the grid spacing is reduced,
* more points per wavelength are used,
* the time step is sufficiently small,
* boundary conditions are appropriate,
* source frequencies are properly sampled,
* and results are compared with analytical or known reference behavior.

---

## 25. Discrete energy diagnostic

The current scalar solver advances the time-independent variable-speed
equation

```math
\frac{1}{c(x,y)^2}u_{tt}
=
u_{xx}+u_{yy}.
```

A compatible continuous energy density is

```math
\mathcal{E}
=
\frac{1}{2c(x,y)^2}u_t^2
+
\frac{1}{2}\left(u_x^2+u_y^2\right).
```

This expression follows by multiplying the equation by $u_t$:

```math
\frac{1}{c(x,y)^2}u_tu_{tt}
=
u_t\left(u_{xx}+u_{yy}\right).
```

Because the material map is independent of time, the left-hand side is

```math
\frac{1}{c(x,y)^2}u_tu_{tt}
=
\frac{\partial}{\partial t}
\left(
\frac{1}{2c(x,y)^2}u_t^2
\right).
```

For the spatial terms, the product rule gives, for example,

```math
u_tu_{xx}
=
\frac{\partial}{\partial x}
\left(
u_tu_x
\right)
-
\frac{\partial}{\partial t}
\left(
\frac{1}{2}u_x^2
\right),
```

with an analogous expression in the $y$ direction.

Substituting these relations into the wave equation and grouping the time derivatives leads to the local conservation law

```math
\frac{\partial \mathcal{E}}{\partial t}
+
\nabla\cdot\mathbf{S}
=
0,
```

where

```math
\mathbf{S}
=
-u_t\nabla u
```

represents the spatial flow of wave energy.

The quantity inside the time derivative is therefore identified as the energy density:

```math
\mathcal{E}
=
\frac{1}{2c(x,y)^2}u_t^2
+
\frac{1}{2}\left(u_x^2+u_y^2\right).
```

For a uniform medium, multiplying this density and flux by the constant $c^2$
recovers the equivalent Phase 1 convention
$\tfrac12u_t^2+\tfrac12c^2|\nabla u|^2$. A spatially varying $c(x,y)$ does not
permit that factor to be removed globally, so the implementation uses the
variable-speed form above.

The first term is associated with temporal variation and can be interpreted as a kinetic-like contribution.

The second term is associated with spatial gradients and can be interpreted as a potential-like contribution caused by deformation of the field.

### 25.1 Time derivative

For two consecutive time states, the implementation defines the half-step
velocity:

```math
v^{n-1/2}=\frac{u^n-u^{n-1}}{\Delta t}.
```

In code:

```python
velocity = (current - previous) / dt
```

### 25.2 Spatial derivatives

Phase 5.1 places spatial differences on the faces between adjacent nodes. The
x-face difference is:

```math
D_xu_{i+1/2,j}^{n}
=
\frac{u_{i+1,j}^{n}-u_{i,j}^{n}}{\Delta x}.
```

In code:

```python
gradient_x = (
    current[1:, :] - current[:-1, :]
) / dx
```

The y-face difference is:

```math
D_yu_{i,j+1/2}^{n}
=
\frac{u_{i,j+1}^{n}-u_{i,j}^{n}}{\Delta y}.
```

In code:

```python
gradient_y = (
    current[:, 1:] - current[:, :-1]
) / dy
```

### 25.3 Total discrete energy

The centered leapfrog update exactly conserves the half-step energy:

```math
\begin{aligned}
E_h^{n+1/2}
={}&
\frac12\sum_{i,j}
\frac{(v_{i,j}^{n+1/2})^2}{c_{i,j}^2}\Delta x\Delta y
\\
&+\frac12\sum_{x\text{-faces}}
D_xu^{n+1}D_xu^n\Delta x\Delta y
\\
&+\frac12\sum_{y\text{-faces}}
D_yu^{n+1}D_yu^n\Delta x\Delta y.
\end{aligned}
```

The cross-time potential terms arise directly from multiplying the leapfrog
equation by its centered velocity. They make the diagnostic an exact invariant
of the source-free, undamped fixed-boundary update rather than only an
independent approximation of continuous energy.

The detailed proof, including discrete summation by parts and the associated
face flux, is given in
[Scalar Energy and Flux](04_scalar_energy_and_flux.md).

### 25.4 Gaussian pulse

For a Gaussian pulse without a continuous source, the simulation plots normalized energy:

```math
\frac{E(t)}{E(0)}.
```

This is useful for comparing fixed and sponge boundaries.

With fixed boundaries, most energy remains in the domain.

With sponge boundaries, energy decreases as waves enter the damping layer.

### 25.5 Continuous source

For a continuous source, the initial field may have zero energy while the source adds energy at every time step.

Normalizing by the initial energy would therefore be undefined or misleading.

For source-driven simulations, the code plots absolute total energy:

```math
E(t).
```

The energy can:

* increase while the domain fills with waves,
* oscillate because of sinusoidal excitation,
* fluctuate due to interference,
* or approach a long-term balance between source injection and sponge absorption.

---

## 26. Normalized units

The Phase 1 simulation uses normalized units.

Typical values are:

```python
c = 1.0
dx = 1.0
dy = 1.0
dt = 0.4
```

These values do not directly represent meters, seconds, or the physical speed of light.

Normalized units are useful because they simplify the initial numerical implementation and allow the focus to remain on:

* propagation,
* stability,
* resolution,
* boundaries,
* sources,
* and diagnostics.

The relationships between quantities remain meaningful.

For example:

```math
\lambda=\frac{c}{f}
```

still determines the nominal wavelength in simulation-length units.

A later phase may connect the solver to physical units by defining:

* a physical length scale,
* a physical time scale,
* a physical frequency,
* refractive index,
* and material properties.

---

## 27. Computational cost

The simulation stores arrays with shape:

```math
N_x\times N_y.
```

For:

```text
nx = 150
ny = 150
```

the number of grid points is:

```math
150\times150=22500.
```

At each time step, the solver performs operations across the full grid.

The computational cost per step is therefore approximately proportional to:

```math
N_xN_y.
```

If both grid dimensions are doubled:

```math
N_x\rightarrow2N_x,
```

and:

```math
N_y\rightarrow2N_y,
```

then the number of grid points increases by a factor of four:

```math
(2N_x)(2N_y)=4N_xN_y.
```

Memory use also increases because several arrays are stored simultaneously, including:

* the previous field,
* the current field,
* the next field,
* the Laplacian,
* the damping profile,
* and diagnostic gradient arrays.

Higher spatial resolution therefore improves accuracy but increases both computation time and memory requirements.

---

## 28. Summary

The finite difference method transforms the continuous wave equation:

```math
u_{tt}=c^2\nabla^2u
```

into the explicit update:

```math
u_{i,j}^{n+1}
=
2u_{i,j}^{n}
-
u_{i,j}^{n-1}
+
c^2\Delta t^2
\nabla^2u_{i,j}^{n}.
```

The discrete Laplacian is:

```math
\nabla^2u_{i,j}^{n}
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
}.
```

The current implementation uses NumPy slicing to apply this stencil simultaneously to all interior grid points.

The solver also includes:

* second-order initialization for a Gaussian pulse,
* a zero-field initialization,
* continuous sinusoidal point and finite-line sources,
* reusable spatial source profiles and a smooth turn-on ramp,
* fixed reflective boundaries,
* a spatially varying sponge layer,
* uniform, planar-interface, rectangular, and composite material maps,
* CFL stability validation,
* spatial wavelength-resolution diagnostics,
* temporal source-sampling checks,
* approximate energy tracking,
* named point and line field monitors,
* and single-frequency harmonic-response analysis.

The harmonic estimator and its numerical-dispersion convention are derived in
[Harmonic Response Analysis](02_harmonic_response_analysis.md).

The damped update is:

```math
u^{n+1}
=
\frac{
2u^n
-
\left(
1-\frac{\gamma\Delta t}{2}
\right)
u^{n-1}
+
c^2\Delta t^2\nabla^2u^n
}{
1+\frac{\gamma\Delta t}{2}
}.
```

The finite difference method is the central mathematical and computational foundation of Phase 1 of the Photonics Simulator project.
