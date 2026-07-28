# 2026-07-28 - Phase 2.2 Uniform Material Map

## 1. Goal

The goal of Phase 2.2 was to introduce material infrastructure into the
two-dimensional scalar-wave simulator without introducing a material
interface or changing the verified default numerical behavior.

The main objectives were:

1. Add an explicit material configuration.
2. Represent refractive index and wave speed as grid-sized arrays.
3. Make the solver use the spatial wave-speed array.
4. Generalize the CFL and energy calculations for a variable-speed medium.
5. Validate material configurations and arrays.
6. Add a material-map visualization.
7. Preserve the complete Phase 2.1 numerical regression.

This was intentionally an infrastructure phase. The default domain remains
uniform, with refractive index \(n=1\) and wave speed \(c=1\).

---

## 2. Phase context

Phase 1 established the scalar-wave solver, sources, boundary conditions,
visualization, and energy diagnostics.

Phase 2.1 reorganized the original single-file implementation into the
reusable `wavesim` package. That refactor preserved the numerical behavior of
the final Phase 1 simulation.

Phase 2.2 is the first material-related phase:

```text
Phase 2.1 - Modular refactor                 Complete
Phase 2.2 - Uniform material map             Complete
Phase 2.3 - Planar material interface        Next
Phase 2.4 - Rectangular dielectric region    Planned
Phase 2.5 - Reusable geometry functions      Planned
Phase 2.6 - Phase validation                 Planned
```

The purpose of introducing a uniform map first was to separate structural
changes from new interface physics. If the default simulation changed during
this phase, the regression test would identify the change before an interface
made the cause harder to isolate.

---

## 3. Files added or modified

New material module:

```text
wavesim/materials.py
```

New material tests:

```text
tests/test_materials.py
```

Modified modules:

```text
wavesim/config.py
wavesim/solver.py
wavesim/visualization.py
```

Updated project documentation:

```text
README.md
```

The existing regression test remained in:

```text
tests/test_phase2_1_regression.py
```

---

## 4. Selected scalar material model

The solver now advances the variable-speed scalar wave equation

```math
\frac{\partial^2 u}{\partial t^2}
=
c(x,y)^2\nabla^2u.
```

The local wave speed is derived from refractive index using

```math
c(x,y)
=
\frac{c_{\mathrm{ref}}}{n(x,y)}.
```

Here:

- \(u(x,y,t)\) is an abstract scalar wave field;
- \(c_{\mathrm{ref}}\) is the reference wave speed;
- \(n(x,y)\) is the refractive-index map;
- \(c(x,y)\) is the local propagation-speed map.

The default normalized values are:

```text
reference_wave_speed = 1.0
background_refractive_index = 1.0
```

Therefore:

```math
n(x,y)=1
```

and

```math
c(x,y)=1
```

at every grid cell.

This model is still scalar. It is not yet identified as a TE or TM
electromagnetic formulation and is not a complete Maxwell solver.

---

## 5. Material configuration

A frozen configuration dataclass was added:

```python
@dataclass(frozen=True)
class MaterialConfig:
    reference_wave_speed: float = 1.0
    background_refractive_index: float = 1.0
```

`MaterialConfig` was added to `SimulationConfig`.

Wave speed was removed from `TimeConfig` because propagation speed is a
material property rather than a time-stepping setting. `TimeConfig` now
contains only:

```python
dt: float = 0.4
steps: int = 500
```

This removes the possibility of maintaining two independent wave-speed values
in the time and material configurations.

The distinction is now:

```text
TimeConfig      -> when and how long the simulation advances
MaterialConfig  -> how the medium determines propagation speed
```

---

## 6. Material-map representation

The new material module defines:

```python
@dataclass
class MaterialMap:
    refractive_index: np.ndarray
    wave_speed: np.ndarray
```

Both arrays must have:

```python
shape == grid.shape
```

The arrays follow the existing storage convention:

```text
array[x_index, y_index]
```

The initial map constructor creates a uniform refractive-index array:

```python
refractive_index = np.full(
    grid.shape,
    material.background_refractive_index,
    dtype=float,
)
```

The wave-speed map is then derived from it:

```python
wave_speed = (
    material.reference_wave_speed
    / refractive_index
)
```

`Wave2DSimulation` constructs and owns the resulting map:

```python
simulation.material_map
```

This keeps the fixed configuration separate from the precomputed spatial
arrays used during a simulation.

---

## 7. Material validation

The scalar material configuration is rejected when:

- the reference wave speed is not finite;
- the reference wave speed is not positive;
- the background refractive index is not finite;
- the background refractive index is not positive.

The constructed arrays are rejected when:

- either array has the wrong shape;
- either array contains `NaN` or infinity;
- any refractive-index value is zero or negative;
- any wave-speed value is zero or negative.

Invalid values are not clipped, replaced, or repaired silently. The validation
functions raise descriptive `ValueError` exceptions instead.

This validation is important because non-finite or nonpositive speeds would
make the field update, energy diagnostic, and CFL calculation invalid.

---

## 8. Spatial finite-difference update

The Phase 2.1 homogeneous update used one scalar speed:

```math
u_{i,j}^{n+1}
=
2u_{i,j}^{n}
-
u_{i,j}^{n-1}
+
(c\Delta t)^2
\nabla_h^2u_{i,j}^{n}.
```

Phase 2.2 replaces that scalar factor with the spatial speed map:

```math
u_{i,j}^{n+1}
=
2u_{i,j}^{n}
-
u_{i,j}^{n-1}
+
\Delta t^2c_{i,j}^2
\nabla_h^2u_{i,j}^{n}.
```

Conceptually, the numerical implementation uses:

```python
time.dt**2 * wave_speed**2 * laplacian
```

The same substitution was applied to both:

- the fixed-boundary update;
- the sponge-boundary update.

The source ordering was not changed. A configured source is still injected
after the finite-difference update.

With a uniform speed map containing only `1.0`, the new expression reproduces
the original scalar-speed expression.

---

## 9. Gaussian initial condition

The Gaussian pulse still supports a zero initial velocity.

The Phase 2.2 previous time level is initialized using:

```math
u^{-1}
=
u^0
+
\frac{1}{2}
\Delta t^2c(x,y)^2
\nabla_h^2u^0.
```

This is the spatial-speed version of the initialization that was already
verified in Phase 1 and preserved during Phase 2.1.

The default continuous-source configuration uses the zero initial condition,
but retaining a correct material-aware Gaussian initialization is necessary
for source-free pulse simulations.

---

## 10. CFL stability calculation

The stability calculation now uses the maximum wave speed anywhere in the
material map:

```math
c_{\max}
=
\max_{i,j}c_{i,j}.
```

The two-dimensional Courant number is:

```math
C
=
c_{\max}\Delta t
\sqrt{
\frac{1}{\Delta x^2}
+
\frac{1}{\Delta y^2}
}.
```

The simulation requires:

```math
C\leq1.
```

The order of initialization is now:

1. Validate the ordinary configuration values.
2. Construct and validate the material map.
3. Find the maximum map speed.
4. Validate the CFL condition.
5. Allocate and initialize the evolving field state.

This order is necessary because the final stability limit depends on the
actual material map rather than only on a scalar configuration value.

For the default parameters:

```text
c_max = 1.0
dt = 0.4
dx = 1.0
dy = 1.0
```

the Courant number remains:

```math
C
=
1.0(0.4)\sqrt{1+1}
\approx
0.566.
```

---

## 11. Source wavelength diagnostic

The nominal source wavelength is now calculated from the wave speed at the
source position:

```math
\lambda_{\mathrm{source}}
=
\frac{c_{\mathrm{source}}}{f}.
```

This is more appropriate than using the maximum speed in the whole domain.
When spatial materials are introduced later, the local medium surrounding the
source determines its nominal wavelength.

The number of grid points per wavelength remains:

```math
N_{\lambda,x}
=
\frac{\lambda_{\mathrm{source}}}{\Delta x}
```

and

