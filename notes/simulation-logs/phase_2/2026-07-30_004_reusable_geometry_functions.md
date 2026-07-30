# 2026-07-30 - Phase 2.5 Reusable Geometry Functions

## 1. Goal

The goal of Phase 2.5 was to replace one-geometry-at-a-time material
construction with a reusable composition pipeline.

Before this phase, the project supported:

- a uniform material map;
- one vertical planar interface;
- one strictly embedded rectangular dielectric.

Each constructor produced a complete `MaterialMap` immediately. That approach
was appropriate while introducing the first material geometries, but it did
not provide a public way to combine multiple regions before deriving wave
speed.

Phase 2.5 introduced the following workflow:

```text
create background refractive-index array
                |
                v
apply geometry operation 1
                |
                v
apply geometry operation 2
                |
                v
finalize the completed refractive-index array
                |
                v
validated MaterialMap
                |
                v
Wave2DSimulation
```

The main objectives were:

1. Validate refractive-index arrays independently.
2. Separate geometry construction from wave-speed derivation.
3. Create a reusable background array.
4. Apply multiple rectangular regions sequentially.
5. Define explicit overlap behavior.
6. Avoid accidental mutation and shared array ownership.
7. Keep the existing public constructors compatible.
8. Demonstrate composition with a nested three-material scenario.
9. Verify propagation through the composite object headlessly.
10. Preserve every previous numerical and scenario regression.

---

## 2. Phase context

The relevant Phase 2 sequence is:

```text
Phase 2.1 - Modular refactor                 Complete
Phase 2.2 - Uniform material map             Complete
Phase 2.3 - Planar dielectric interface      Complete
Phase 2.4 - Rectangular dielectric region    Complete
Phase 2.5 - Reusable geometry functions      Implemented and verified
Phase 2.6 - Phase validation                 Next
```

Phase 2.4 intentionally delayed generalization until an explicit rectangular
object revealed which operations were actually shared.

The recurring pattern was:

```text
construct n(x,y)
derive c(x,y)
validate both arrays
```

Phase 2.5 separates those stages so multiple geometry operations can act on
`n(x,y)` before `c(x,y)` is calculated.

---

## 3. Physical model

The physical model is unchanged.

The simulated scalar field represents:

```math
u(x,y,t)=E_z(x,y,t),
```

and obeys:

```math
\frac{\partial^2 E_z}{\partial t^2}
=
c(x,y)^2\nabla^2E_z.
```

The local wave speed is:

```math
c(x,y)
=
\frac{c_{\mathrm{ref}}}{n(x,y)}.
```

Phase 2.5 changes how the refractive-index array is assembled. It does not
change:

- the finite-difference update;
- the selected interface model;
- the energy diagnostic;
- CFL validation;
- source application;
- boundary handling;
- material contour visualization.

The material assumptions remain linear, isotropic, lossless, nondispersive,
nonmagnetic, and spatially varying only through permittivity.

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

New composite scenario:

```text
simulations/wave2d_composite_geometry.py
```

New composite scenario tests:

```text
tests/test_composite_geometry_scenario.py
```

New representative figures:

```text
outputs/figures/phase_2/2026-07-30_composite_geometry_material_map.png
outputs/figures/phase_2/2026-07-30_composite_geometry_field.png
outputs/figures/phase_2/2026-07-30_composite_geometry_energy.png
```

New simulation log:

```text
notes/simulation-logs/phase_2/2026-07-30_004_reusable_geometry_functions.md
```

Updated project overview:

```text
README.md
```

No Phase 2.5 change was required in:

```text
wavesim/config.py
wavesim/solver.py
wavesim/visualization.py
```

---

## 5. Independent refractive-index validation

The new validation function is:

```python
validate_refractive_index_array(
    refractive_index,
    grid,
)
```

It verifies:

1. The array shape equals `grid.shape`.
2. Every value is finite.
3. Every value is positive.

This validation now occurs before wave-speed derivation. Invalid values such
as zero therefore cannot create an infinity through division before the
underlying refractive-index error is reported.

`validate_material_map()` reuses this function and then validates the
wave-speed array independently.

The separation supports geometry operations that work only with
refractive-index arrays and do not yet have a `MaterialMap`.

---

## 6. Material-map finalization

The new finalization function is:

```python
create_material_map_from_refractive_index(
    grid,
    material,
    refractive_index,
)
```

It performs the following steps:

1. Converts the completed input to a floating-point NumPy array.
2. Makes a defensive copy.
3. Validates the copied refractive-index array.
4. Derives wave speed using the configured reference speed.
5. Constructs a `MaterialMap`.
6. Validates the complete material map.

The derived array is:

```python
wave_speed = (
    material.reference_wave_speed
    / refractive_index_copy
)
```

Wave-speed derivation now has one reusable implementation rather than being
repeated by every geometry constructor.

---

## 7. Defensive copy ownership

Finalization does not store the caller's editable array directly.

Instead, it uses:

```python
np.array(
    refractive_index,
    dtype=float,
    copy=True,
)
```

This establishes the ownership boundary:

```text
editable geometry arrays
    belong to geometry construction

finalized refractive-index and wave-speed arrays
    belong to the MaterialMap
```

Changing the source geometry array after finalization does not alter the
completed map.

The tests verify:

```python
np.shares_memory(
    material_map.refractive_index,
    source_index,
)
```

is false.

They also verify that an integer source array becomes a floating-point
material array without truncating derived material values.

---

## 8. Background refractive-index construction

The reusable background function is:

```python
create_background_refractive_index_array(
    grid,
    material,
)
```

It creates:

```python
np.full(
    grid.shape,
    material.background_refractive_index,
    dtype=float,
)
```

and validates the result before returning it.

Unlike `create_uniform_material_map()`, this function returns only `n(x,y)`.
It is therefore an appropriate starting point for later geometry operations.

---

## 9. Reusable rectangular operation

The reusable geometry operation is:

```python
add_rectangular_region(
    refractive_index,
    grid,
    x_start=...,
    x_stop=...,
    y_start=...,
    y_stop=...,
    region_refractive_index=...,
)
```

It:

1. Validates the input refractive-index array.
2. Validates all four bounds.
3. Validates the region refractive index.
4. Makes a floating-point copy of the input.
5. Writes the rectangular slice into the copy.
6. Validates the updated result.
7. Returns the new array.

The slice convention remains half-open:

```python
updated_refractive_index[
    x_start:x_stop,
    y_start:y_stop,
] = region_refractive_index
```

Therefore:

```text
x_start <= x < x_stop
y_start <= y < y_stop
```

---

## 10. Pure-copy geometry behavior

`add_rectangular_region()` returns a new array and leaves its input unchanged.

Composition therefore looks like:

```python
refractive_index = (
    create_background_refractive_index_array(
        grid,
        material,
    )
)

refractive_index = add_rectangular_region(
    refractive_index,
    grid,
    ...,
)

refractive_index = add_rectangular_region(
    refractive_index,
    grid,
    ...,
)
```

The selected behavior favors:

- explicit state transitions;
- simple reasoning;
- isolated intermediate results;
- protection against unintended mutation;
- straightforward tests.

The cost is one complete array copy per geometry operation. This is acceptable
for the current educational grid sizes and small number of regions. A future
large-scale geometry builder could use controlled in-place construction if
profiling shows that copies are a meaningful bottleneck.

---

## 11. General bounds and edge contact

The reusable rectangular operation accepts:

```math
0
\le
x_{\mathrm{start}}
<
x_{\mathrm{stop}}
\le
n_x
```

and:

```math
0
\le
y_{\mathrm{start}}
<
y_{\mathrm{stop}}
\le
n_y.
```

This means a general region may touch any grid edge.

That behavior is required to express geometries such as the right side of a
planar interface:

```python
x_start = interface_index
x_stop = grid.nx
y_start = 0
y_stop = grid.ny
```

The Phase 2.4 embedded-rectangle constructor remains stricter. It still
requires at least one background cell on every side.

The distinction is:

```text
add_rectangular_region()
    general composition operation
    edge contact allowed
    returns a refractive-index array

create_rectangular_material_map()
    dedicated embedded-object constructor
    edge contact rejected
    returns a MaterialMap
```

---

## 12. Overlap semantics

Overlapping geometry uses ordered overwrite semantics:

```text
later operation wins
```

For example:

```python
first = add_rectangular_region(
    background,
    grid,
    region_refractive_index=1.5,
    ...,
)

second = add_rectangular_region(
    first,
    grid,
    region_refractive_index=2.0,
    ...,
)
```

