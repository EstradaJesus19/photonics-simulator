# 2026-07-29 - Phase 2.4 Rectangular Dielectric Region

## 1. Goal

The goal of Phase 2.4 was to extend the material infrastructure from one
unbounded planar interface to one finite, grid-aligned dielectric object.

The selected geometry is a rectangular region embedded in a uniform
background:

```text
Background material
    refractive index = 1.0

Rectangular material
    refractive index = 1.5
    x indices = [110, 160)
    y indices = [50, 110)
```

The main objectives were:

1. Add a rectangular material-map constructor.
2. Define an unambiguous indexing convention.
3. Validate the rectangle bounds and refractive index.
4. Keep geometry construction separate from the solver.
5. Reuse the material-map injection introduced in Phase 2.3.
6. Create a dedicated rectangular-dielectric scenario.
7. Display all four material boundaries automatically.
8. Verify that the wave enters and exits the rectangle.
9. Confirm numerical stability without relying only on visual inspection.
10. Preserve all previous uniform-material and planar-interface behavior.

Phase 2.4 intentionally implements one explicit rectangular constructor.
General geometry composition remains reserved for Phase 2.5.

---

## 2. Phase context

The relevant Phase 2 sequence is:

```text
Phase 2.1 - Modular refactor                 Complete
Phase 2.2 - Uniform material map             Complete
Phase 2.3 - Planar dielectric interface      Complete
Phase 2.4 - Rectangular dielectric region    Implemented and verified
Phase 2.5 - Reusable geometry functions      Next
Phase 2.6 - Phase validation                 Planned
```

Phase 2.3 established the architecture required by this phase:

- a validated `MaterialMap`;
- spatial refractive-index and wave-speed arrays;
- optional material-map injection into `Wave2DSimulation`;
- CFL validation using the fastest speed in the supplied map;
- material-aware stepping and energy calculation;
- material contours derived directly from the refractive-index map;
- reusable, headless scenario construction.

Phase 2.4 therefore required no geometry-specific changes to the solver or
visualization system.

---

## 3. Physical model

The scalar field continues to represent the out-of-plane electric component:

```math
u(x,y,t)=E_z(x,y,t).
```

The selected reduced electromagnetic model is:

```math
\frac{\partial^2 E_z}{\partial t^2}
=
c(x,y)^2\nabla^2E_z,
```

with:

```math
c(x,y)
=
\frac{c_{\mathrm{ref}}}{n(x,y)}.
```

The material assumptions remain:

- linear;
- isotropic;
- lossless;
- nondispersive;
- nonmagnetic;
- spatially varying permittivity;
- spatially constant permeability.

For the Phase 2.4 scenario:

```text
Background:
    n = 1.0
    c = 1.0

Rectangle:
    n = 1.5
    c = 1 / 1.5 = 0.666...
```

The wave therefore propagates more slowly and has a shorter wavelength inside
the rectangle.

The derivation and limitations of this model are documented in:

```text
notes/physics/02_ez_dielectric_interface_model.md
```

---

## 4. Files added or modified

Modified material infrastructure:

```text
wavesim/materials.py
```

Expanded material tests:

```text
tests/test_materials.py
```

New scenario:

```text
simulations/wave2d_rectangular_dielectric.py
```

New scenario tests:

```text
tests/test_rectangular_dielectric_scenario.py
```

New representative figures:

```text
outputs/figures/phase_2/2026-07-29_rectangular_dielectric_material_map.png
outputs/figures/phase_2/2026-07-29_rectangular_dielectric_field.png
outputs/figures/phase_2/2026-07-29_rectangular_dielectric_energy.png
```

New simulation log:

```text
notes/simulation-logs/phase_2/2026-07-29_003_rectangular_dielectric_region.md
```

No Phase 2.4 change was required in:

```text
wavesim/solver.py
wavesim/visualization.py
```

Their existing supplied-map and generic-contour behavior already supported the
new geometry.

---

## 5. Rectangular material constructor

The following constructor was added:

```python
create_rectangular_material_map(
    grid,
    material,
    x_start,
    x_stop,
    y_start,
    y_stop,
    rectangle_refractive_index,
)
```

It performs the following operations:

1. Validates all four bounds.
2. Validates the rectangular refractive index.
3. Creates a uniform background array.
4. Assigns the rectangular refractive index to one array slice.
5. Derives the complete wave-speed array.
6. Constructs a `MaterialMap`.
7. Runs the common material-map validation.

The background value comes from:

```python
material.background_refractive_index
```

and the speed is derived using:

```python
material.reference_wave_speed / refractive_index
```

The constructor returns complete arrays rather than geometry metadata. The
solver therefore remains independent of how the material was constructed.

---

## 6. Half-open indexing convention

Rectangle bounds use the NumPy half-open convention:

```python
refractive_index[
    x_start:x_stop,
    y_start:y_stop,
] = rectangle_refractive_index
```

The start indices are included and the stop indices are excluded:

```text
x_start <= x < x_stop
y_start <= y < y_stop
```

For the Phase 2.4 scenario:

```text
x_start = 110
x_stop  = 160
y_start = 50
y_stop  = 110
```

the occupied cells are:

```text
x = 110 through 159
y = 50 through 109
```

The rectangle dimensions are therefore:

```text
width  = 160 - 110 = 50 cells
height = 110 - 50  = 60 cells
```

With unit grid spacing, these also correspond to 50 by 60 normalized spatial
units.

This convention matches normal Python and NumPy slicing and makes dimensions
equal to `stop - start`.

---

## 7. Discrete material boundaries

The four discrete transitions occur between the following cell pairs:

```text
Left boundary:
    x = 109 and x = 110

Right boundary:
    x = 159 and x = 160

Bottom boundary:
    y = 49 and y = 50

Top boundary:
    y = 109 and y = 110
```

The rectangular region is bounded in both spatial directions, unlike the
Phase 2.3 planar interface.

The four interfaces allow additional behavior:

- reflection from the front face;
- transmission into the rectangle;
- reflection from the rear face;
- transmission back into the background;
- diffraction around the upper and lower edges;
- internal interference between multiple reflected components.

---

## 8. Rectangle-specific validation

Each bound must be an integer:

```text
x_start
x_stop
y_start
y_stop
```

Boolean values are rejected even though `bool` is a subclass of `int` in
Python.

The x bounds must satisfy:

```math
1
\le
x_{\mathrm{start}}
<
x_{\mathrm{stop}}
\le
n_x-1.
```

The y bounds must satisfy:

```math
1
\le
y_{\mathrm{start}}
<
y_{\mathrm{stop}}
\le
n_y-1.
```

These conditions guarantee that the rectangle:

1. is nonempty;
2. remains strictly inside the computational grid;
3. leaves at least one background cell on every side.

The rectangular refractive index must be:

```text
finite
positive
```

The constructor rejects:

```text
0
negative values
NaN
positive infinity
```

Finally, the common `validate_material_map()` function verifies the complete
refractive-index and wave-speed arrays.

---

## 9. Why the rectangle must remain inside the grid

A rectangle touching an outer grid boundary would no longer have four
background-material interfaces.

Requiring at least one surrounding background cell:

- preserves the meaning of an embedded object;
- makes all four interfaces explicit;
- prevents confusion between a material transition and an outer boundary;
- keeps this constructor distinct from the planar-interface constructor;
- supports predictable contour visualization.

The dedicated scenario uses a much larger separation from the outer boundary
than the minimum enforced by the generic constructor.

---

## 10. Dedicated scenario

The dedicated entry point is:

```text
simulations/wave2d_rectangular_dielectric.py
```

It can be launched from the repository root using:

```powershell
python -m simulations.wave2d_rectangular_dielectric
```

The module exposes:

```python
create_scenario()
```

which returns:

```python
tuple[SimulationConfig, MaterialMap]
```

This keeps scenario construction reusable by:

- the interactive entry point;
- unit tests;
- headless propagation checks;
- future result-saving tools;
- future parameter studies.

Matplotlib is imported only inside `main()`, so importing `create_scenario()`
does not require the visualization system.

---

## 11. Scenario parameters

The Phase 2.4 scenario uses:

```text
Grid
    nx = 240
    ny = 160
    dx = 1.0
    dy = 1.0

Time
    dt = 0.4
    steps = 600

Background material
    refractive index = 1.0
    wave speed = 1.0

Rectangular material
    refractive index = 1.5
    wave speed = 0.666...

Rectangle
    x indices = [110, 160)
    y indices = [50, 110)
    width = 50 cells
    height = 60 cells

Initial condition
    kind = zero

Source
    kind = point_sine
    position = (60, 80)
    amplitude = 0.5
    frequency = 0.05

Boundary
    kind = sponge
    damping width = 25
    maximum damping = 0.02
    damping exponent = 2
```

The source is horizontally aligned with the center of the rectangle:

```text
rectangle y center = (50 + 110) / 2 = 80
source y = 80
```

This alignment sends the strongest forward-propagating portion of the circular
wavefront through the central part of the object.

---

## 12. Spatial layout

The approximate horizontal layout through `y = 80` is:

```text
x = 0        source       rectangle front      rectangle rear       x = 239
|---------------*----------------|==================|--------------------|
              x = 60          x = 110           x = 160

       background n = 1.0       rectangle n = 1.5      background n = 1.0
```

The full rectangle occupies:

```text
110 <= x < 160
 50 <= y < 110
```

The source-to-front-face distance is:

```math
110-60=50
```

grid units.

---

## 13. Geometry placement relative to the sponge

The sponge width is:

```text
25 cells
```

The undamped central ranges begin after index 25 and end before:

```text
x = 240 - 25 = 215
y = 160 - 25 = 135.
```

The important positions are:

```text
source x = 60
rectangle x range = [110, 160)
rectangle y range = [50, 110)
```

Therefore:

- the source is outside the left sponge;
- the rectangle is outside the left and right sponge regions;
- the rectangle is outside the bottom and top sponge regions;
- the rectangle has undamped background space on every side;
- the transmitted wave has room to emerge before reaching the right sponge.

The scenario test protects these placement relationships.

---

## 14. CFL stability

The maximum wave speed remains in the background:

```math
c_{\max}=1.
```

The speed inside the rectangle is:

```math
c_{\mathrm{rectangle}}
=
\frac{1}{1.5}
\approx
0.667.
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

Using:

```text
c_max = 1.0
dt = 0.4
dx = 1.0
dy = 1.0
```

gives:

```math
C
=
0.4\sqrt{2}
\approx
0.566.
```

The scenario therefore satisfies:

```math
C<1.
```

The solver obtains `c_max` from the supplied material map rather than assuming
that the background is always the fastest material.

---

## 15. Wavelength resolution

The temporal source frequency is:

```text
f = 0.05
```

In the background:

```math
\lambda_{\mathrm{background}}
=
\frac{1}{0.05}
=
20.
```

This gives:

```text
20 grid points per wavelength
```

with unit grid spacing.

Inside the rectangle:

```math
\lambda_{\mathrm{rectangle}}
=
\frac{1/1.5}{0.05}
\approx
13.33.
```

This gives approximately:

```text
13.33 grid points per wavelength
```

inside the dielectric.

Both materials remain above the existing ten-points-per-wavelength guideline.
The visibly shorter wavelength inside the rectangle is therefore expected
physical behavior rather than an under-resolved artifact.

---

## 16. Approximate propagation timing

The source-to-front-face distance is:

```math
d_1=50.
```

At the background speed:

```math
t_1
=
\frac{50}{1}
=
50.
```

With:

```math
\Delta t=0.4,
```

the wave reaches the front face at approximately:

```math
\frac{50}{0.4}
=
125
```

time steps.

The rectangle width is:

```math
d_2=50.
```

At the rectangular-material speed:

```math
t_2
=
\frac{50}{2/3}
=
75.
```

The approximate time required to reach the rear face is therefore:

```math
t_{\mathrm{rear}}
\approx
50+75
=
125,
```

or:

```math
\frac{125}{0.4}
\approx
313
```

time steps.

The automated test advances to step 360. This provides time for a measurable
field to emerge several cells beyond the rear boundary.

---

## 17. Reuse of supplied-map architecture

The scenario constructs its map first:

```python
material_map = create_rectangular_material_map(...)
```

and then supplies it to the simulation:

```python
Wave2DSimulation(
    config,
    material_map=material_map,
)
```

The interactive workflow uses the same injection:

```python
run_interactive_simulation(
    config,
    material_map=material_map,
)
```

No rectangle coordinates are passed to the solver.

The solver sees only:

```text
refractive_index[x, y]
wave_speed[x, y]
```

This confirms that the Phase 2.3 separation of responsibilities extends to a
finite object:

```text
materials.py
    constructs the geometry-dependent arrays

solver.py
    evolves whichever valid arrays it receives
