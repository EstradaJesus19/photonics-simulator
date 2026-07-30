# 2026-07-30 - Phase 2.6 Phase Validation

## 1. Goal

The goal of Phase 2.6 was to validate and stabilize the complete Phase 2
material infrastructure.

This was intentionally a consolidation phase rather than a feature phase.

The primary questions were:

1. Is the supported Phase 2 API explicit?
2. Do the compatibility constructors match the reusable pipeline?
3. Do all official scenarios satisfy the same material contract?
4. Are all official scenarios CFL stable?
5. Do all driven scenarios meet the wavelength-resolution guideline?
6. Can every official material map construct a valid simulation?
7. Does the scalar-wave energy remain approximately conserved without a
   source or sponge loss?
8. Do all previous regressions still pass?
9. Is the codebase ready to define Phase 2 as complete?

No new geometry, source, boundary condition, or field equation was added.

---

## 2. Phase context

The Phase 2 sequence is:

```text
Phase 2.1 - Modular refactor                 Complete
Phase 2.2 - Uniform material map             Complete
Phase 2.3 - Planar dielectric interface      Complete
Phase 2.4 - Rectangular dielectric region    Complete
Phase 2.5 - Reusable geometry functions      Complete
Phase 2.6 - Phase validation                 Implemented and verified
```

Phase 2 progressed from a uniform scalar solver to a reusable material system:

```text
Phase 2.1
    reusable package structure

Phase 2.2
    spatial refractive-index and wave-speed arrays

Phase 2.3
    first discontinuous planar material

Phase 2.4
    first finite dielectric object

Phase 2.5
    reusable geometry composition

Phase 2.6
    cross-cutting validation and stabilization
```

---

## 3. Baseline before validation

At the start of Phase 2.6:

```text
branch = main
local main = origin/main
working tree = clean
latest commit = f122d12
```

The latest commit was:

```text
f122d12 Add reusable material geometry composition
```

The existing suite contained:

```text
50 tests
```

All 50 tests passed before Phase 2.6 changes were introduced.

---

## 4. Files added or modified

Modified package exports:

```text
wavesim/__init__.py
```

New cross-cutting validation tests:

```text
tests/test_phase2_validation.py
```

New phase-validation log:

```text
notes/simulation-logs/phase_2/2026-07-30_005_phase_2_validation.md
```

The README remains a Phase 2.6 closeout item.

No change was required in:

```text
wavesim/config.py
wavesim/materials.py
wavesim/solver.py
wavesim/visualization.py
simulations/
```

---

## 5. Stable public API

The initial audit found one public-API inconsistency.

`wavesim.__init__` exported most configuration dataclasses but did not export:

```python
MaterialConfig
```

It also did not expose the material-map and geometry functions introduced
throughout Phase 2.

Phase 2.6 defines the supported package-level API explicitly through:

```python
wavesim.__all__
```

The stable Phase 2 names are:

```text
BoundaryConfig
GridConfig
InitialConditionConfig
MaterialConfig
MaterialMap
SimulationConfig
SimulationState
SourceConfig
TimeConfig
VisualizationConfig
Wave2DSimulation
add_rectangular_region
create_background_refractive_index_array
create_default_config
create_material_map_from_refractive_index
create_planar_interface_material_map
create_rectangular_material_map
create_uniform_material_map
validate_material_map
validate_refractive_index_array
```

Existing imports from submodules remain valid. The package-level exports are
an additional stable access path.

---

## 6. Public-API validation

The test:

```python
test_expected_phase2_names_are_public
```

checks every supported name using:

```python
self.assertIn(name, wavesim.__all__)
self.assertTrue(hasattr(wavesim, name))
```

This protects against:

- accidentally removing a supported symbol;
- forgetting to import a symbol into the package namespace;
- allowing `__all__` and the actual module attributes to diverge.

The test checks the expected API as a subset, so future intentional additions
do not break it.

---

## 7. Constructor compatibility goal

Phase 2.5 refactored the older geometry-specific constructors to use the
reusable material pipeline.