Cells covered only by the first region retain:

```text
n = 1.5
```

Cells covered by the second region receive:

```text
n = 2.0
```

including cells where the two rectangles overlap.

This rule is deterministic, easy to visualize, and analogous to painting
successive material regions onto a map.

The API does not yet implement union, intersection, subtraction, blending, or
priority metadata.

---

## 13. Compatibility refactor

The existing constructors remain available:

```python
create_uniform_material_map(...)
create_planar_interface_material_map(...)
create_rectangular_material_map(...)
```

Their public signatures and scenario behavior are unchanged.

They now use the reusable pipeline internally.

The uniform constructor:

```text
creates a background array
finalizes it
```

The planar-interface constructor:

```text
creates a background array
adds one edge-touching rectangular region
finalizes it
```

The embedded-rectangle constructor:

```text
performs its stricter object-specific validation
creates a background array
adds one general rectangular region
finalizes it
```

This refactor removes duplicated wave-speed and `MaterialMap` construction
without breaking previous entry points.

---

## 14. Composite scenario

The dedicated Phase 2.5 scenario is:

```text
simulations/wave2d_composite_geometry.py
```

It can be launched with:

```powershell
python -m simulations.wave2d_composite_geometry
```

The module exposes:

```python
create_scenario()
```

and defers Matplotlib import until `main()`.

The scenario therefore remains usable by:

- the interactive entry point;
- headless tests;
- numerical diagnostics;
- future parameter studies.

---

## 15. Composite geometry

The scenario begins with:

```text
Background
    n = 1.0
```

It then applies:

```text
Outer rectangle
    x = [110, 170)
    y = [45, 115)
    n = 1.5
```

followed by:

```text
Nested core
    x = [130, 155)
    y = [65, 95)
    n = 2.0
```

The core lies strictly inside the outer rectangle:

```text
110 < 130 < 155 < 170
45 < 65 < 95 < 115
```

Because it is applied second, the core overwrites the corresponding part of
the `n=1.5` region.

The resulting map contains exactly:

```text
n = 1.0
n = 1.5
n = 2.0
```

---

## 16. Scenario parameters

The complete scenario uses:

```text
Grid
    nx = 240
    ny = 160
    dx = 1.0
    dy = 1.0

Time
    dt = 0.4
    steps = 600

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

Background
    refractive index = 1.0
    wave speed = 1.0

Outer rectangle
    refractive index = 1.5
    wave speed = 0.667

Core
    refractive index = 2.0
    wave speed = 0.5
```

The source and both rectangles are centered vertically at:

```text
y = 80
```

This alignment sends the strongest forward-propagating part of the circular
wavefront through the nested core.

---

## 17. Geometry placement and sponge separation

The sponge width is:

```text
25 cells
```

The right sponge begins near:

```text
x = 240 - 25 = 215
```

and the top sponge begins near:

```text
y = 160 - 25 = 135.
```

The outer rectangle occupies:

```text
x = [110, 170)
y = [45, 115)
```

It therefore remains outside every sponge region and leaves undamped
background space around the complete object.

The source at:

```text
(60, 80)
```

also lies outside the sponge and to the left of the composite object.

These placement relationships are protected by scenario-level tests.

---

## 18. CFL stability

The fastest material is the background:

```math
c_{\max}=1.
```

The Courant number is:

```math
C
=
c_{\max}\Delta t
\sqrt{
\frac{1}{\Delta x^2}
+
\frac{1}{\Delta y^2}
}
=
0.4\sqrt{2}
\approx
0.566.
```

Therefore:

```math
C<1.
```

The lower speeds in the outer rectangle and core do not reduce stability.
The simulation still validates CFL using the maximum speed in the completed
material map.

---

## 19. Wavelength resolution

With:

```text
f = 0.05
```

the background wavelength is:

```math
\lambda_1
=
\frac{1.0}{0.05}
=
20.
```

The outer-rectangle wavelength is:

```math
\lambda_{1.5}
=
\frac{1/1.5}{0.05}
\approx
13.33.
```

The core wavelength is:

```math
\lambda_2
=
\frac{0.5}{0.05}
=
10.
```

With unit spacing, the three materials contain approximately:

```text
20 points per wavelength
13.33 points per wavelength
10 points per wavelength
```