```

---

## 18. Generic boundary visualization

The existing visualization derives boundaries from the refractive-index map.

For this scenario:

```text
unique refractive indices = [1.0, 1.5]
```

The contour level is:

```math
\frac{1.0+1.5}{2}
=
1.25.
```

Applying that contour to the two-dimensional material map produces the
complete rectangle outline automatically.

The visualization does not receive:

```text
RECTANGLE_X_START
RECTANGLE_X_STOP
RECTANGLE_Y_START
RECTANGLE_Y_STOP
```

This demonstrates that the Phase 2.3 contour design was already general enough
for bounded shapes.

---

## 19. Material-constructor tests

Four tests were added in:

```text
tests/test_materials.py
```

under:

```python
RectangularMaterialMapTest
```

They verify:

1. Correct background refractive index.
2. Correct rectangular refractive index.
3. Correct background wave speed.
4. Correct rectangular wave speed.
5. Correct half-open array placement.
6. Rejection of bounds that touch the outer grid.
7. Rejection of empty or reversed x ranges.
8. Rejection of empty or reversed y ranges.
9. Rejection of noninteger bounds.
10. Rejection of zero, negative, non-finite, or infinite refractive indices.

The expected complete material array is constructed independently in the test
and compared with:

```python
np.testing.assert_array_equal(...)
```

This verifies the rectangle interior, the background, and all four transitions
in one exact array comparison.

---

## 20. Scenario-level tests

Five tests were added in:

```text
tests/test_rectangular_dielectric_scenario.py
```

They verify:

1. Grid, time, source, and boundary parameters.
2. Complete rectangular material geometry.
3. Complete wave-speed geometry.
4. Source and rectangle placement outside the sponge.
5. Construction of a valid `Wave2DSimulation`.
6. Ownership of the supplied material map.
7. Correct field shape.
8. Finite initial energy.
9. Propagation into the rectangle.
10. Propagation beyond the rear face.
11. Finite current and previous fields.
12. Finite energy history.
13. Positive driven-wave energy.
14. Absence of obvious runaway field growth.

The scenario tests use `create_scenario()` directly and do not open Matplotlib.

---

## 21. Headless propagation check

The complete scenario is advanced for:

```text
360 steps
```

The test checks:

```text
step_index = 360
energy-history length = 361
```

The extra energy-history value represents the initial state at step zero.

The rectangle-interior sampling region is:

```python
current[
    RECTANGLE_X_START + 5:RECTANGLE_X_STOP - 5,
    center_y - 10:center_y + 10,
]
```

For the scenario constants, this corresponds to:

```text
x = [115, 155)
y = [70, 90)
```

The rear transmitted region is:

```python
current[
    RECTANGLE_X_STOP + 5:,
    center_y - 10:center_y + 10,
]
```

which begins at:

```text
x = 165
```

and uses a narrow central y band aligned with the source and rectangle center.

This central band makes the check more representative of propagation through
the rectangle than a whole-domain region that would also include waves
diffracting around the object.

Both sampled regions must satisfy:

```text
maximum absolute amplitude > 1e-3
```

The threshold confirms a measurable field rather than roundoff-level numerical
noise.

---

## 22. Numerical-safety checks

The propagation test requires:

```python
np.all(np.isfinite(current))
np.all(np.isfinite(previous))
np.all(np.isfinite(energy_history))
```

It also requires:

```text
current energy > 0
maximum absolute field < 10
```

The upper field limit is a broad smoke-test threshold. It detects severe
numerical growth without making the test fragile with respect to small,
legitimate changes in the waveform.

During checkpoint selection, representative values at step 360 were
approximately:

```text
maximum absolute field              1.218
maximum interior amplitude          0.224
maximum rear-center amplitude       0.172
total scalar-wave energy           48.442
```

These values are diagnostic observations, not exact regression targets. The
automated assertions intentionally use broad physical and numerical
conditions.

---

## 23. Complete automated test result

The full command is:

```powershell
python -m unittest discover -s tests -v
```

The verified result was:

```text
Ran 35 tests

OK
```

The suite contains:

```text
26 tests preserved from Phase 2.3
 4 rectangular material-constructor tests
 5 rectangular scenario tests