Phase 2.6 verifies that the convenience constructors remain numerically
equivalent to constructing the same maps manually.

The compared paths are:

```text
compatibility wrapper
        versus
background array
    + reusable geometry operation
    + material finalization
```

The comparison checks both:

```text
refractive_index
wave_speed
```

---

## 8. Uniform-constructor equivalence

The uniform wrapper:

```python
create_uniform_material_map(
    grid,
    material,
)
```

is compared with:

```python
refractive_index = (
    create_background_refractive_index_array(
        grid,
        material,
    )
)

expected = create_material_map_from_refractive_index(
    grid,
    material,
    refractive_index,
)
```

The arrays are exactly equivalent.

---

## 9. Planar-constructor equivalence

The planar wrapper:

```python
create_planar_interface_material_map(
    grid,
    material,
    interface_index=4,
    right_refractive_index=1.75,
)
```

is compared with a reusable full-height rectangular operation:

```python
refractive_index = add_rectangular_region(
    refractive_index,
    grid,
    x_start=4,
    x_stop=grid.nx,
    y_start=0,
    y_stop=grid.ny,
    region_refractive_index=1.75,
)
```

This verifies that a vertical slab created by the general geometry function is
equivalent to the dedicated Phase 2.3 interface constructor.

---

## 10. Embedded-rectangle equivalence

The embedded wrapper:

```python
create_rectangular_material_map(
    grid,
    material,
    x_start=2,
    x_stop=6,
    y_start=2,
    y_stop=5,
    rectangle_refractive_index=2.0,
)
```

is compared with the same bounds applied through:

```python
add_rectangular_region(...)
```

followed by:

```python
create_material_map_from_refractive_index(...)
```

The wrapper retains its stricter validation while producing the same valid
map as the reusable pipeline.

---

## 11. Official scenario matrix

The validation suite constructs four official Phase 2 cases:

```text
uniform
planar interface
embedded rectangle
nested composite
```

The cases are created from:

```python
create_default_config()
create_planar_scenario()
create_rectangle_scenario()
create_composite_scenario()
```

The uniform case constructs its map using:

```python
create_uniform_material_map(...)
```

All other cases use their dedicated headless scenario constructors.

---

## 12. Shared material contract

Every official scenario must satisfy:

```text
refractive_index.shape == grid.shape
wave_speed.shape == grid.shape
all refractive-index values finite
all refractive-index values positive
all wave-speed values finite
all wave-speed values positive
```

Each map is passed through:

```python
validate_material_map(
    material_map,
    config.grid,
)
```

The suite also verifies the physical material relationship:

```math
c(x,y)
=
\frac{c_{\mathrm{ref}}}{n(x,y)}
```

for every cell in every official map.

This is stronger than checking only the presence of valid positive arrays. It
confirms that the official Phase 2 construction paths preserve the selected
refractive-index relationship.

---

## 13. Scenario material summary

The validated material ranges are:

```text
Uniform scenario
    n = 1.0
    c = 1.0

Planar-interface scenario
    n = 1.0 and 1.5
    c = 1.0 and 0.667

Embedded-rectangle scenario
    n = 1.0 and 1.5
    c = 1.0 and 0.667

Composite scenario
    n = 1.0, 1.5, and 2.0
    c = 1.0, 0.667, and 0.5
```

The composite scenario therefore provides the strictest wavelength-resolution
case.

---

## 14. Cross-scenario CFL validation

For each official scenario, Phase 2.6 calculates:

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

Every official scenario uses:

```text
c_max = 1.0
dt = 0.4
dx = 1.0
dy = 1.0
```

Therefore:

```math
C
=
0.4\sqrt{2}
\approx
0.566.
```

The validation requires:

```math
C\le1.
```

All official Phase 2 scenarios pass.

---

## 15. Cross-scenario wavelength validation

For every driven scenario, the validation calculates:

```math
\lambda_{\min}
=
\frac{c_{\min}}{f}
```

and:

```math
N_{\lambda,\min}
=
\frac{\lambda_{\min}}
{\max(\Delta x,\Delta y)}.
```