respectively.

The core exactly meets the configured ten-points-per-wavelength guideline.
A scenario test calculates the minimum resolution from the actual material
map and verifies it against `MIN_POINTS_PER_WAVELENGTH`.

---

## 20. Approximate propagation timing

The source-to-object distance is:

```math
110-60=50.
```

At background speed, the front face is reached at approximately:

```math
t=50,
```

or:

```math
\frac{50}{0.4}=125
```

steps.

Along the central horizontal path, the wave then traverses:

```text
20 outer-material cells before the core
25 core cells
15 outer-material cells after the core
```

The corresponding approximate travel times are:

```math
\frac{20}{2/3}=30,
```

```math
\frac{25}{1/2}=50,
```

and:

```math
\frac{15}{2/3}=22.5.
```

The estimated rear-face arrival time is:

```math
50+30+50+22.5=152.5,
```

or approximately:

```math
\frac{152.5}{0.4}\approx381
```

steps.

The headless propagation test advances to step 420, providing time for a
measurable transmitted field to emerge beyond the object.

---

## 21. Reusable geometry tests

Six tests protect the reusable geometry operations.

They verify:

1. The background array uses the configured background index.
2. The background array uses floating-point storage.
3. A general rectangle may touch grid edges.
4. Adding a rectangle returns a new array.
5. The original array remains unchanged.
6. Sequential rectangles compose correctly.
7. The second rectangle overwrites the first in overlapping cells.
8. The second result does not share memory with the first.
9. Empty, reversed, negative, and out-of-grid bounds are rejected.
10. Noninteger and boolean bounds are rejected.
11. Zero, negative, non-finite, and infinite material values are rejected.

The overlap test independently constructs the expected final array, including
the overwritten intersection.

---

## 22. Material finalization tests

Three tests protect material-map finalization.

They verify:

1. Wave speed is derived from the completed refractive-index array.
2. Integer input is converted safely to floating point.
3. The completed map does not share memory with the source array.
4. Later source-array mutation does not change the map.
5. Incorrect input shapes are rejected.
6. Non-finite refractive indices are rejected.
7. Nonpositive refractive indices are rejected.

These tests define the boundary between editable geometry construction and the
final map used by the simulation.

---

## 23. Composite scenario tests

Six tests protect the complete Phase 2.5 scenario.

They verify:

1. Grid, time, source, and boundary parameters.
2. Exact outer-region placement.
3. Exact core placement.
4. Last-operation-wins core overwrite.
5. The three expected refractive-index values.
6. Correct wave speed in every cell.
7. Strict nesting of the core.
8. Source and geometry placement outside the sponge.
9. Minimum wavelength resolution.
10. Valid simulation construction.
11. Ownership of the supplied material map.
12. Propagation into the core.
13. Propagation beyond the rear face.
14. Finite fields and energy history.
15. Absence of obvious runaway field growth.

The scenario tests import `create_scenario()` without loading Matplotlib.

---

## 24. Headless propagation check

The scenario is advanced for:

```text
420 steps
```

The core sampling region excludes five cells from each core edge:

```python
current[
    CORE_X_START + 5:CORE_X_STOP - 5,
    CORE_Y_START + 5:CORE_Y_STOP - 5,
]
```

The rear transmitted region begins five cells beyond the outer rectangle:

```python
current[
    OUTER_X_STOP + 5:,
    center_y - 10:center_y + 10,
]
```

Both regions must have:

```text
maximum absolute amplitude > 1e-3
```

The test also requires:

```text
step index = 420
energy-history length = 421
current field finite
previous field finite
energy history finite
current energy positive
maximum absolute field < 10
```

Representative diagnostic values at step 420 were:

```text
maximum absolute field              1.086
maximum core amplitude              0.211
maximum rear-center amplitude       0.237
total scalar-wave energy           53.684
```

These observations were used to select robust thresholds. They are not exact
regression targets.

---

## 25. Complete automated test result

The full command is:

```powershell
python -m unittest discover -s tests -v
```

The independently verified result was:

```text
Ran 50 tests

OK
```

The Phase 2.5 additions are:

```text
 3 material-finalization tests
 6 reusable-geometry tests
 6 composite-scenario tests
15 Phase 2.5 tests
```

Together with the previous:

```text
35 tests
```