35 tests total
```

The passing suite confirms that Phase 2.4 did not break:

- the default uniform simulation;
- the Phase 2.1 numerical regression;
- uniform material behavior;
- planar-interface construction;
- supplied material-map integration;
- material-aware stepping and energy;
- CFL validation;
- the Phase 2.3 scenario.

---

## 24. Interactive observations

The interactive rectangular-dielectric scenario produced the expected
qualitative behavior.

The confirmed observations were:

1. The material map displayed a 50-by-60 rectangular region.
2. The rectangle appeared at the intended x and y indices.
3. The field animation displayed all four boundaries.
4. The point source produced outgoing circular wavefronts.
5. The wave reached the front face at approximately the expected time.
6. Part of the field reflected back into the background.
7. Part of the field entered the rectangle.
8. Propagation was slower inside the higher-index material.
9. The wavelength was shorter inside the rectangle.
10. A transmitted component emerged from the rear face.
11. Waves diffracted around the upper and lower edges.
12. Multiple interfaces produced internal interference.
13. The sponge reduced outer-boundary contamination.
14. No numerical instability or non-finite behavior was observed.

These observations are consistent with scattering from a finite dielectric
object.

---

## 25. Interpretation of the final field

The saved field figure corresponds to:

```text
step = 600
total scalar-wave energy = 66.4356
```

The rectangular contour remains clearly visible.

The field on the source side contains:

- the continuously generated incident field;
- reflection from the front surface;
- waves returning from later internal reflections;
- diffraction around the object.

The field inside the rectangle shows a distinct interference pattern created
by its four boundaries and reduced propagation speed.

The field beyond the rectangle confirms rear-face transmission. The wavefront
is not a simple plane wave because the source is localized and the object is
finite.

---

## 26. Energy interpretation

The saved energy history rises from zero to approximately:

```text
66.4
```

over 600 time steps.

This increase is expected because the point source continuously injects
energy. The sponge removes part of the outgoing energy, but it does not
necessarily remove it as quickly as the active source adds it.

The small repeated oscillations are associated with the sinusoidal source and
the evolving interference pattern.

The curve remains smooth and bounded over the simulated interval. It does not
show the explosive growth characteristic of a numerical instability.

The diagnostic remains the scalar-wave energy:

```math
E_{\mathrm{wave}}
=
\int
\left[
\frac{1}{2c(x,y)^2}E_{z,t}^2
+
\frac{1}{2}
\left|\nabla E_z\right|^2
\right]
dA.
```

It is not the complete Maxwell electromagnetic energy because the solver does
not explicitly evolve or store the magnetic field components.

---

## 27. Figures

The rectangular material map was saved at:

```text
outputs/figures/phase_2/2026-07-29_rectangular_dielectric_material_map.png
```

![Rectangular dielectric material map](../../../outputs/figures/phase_2/2026-07-29_rectangular_dielectric_material_map.png)

Figure 1. Refractive-index map for the Phase 2.4 scenario. The background has
`n = 1.0`, and the finite rectangular region has `n = 1.5`.

The final field was saved at:

```text
outputs/figures/phase_2/2026-07-29_rectangular_dielectric_field.png
```

![Rectangular dielectric field](../../../outputs/figures/phase_2/2026-07-29_rectangular_dielectric_field.png)

Figure 2. Field at step 600. The dashed contour marks all four rectangle
boundaries. The result shows scattering, transmission, diffraction, and
internal interference.

The energy history was saved at:

```text
outputs/figures/phase_2/2026-07-29_rectangular_dielectric_energy.png
```

![Rectangular dielectric energy](../../../outputs/figures/phase_2/2026-07-29_rectangular_dielectric_energy.png)

Figure 3. Total scalar-wave energy during continuous excitation. The source
adds energy while the sponge removes part of the outgoing field.

---

## 28. Architecture decisions

The following decisions were made:

1. Add one explicit rectangular constructor before generalizing geometry.
2. Use standard half-open NumPy bounds.
3. Require the rectangle to remain strictly inside the grid.
4. Use the configured material as the uniform background.
5. Supply the rectangular refractive index explicitly.
6. Derive wave speed from refractive index rather than accepting two
   independently editable arrays.
7. Return a complete validated `MaterialMap`.
8. Keep rectangle coordinates out of the solver.
9. Reuse optional supplied-map injection unchanged.
10. Reuse generic material contours unchanged.
11. Use sponge boundaries for the primary scattering experiment.
12. Keep the source aligned with the rectangle center.
13. Test a central transmission corridor behind the object.
14. Use broad smoke-test thresholds rather than exact field values.
15. Keep scenario construction importable without Matplotlib.
16. Preserve the existing default and planar scenarios.

---

## 29. Problems encountered

No numerical failure was observed in the rectangular scenario.

One test-placement error occurred during implementation. The propagation test
was initially placed inside:

```python
RectangularMaterialMapTest
```

in:

```text
tests/test_materials.py
```

That class does not construct a complete scenario and therefore has no:

```python
self.config
self.material_map
```

The test was moved to:

```python
RectangularDielectricScenarioTest
```

in:

```text
tests/test_rectangular_dielectric_scenario.py
```

where `setUp()` creates both objects using `create_scenario()`.

This reinforced the intended test separation:

```text
tests/test_materials.py
    isolated material-constructor behavior