The minimum points per wavelength are:

```text
Uniform default
    c_min = 1.0
    f = 0.075
    points per wavelength = 13.33

Planar interface
    c_min = 0.667
    f = 0.05
    points per wavelength = 13.33

Embedded rectangle
    c_min = 0.667
    f = 0.05
    points per wavelength = 13.33

Composite
    c_min = 0.5
    f = 0.05
    points per wavelength = 10
```

Every case satisfies:

```python
minimum_points_per_wavelength
>= MIN_POINTS_PER_WAVELENGTH
```

where:

```text
MIN_POINTS_PER_WAVELENGTH = 10
```

---

## 16. Cross-scenario simulation construction

Every official configuration and material map is supplied to:

```python
Wave2DSimulation(
    config,
    material_map=material_map,
)
```

The validation checks:

```text
the simulation retains the supplied map
the field shape equals grid.shape
the initial energy is finite
```

This confirms that all Phase 2 material construction paths remain compatible
with the solver boundary.

The validation is headless and does not import Matplotlib.

---

## 17. Why an energy-conservation check was added

The driven scenarios are useful for scattering visualization, but their energy
histories combine:

- continuous source injection;
- sponge removal;
- numerical evolution.

They cannot isolate conservative behavior.

Phase 2.6 therefore adds one source-free composite test with:

```text
initial condition = Gaussian
source = none
boundary = fixed
steps = 300
```

The Gaussian begins at:

```text
(60, 80)
```

and propagates toward the nested composite object.

Fixed boundaries remove sponge loss, and disabling the source removes external
energy injection.

---

## 18. Energy diagnostic under validation

The scalar-wave energy is:

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

The test normalizes the complete energy history using:

```python
relative_energy = (
    energy_history
    / simulation.initial_energy
)
```

It requires:

```text
initial energy > 0
normalization enabled
all energy values finite
energy-history length = 301
maximum relative drift < 5%
```

---

## 19. Measured source-free energy result

The measured values were:

```text
Initial energy             1.5605401816
Final energy               1.5568852155
Final relative energy      0.9976578840
Minimum relative energy    0.9720232760
Maximum relative energy    1.0125209664
Maximum absolute drift     0.0279767240
```

Therefore, the maximum observed deviation was approximately:

```text
2.80%
```

and the final energy differed from the initial energy by approximately:

```text
0.23%
```

The measured maximum remains comfortably below the selected:

```text
5% smoke-test threshold
```

---

## 20. Interpretation of the energy tolerance

The current energy diagnostic approximates the continuous scalar-wave energy.
It is not an exactly conserved discrete invariant of the leapfrog update.

Some step-to-step oscillation and numerical drift are therefore expected.

The 5% threshold:

- is broad enough to tolerate the observed 2.8% numerical variation;
- is narrow enough to detect meaningful conservation regressions;
- applies only to the defined fixed-boundary, source-free composite case;
- does not claim exact electromagnetic energy conservation.

The solver still does not explicitly store \(H_x\) or \(H_y\), so this is not
the complete Maxwell energy.

---

## 21. Phase 2.6 test additions

Phase 2.6 adds:

```text
1 public-API test
3 constructor-equivalence tests
4 cross-scenario contract tests
1 source-free energy test
```

This gives:

```text
9 Phase 2.6 tests
```

The previous suite contained:

```text
50 tests
```

The final Phase 2 suite therefore contains:

```text
59 tests
```

---

## 22. Complete test result

The full command is:

```powershell
python -m unittest discover -s tests -v
```

The independently verified result was:

```text
Ran 59 tests

OK
```

The complete suite includes:

- the Phase 2.1 numerical regression;
- uniform material behavior;
- material-array validation;
- supplied-map integration;
- spatially varying time stepping;
- material-aware energy;
- maximum-speed CFL validation;
- planar-interface behavior;
- embedded-rectangle behavior;
- reusable geometry composition;
- overlap precedence;
- composite scenario behavior;
- the stable public API;
- compatibility-wrapper equivalence;
- cross-scenario material invariants;
- cross-scenario CFL and wavelength validation;
- source-free composite energy behavior.