the suite now contains:

```text
50 tests total
```

All uniform, planar-interface, embedded-rectangle, and Phase 2.1 numerical
regressions continue to pass.

---

## 26. Generic contour behavior

The completed composite map contains:

```text
unique refractive indices = [1.0, 1.5, 2.0]
```

The existing visualization derives midpoint contour levels:

```math
\frac{1.0+1.5}{2}=1.25
```

and:

```math
\frac{1.5+2.0}{2}=1.75.
```

These levels outline both:

- the outer `n=1.0` to `n=1.5` transition;
- the inner `n=1.5` to `n=2.0` transition.

No geometry constants are passed to the visualization. The two nested contours
are inferred from the final refractive-index array.

---

## 27. Interactive observations

The interactive scenario produced the expected qualitative behavior.

The confirmed observations were:

1. The material map contained a uniform background.
2. The outer rectangle appeared at the intended bounds.
3. The core appeared at the intended nested bounds.
4. The core correctly replaced the overlapping outer material.
5. Both material transitions were drawn automatically.
6. The point source produced circular incident wavefronts.
7. Part of the field reflected from the outer front face.
8. Part of the field entered the `n=1.5` region.
9. Part of the field entered the `n=2.0` core.
10. Wavelength decreased as refractive index increased.
11. Propagation slowed through the higher-index regions.
12. A measurable field emerged beyond the rear face.
13. Multiple internal interfaces produced a complex interference pattern.
14. Edge diffraction remained visible around the finite object.
15. No numerical instability or non-finite behavior was observed.

---

## 28. Figures

The composite material map was saved at:

```text
outputs/figures/phase_2/2026-07-30_composite_geometry_material_map.png
```

![Composite material map](../../../outputs/figures/phase_2/2026-07-30_composite_geometry_material_map.png)

Figure 1. Refractive-index map containing the `n=1.0` background, `n=1.5`
outer rectangle, and nested `n=2.0` core.

The final field was saved at:

```text
outputs/figures/phase_2/2026-07-30_composite_geometry_field.png
```

![Composite field](../../../outputs/figures/phase_2/2026-07-30_composite_geometry_field.png)

Figure 2. Field at step 600. Both material contours are visible, together with
reflection, transmission, diffraction, and internal interference. The
displayed total scalar-wave energy is approximately `66.5612`.

The energy history was saved at:

```text
outputs/figures/phase_2/2026-07-30_composite_geometry_energy.png
```

![Composite energy](../../../outputs/figures/phase_2/2026-07-30_composite_geometry_energy.png)

Figure 3. Total scalar-wave energy during continuous excitation. The curve
rises smoothly because the source continues to add energy while the sponge
removes part of the outgoing field.

---

## 29. Architecture decisions

The following decisions were made:

1. Compose refractive-index arrays before deriving wave speed.
2. Keep the solver independent of geometry operations.
3. Provide independent refractive-index validation.
4. Centralize material-map finalization.
5. Make a defensive copy during finalization.
6. Return a new array from every geometry operation.
7. Allow general rectangles to touch grid edges.
8. Preserve stricter validation in the embedded-object wrapper.
9. Use standard half-open NumPy bounds.
10. Define later operations as overwriting earlier operations.
11. Preserve all existing constructor signatures.
12. Refactor existing constructors to use the reusable pipeline.
13. Demonstrate composition with a nested core rather than unrelated objects.
14. Keep scenario construction headless-compatible.
15. Use broad propagation thresholds instead of fragile exact waveforms.
16. Accept array-copy overhead at the current project scale.

---

## 30. Problems and design tradeoffs

No numerical failure occurred during Phase 2.5.

The main design choice was whether geometry operations should mutate an array
in place or return a copy.

In-place mutation would reduce allocations, but it would also make
intermediate ownership and test isolation less explicit.

The selected rule was:

```text
geometry operations return new arrays
```

This matches the project's preference for explicit, progressively validated
state.

Another design choice concerned grid edges.

The Phase 2.4 rectangle represented an embedded object and therefore had to
remain strictly inside the grid. A general reusable operation must also be able
to represent slabs and full-height regions, so it permits edge contact.

The two contracts remain separate and are tested independently.

---

## 31. Current limitations

The Phase 2.5 implementation has the following limitations:

1. Reusable geometry currently supports only axis-aligned rectangles.
2. Rotated rectangles are not supported.
3. Circles, polygons, and curved boundaries are not supported.
4. Geometry uses grid indices rather than physical coordinates.
5. Overlap supports ordered replacement only.
6. Boolean union, intersection, and subtraction are not implemented.
7. Each geometry operation copies the complete array.
8. No serialized geometry description or scene file exists.
9. The scenario uses a point source rather than controlled plane-wave
   illumination.
10. Reflection and transmission remain qualitative.
11. The solver evolves only `E_z`.
12. Magnetic field components are not stored.
13. Magnetic permeability is spatially constant.
14. Materials remain lossless and nondispersive.
15. The sponge boundary is not a PML.
16. Figures are saved manually.

These limitations define a suitable boundary for Phase 2 material
infrastructure. Phase 2.6 will validate the full phase before later solver or
source improvements.

---

## 32. Phase 2.5 definition of done

```text
[x] Refractive-index arrays can be validated independently
[x] Material finalization is separated from geometry construction
[x] Finalization makes a defensive floating-point copy
[x] Wave-speed derivation has one reusable implementation
[x] A reusable background array can be created
[x] Rectangular regions can be applied sequentially
[x] Geometry operations leave their inputs unchanged
[x] General rectangles may touch grid edges
[x] Half-open bounds remain explicit
[x] Bounds and material values are validated
[x] Overlap behavior is explicitly last-operation-wins
[x] Overlap behavior has automated tests
[x] Existing uniform constructor remains compatible
[x] Existing planar-interface constructor remains compatible
[x] Existing embedded-rectangle constructor remains compatible
[x] Existing constructors use the reusable pipeline
[x] Composite three-material scenario exists
[x] Nested overwrite behavior is verified exactly
[x] Source and geometry remain outside the sponge
[x] All materials meet the wavelength-resolution guideline
[x] Wave propagation into the core is verified
[x] Rear-face transmission is verified
[x] Fields and energy remain finite
[x] Full suite passes with 50 tests
[x] Composite scenario was inspected interactively
[x] Representative material-map figure saved
[x] Representative field figure saved
[x] Representative energy figure saved
[x] Phase 2.5 simulation log created
[x] README updated for Phase 2.5
[x] Phase 2.5 commit created
[x] Phase 2.5 changes pushed to GitHub
```

Phase 2.5 implementation, validation, interactive inspection, figures,
documentation, and repository closeout are complete.

---

## 33. Next phase

The next planned phase is:

```text
Phase 2.6 - Phase validation
```

Phase 2.6 should consolidate and validate the complete Phase 2 material
infrastructure rather than immediately adding another geometry.

Planned work should include:

1. Reviewing all Phase 2 public APIs and naming.
2. Confirming uniform, planar, embedded, and composite construction contracts.
3. Verifying numerical compatibility with the Phase 2.1 regression.
4. Reviewing validation and error-message consistency.
5. Reviewing CFL and wavelength behavior across material maps.
6. Identifying duplicated tests or documentation gaps.
7. Defining the stable Phase 2 boundary.
8. Recording which improvements belong to future source, boundary, or Maxwell
   solver phases.
9. Creating a Phase 2 completion tag after validation.

---

## 34. Summary

Phase 2.5 transformed material construction from isolated geometry-specific
constructors into a reusable composition pipeline.

Geometry now builds only:

```text
n(x,y)
```

and finalization derives:

```text
c(x,y)
```

once the geometry is complete.

Reusable operations create a background array and add non-mutating,
half-open rectangular regions. Multiple operations compose sequentially, and
later operations deterministically overwrite earlier values in overlapping
cells.

The existing uniform, planar-interface, and embedded-rectangle constructors
remain compatible and now use the same internal pipeline.

The nested composite scenario demonstrates the complete workflow with:

```text
background n = 1.0
outer rectangle n = 1.5
core n = 2.0
```

The interactive simulation showed both interfaces, progressively shorter
wavelengths, slower internal propagation, transmission, diffraction, and
complex internal interference.

A headless 420-step check verified measurable field amplitude in the core and
beyond the rear face while all fields and energy values remained finite.

All 50 tests passed, including every previous material, scenario, and numerical
regression.

Phase 2.5 implementation, validation, figures, documentation, and repository
closeout are complete.