```math
N_{\lambda,y}
=
\frac{\lambda_{\mathrm{source}}}{\Delta y}.
```

The existing warning threshold of ten points per wavelength was preserved.

---

## 12. Generalized energy diagnostic

The Phase 2.2 scalar equation can be written as:

```math
\frac{1}{c(x,y)^2}u_{tt}
=
\nabla^2u.
```

For a time-independent speed map, the selected diagnostic is:

```math
E
=
\int
\left[
\frac{1}{2c(x,y)^2}u_t^2
+
\frac{1}{2}
\left|\nabla u\right|^2
\right]
dA.
```

The implemented discrete approximation is:

```math
E
\approx
\sum_{i,j}
\left[
\frac{1}{2c_{i,j}^2}u_t^2
+
\frac{1}{2}
\left(
u_x^2+u_y^2
\right)
\right]
\Delta x\Delta y.
```

Velocity remains approximated by:

```math
u_t
\approx
\frac{u^n-u^{n-1}}{\Delta t}.
```

Spatial gradients remain centered finite differences.

When \(c(x,y)=1\), the generalized expression has exactly the same numerical
form as the Phase 2.1 energy diagnostic. This allowed the original energy
regression to remain unchanged.

The existing display convention was also preserved:

- source-free simulations with nonzero initial energy display normalized
  remaining energy;
- continuously driven simulations display absolute total energy.

---

## 13. Material-map visualization

An optional refractive-index figure was added.

The displayed array is:

```python
simulation.material_map.refractive_index.T
```

with:

```python
origin="lower"
```

This follows the same orientation convention as the wave field and sponge
profile:

```text
stored array orientation:     array[x_index, y_index]
displayed image orientation:  array.T with origin="lower"
```

The figure reports the minimum and maximum refractive index. The interactive
workflow also prints the minimum and maximum refractive index and wave speed.

For the default Phase 2.2 configuration, the map appears uniformly colored and
reports:

```text
refractive-index minimum = 1.000
refractive-index maximum = 1.000
wave-speed minimum = 1.000
wave-speed maximum = 1.000
```

Although a uniform plot contains no geometry, it verifies the map shape,
orientation, values, and visualization pipeline before interfaces are added.

---

## 14. Test coverage

The test suite now contains 15 tests.

The material tests cover:

1. Default uniform refractive index and speed.
2. A non-unit uniform refractive index.
3. Material-map ownership by `Wave2DSimulation`.
4. Use of the material speed during the field update.
5. Use of the material speed in the energy diagnostic.
6. CFL validation using the fastest material speed.
7. Invalid reference wave speed.
8. Invalid background refractive index.
9. Incorrect refractive-index-map shape.
10. Incorrect wave-speed-map shape.
11. Non-finite refractive-index values.
12. Non-finite wave-speed values.
13. Nonpositive refractive-index values.
14. Nonpositive wave-speed values.

The fifteenth test is the original full Phase 2.1 numerical regression.

The test command was:

```powershell
python -m unittest discover -s tests -v
```

All tests passed.

---

## 15. Preserved numerical regression

The default simulation remains:

```text
initial condition: zero
source: point_sine
boundary: sponge
refractive index: uniform n = 1
wave speed: uniform c = 1
```

The protected energy checkpoints remain:

```text
Step 1:     0.03182002983188608
Step 50:   10.861960749063872
Step 100:  22.499974544196014
Step 250:  50.83918140302646
Step 500:  70.13486394160974
```

The expected final field extrema remain:

```text
Minimum: -0.5893284375273641
Maximum:  0.365929446861314
```

The energy-history length after 500 updates remains:

```text
501
```

because the history includes the initial state at step zero.

Preserving these values confirms that the uniform map reproduces the previous
homogeneous solver and that Phase 2.2 did not accidentally change the source
ordering, damping update, initial state, or numerical time stepping.

---

## 16. Architecture decisions

The following design decisions were made:

1. Keep configuration values in frozen dataclasses.
2. Store grid-sized material arrays in a separate mutable `MaterialMap`.
3. Let `Wave2DSimulation` own its constructed material map.
4. Keep `wavesim/solver.py` independent of Matplotlib.
5. Keep scenario files thin.
6. Pass numerical dependencies explicitly rather than using module-level
   globals.
7. Use the maximum map speed for CFL stability.
8. Use the local source speed for wavelength reporting.
9. Introduce only a uniform material constructor in Phase 2.2.
10. Preserve the original Phase 2.1 regression unchanged.

Interface- and geometry-specific helper functions were deliberately not added.
They belong to later Phase 2 work.

---

## 17. Current limitations

Phase 2.2 has the following intentional limitations:

1. The material constructor creates only a uniform map.
2. No discontinuous interface has been added.
3. No rectangular dielectric region has been added.
4. The model is scalar and has no selected TE or TM interpretation.
5. The current point source is not ideal for quantitative interface
   validation.
6. The sponge profile is independent of material properties.
7. The code uses normalized rather than SI units.
8. No material dispersion or loss is modeled.
9. No claim of quantitatively accurate Fresnel behavior is made.
10. Material and geometry coordinates are still expressed as grid indices.

These limitations are acceptable because the purpose of Phase 2.2 was to
establish material infrastructure without introducing interface physics.

---

## 18. Unresolved interface decision

Before Phase 2.3 introduces a discontinuity, the governing PDE and its physical
interpretation must be reviewed explicitly.

The current equation is:

```math
u_{tt}
=
c(x,y)^2\nabla^2u.
```

At a discontinuous material boundary, simply multiplying the existing
cell-centered Laplacian by a discontinuous speed array produces one particular
scalar model. It is not automatically equivalent to a TE or TM Maxwell
interface.

A different physical model could require a divergence-form operator:

```math
\nabla\cdot\left[a(x,y)\nabla u\right].
```

The appropriate coefficient and interface conditions depend on the field being
modeled.

Therefore, Phase 2.3 must define:

1. whether the field remains an abstract scalar wave or represents a specific
   electromagnetic component;
2. the precise variable-coefficient PDE;
3. the interface continuity conditions;
4. the chosen coefficient placement and finite-difference discretization;
5. which qualitative or quantitative results are physically justified.

No planar interface should be implemented before this decision is documented.

---

## 19. Phase 2.2 definition of done

```text
[x] wavesim/materials.py exists
[x] MaterialConfig exists
[x] MaterialMap stores refractive index and wave speed
[x] Default map is uniform with n = 1 and c = 1
[x] Solver uses a wave-speed array
[x] CFL uses the maximum wave speed
[x] Initial-condition setup uses the material map
[x] Energy diagnostic uses the selected variable-speed scalar model
[x] Material configuration and array validation exist
[x] Material visualization exists
[x] Material-specific tests pass
[x] Original Phase 2.1 regression passes
[x] No interface or dielectric geometry was added
```

Phase 2.2 is complete.

---

## 20. Next steps

The next planned phase is:

```text
Phase 2.3 - Add one planar material interface
```

Before writing interface code:

1. Review the scalar PDE at a discontinuous coefficient.
2. Decide the intended physical interpretation.
3. Document the corresponding interface conditions.
4. Decide whether the existing cell-centered update is sufficient for the
   phase goal or whether a conservative discretization is required.
5. Define a simple planar geometry and keep it away from the sponge region.
6. Preserve the Phase 2.2 uniform-map configuration as a regression case.
7. Avoid quantitative Fresnel validation until a suitable source and physical
   field formulation have been selected.

---

## 21. Summary

Phase 2.2 introduced the project’s first explicit material representation.

Refractive index and wave speed are now stored as validated spatial arrays,
and the solver uses the speed map for:

- Gaussian initialization;
- fixed and sponge time stepping;
- CFL stability;
- source wavelength reporting;
- energy diagnostics.

The interactive workflow can display the refractive-index map and report its
range.

Most importantly, the default uniform map reproduces the complete verified
Phase 2.1 numerical regression. This establishes a controlled foundation for
introducing a planar material interface in Phase 2.3.