---

## 23. Syntax and import audit

Every Python file under:

```text
wavesim/
simulations/
tests/
```

was compiled in memory using Python's built-in `compile()` function.

The result was:

```text
Compiled 16 Python files successfully
```

The following also imported successfully without Matplotlib:

```text
wavesim public package
planar scenario constructor
embedded-rectangle scenario constructor
composite scenario constructor
```

Each scenario constructor executed successfully during the import audit.

---

## 24. Repository-quality audit

The following checks were performed:

```text
git diff --check
scan for TODO
scan for FIXME
scan for XXX
scan for HACK
```

No whitespace error was reported.

No unresolved marker was found in:

```text
wavesim/
simulations/
tests/
README.md
notes/
```

Git reported a normal line-ending notice for `wavesim/__init__.py`:

```text
LF will be replaced by CRLF the next time Git touches it
```

This is a Windows line-ending normalization notice, not a code or whitespace
failure.

---

## 25. Validated Phase 2 architecture

The validated dependency direction remains:

```text
config
    |
    v
materials
    |
    v
solver
    |
    v
visualization
    |
    v
scenario entry points
```

The responsibilities are:

```text
config.py
    immutable configuration
    validation
    CFL and wavelength reporting

materials.py
    refractive-index arrays
    geometry composition
    wave-speed derivation
    material validation

solver.py
    finite-difference evolution
    source and boundary handling
    energy diagnostics

visualization.py
    material and damping figures
    interface contours
    animation and energy plots

simulations/
    reproducible scenario definitions
    thin interactive entry points
```

The solver remains independent of geometry-specific coordinates.

---

## 26. Phase 2 validated capabilities

At the end of Phase 2, the project supports:

1. A modular, headless-compatible scalar-wave solver.
2. Frozen simulation configuration.
3. Validated refractive-index arrays.
4. Validated wave-speed arrays.
5. Uniform material maps.
6. Vertical planar interfaces.
7. Strictly embedded rectangular dielectrics.
8. Reusable rectangular geometry composition.
9. Edge-touching general rectangles and slabs.
10. Multiple and nested material regions.
11. Deterministic overlap precedence.
12. Defensive material-map finalization.
13. Optional supplied-map injection.
14. Maximum-speed CFL validation.
15. Material-aware finite-difference stepping.
16. Material-aware scalar-wave energy.
17. Generic material-interface contours.
18. Headless official scenario construction.
19. Propagation verification across discontinuous materials.
20. A documented and tested public package API.

---

## 27. Scientific validation boundary

The validated solver is a reduced second-order \(E_z\) model:

```math
E_{z,tt}
=
c(x,y)^2\nabla^2E_z.
```

The validation supports qualitative conclusions about:

- reflection;
- transmission;
- refraction;
- wavelength reduction;
- slower propagation in higher-index media;
- scattering from finite objects;
- diffraction around material edges;
- internal interference.

It does not validate:

- quantitative Fresnel coefficients;
- full vector electromagnetic fields;
- spatially varying magnetic permeability;
- material dispersion;
- material loss;
- PML performance;
- complete Maxwell energy;
- TE/TM FDTD updates.

Those claims remain outside the Phase 2 boundary.

---

## 28. Geometry boundary

Phase 2 validates reusable composition of axis-aligned rectangular regions.

This already expresses:

- vertical slabs;
- horizontal slabs;
- embedded rectangles;
- nested rectangles;
- multiple separated rectangles;
- overlapping rectangles.

Phase 2 does not include:

- circles;
- ellipses;
- rotated rectangles;
- polygons;
- arbitrary masks;
- physical-coordinate geometry.

A future geometry library should build these shapes through a reusable masked
region operation rather than adding shape-specific material logic to the
solver.

---

## 29. Known design limitations

The validated Phase 2 design retains the following limitations:

1. `MaterialMap` arrays are mutable NumPy arrays.
2. A supplied map should be treated as immutable after simulation
   construction.