tests/test_rectangular_dielectric_scenario.py
    complete configured simulation behavior
```

After the move, all 35 tests passed.

---

## 30. Current limitations

The Phase 2.4 implementation has the following limitations:

1. The constructor creates only one rectangle.
2. The rectangle must be grid-aligned.
3. Geometry is specified using grid indices rather than physical coordinates.
4. The rectangle cannot touch an outer grid boundary.
5. No reusable add, overwrite, union, or composition operation exists yet.
6. Multiple or overlapping shapes are not yet supported by a public helper.
7. Rotated rectangles are not supported.
8. Curved objects are not supported.
9. The point source does not provide controlled plane-wave illumination.
10. Reflection and transmission are verified qualitatively, not as Fresnel
    coefficients.
11. The model evolves only `E_z`, not the complete Maxwell field set.
12. Magnetic permeability is spatially constant.
13. Materials are lossless and nondispersive.
14. The sponge boundary is not a PML.
15. Some numerical dispersion and interface error remain expected.
16. Figures are saved manually rather than automatically.

These limitations are consistent with the incremental Phase 2 plan.

---

## 31. Phase 2.4 definition of done

```text
[x] Rectangular material-map constructor exists
[x] Half-open indexing convention is documented
[x] Rectangle dimensions are unambiguous
[x] Bounds must be integers
[x] Boolean bounds are rejected
[x] Empty and reversed ranges are rejected
[x] Rectangle must remain strictly inside the grid
[x] Rectangular refractive index must be finite and positive
[x] Wave speed is derived from refractive index
[x] Complete material map is validated
[x] Constructor has isolated unit tests
[x] All four material transitions are verified
[x] Dedicated rectangular scenario exists
[x] Scenario construction works headlessly
[x] Source and rectangle are outside the sponge
[x] Source is aligned with the rectangle center
[x] CFL stability is satisfied
[x] Both materials satisfy the wavelength-resolution guideline
[x] Existing solver accepts the rectangle without modification
[x] Existing visualization outlines all four boundaries
[x] Wave entry into the rectangle is verified automatically
[x] Rear-face transmission is verified automatically
[x] Fields and energy remain finite in the smoke test
[x] Broad runaway-growth protection is present
[x] Full suite passes with 35 tests
[x] Qualitative reflection and transmission were observed
[x] Slower propagation and shorter wavelength were observed
[x] Edge diffraction and internal interference were observed
[x] Representative material-map figure saved
[x] Representative field figure saved
[x] Representative energy figure saved
[x] Phase 2.4 simulation log created
[x] README updated for Phase 2.4
[x] Phase 2.4 commit created
```

The Phase 2.4 implementation, validation, interactive inspection, figures,
detailed experiment record, README, and repository closeout are complete.

---

## 32. Next phase

The next planned phase is:

```text
Phase 2.5 - Reusable geometry functions
```

Phase 2.5 should generalize only the patterns now supported by both the planar
and rectangular implementations.

Possible work includes:

1. Creating a background material map independently of any shape.
2. Applying rectangular regions to an existing refractive-index array.
3. Supporting multiple material regions.
4. Defining explicit overwrite behavior for overlapping shapes.
5. Separating geometry mutation from wave-speed derivation.
6. Providing reusable validation for bounds and refractive indices.
7. Preserving final `MaterialMap` validation.
8. Adding tests for composition order and overlapping geometries.

The solver should continue to receive only the final validated map.

---

## 33. Summary

Phase 2.4 introduced the first finite dielectric object into the Photonics
Simulator.

A validated rectangular constructor creates a uniform background and assigns:

```text
n = 1.5
```

to:

```text
x = [110, 160)
y = [50, 110).
```

The corresponding speed inside the object is:

```text
c = 0.667
```

compared with:

```text
c = 1.0
```

in the background.

The scenario reused the supplied-map solver architecture and generic contour
visualization from Phase 2.3 without geometry-specific modifications.

The interactive result displayed the expected reflection, transmission,
shorter internal wavelength, slower internal propagation, edge diffraction,
and interference between multiple boundaries.

A headless 360-step test independently verified measurable field amplitude
both inside and beyond the rectangle while all fields and energy values
remained finite.

All 35 automated tests passed, including the earlier numerical regression and
planar-interface tests.

Phase 2.4 implementation, validation, documentation, and repository closeout
are complete.