3. Geometry operations copy the complete refractive-index array.
4. Geometry uses grid indices rather than physical coordinates.
5. Overlap supports ordered replacement only.
6. Figures are saved manually.
7. Scenario parameters are encoded in Python modules rather than external
   files.
8. The point source emits circular waves over many angles.
9. The sponge is not a PML.
10. The model is scalar rather than full-vector Maxwell FDTD.

These limitations are documented rather than silently hidden.

---

## 30. Why no new figure was required

Phase 2.6 adds validation rather than a new physical scenario.

The existing Phase 2 figures already cover:

```text
uniform material behavior
planar interface
embedded rectangular object
nested composite geometry
energy histories
material and sponge profiles
```

The source-free energy validation is represented numerically by an automated
test rather than another manually saved figure.

No new Phase 2.6 figure is required for the phase definition of done.

---

## 31. Phase 2 definition of done

```text
[x] Phase 2.1 modular refactor complete
[x] Phase 2.2 uniform material maps complete
[x] Phase 2.3 planar dielectric interface complete
[x] Phase 2.4 rectangular dielectric region complete
[x] Phase 2.5 reusable geometry functions complete
[x] Stable Phase 2 public API defined
[x] Public API protected by automated tests
[x] Compatibility wrappers match reusable composition
[x] All official maps satisfy the material contract
[x] All official scenarios satisfy CFL stability
[x] All driven scenarios meet wavelength resolution
[x] All official scenarios construct valid simulations
[x] Source-free composite energy remains within 5%
[x] Phase 2.1 numerical regression remains protected
[x] Full suite passes with 59 tests
[x] All Python files compile
[x] All scenario constructors import headlessly
[x] No unresolved TODO or FIXME markers remain
[x] Phase 2.6 validation log created
[x] README updated for Phase 2 completion
[x] Phase 2.6 commit created
[x] Phase 2.6 changes pushed to GitHub
[x] phase-2-complete tag created
[x] phase-2-complete tag pushed to GitHub
```

Phase 2 implementation, technical validation, README, repository closeout, and
milestone tagging are complete.

---

## 32. Next planned work

After Phase 2 closeout, the recommended next project phase is a geometry
library built on the validated material infrastructure.

The preferred foundation is:

```python
add_masked_region(
    refractive_index,
    grid,
    mask,
    region_refractive_index,
)
```

Shape-specific functions can then produce masks for:

- circles;
- ellipses;
- rotated rectangles;
- polygons;
- imported or procedurally generated structures.

Alternative future work includes:

- controlled line, beam, or plane-wave sources;
- quantitative reflection and transmission measurements;
- improved absorbing boundaries and PML;
- conservative interface discretizations;
- TE and TM electromagnetic FDTD solvers.

The geometry library is the most direct continuation of the newly validated
composition architecture.

---

## 33. Completion and tagging plan

After the README is updated, the Phase 2.6 changes should be committed and
pushed.

The completed Phase 2 state should then receive the annotated tag:

```text
phase-2-complete
```

The tag should identify the exact commit containing:

- the stable public API;
- all 59 tests;
- the Phase 2.6 validation log;
- the completed README;
- the full Phase 2 roadmap closeout.

The tag should be pushed explicitly so GitHub records the milestone.

---

## 34. Summary

Phase 2.6 validated the complete Phase 2 material infrastructure without
adding another feature.

The public package API is now explicit and protected.

The uniform, planar-interface, and embedded-rectangle compatibility
constructors are numerically equivalent to the reusable geometry pipeline.

Uniform, planar, rectangular, and composite scenarios all satisfy:

```text
valid material-array shapes
finite positive material values
c = c_ref / n
CFL stability
wavelength resolution
solver construction
```

A source-free, fixed-boundary composite simulation retained energy within a
maximum measured deviation of approximately 2.8%, below the protected 5%
threshold.

All 59 tests passed. All 16 Python files compiled successfully. All official
scenario constructors imported and executed headlessly. No unresolved work
markers or whitespace failures were found.

Phase 2 implementation, technical validation, documentation, repository
closeout, and milestone tagging are complete.