# Phase 4.7 — Two-Dimensional Directional Coupler

Date: 2026-08-27

## 1. Objective

Phase 4.7 introduces the first coupled photonic structure in the project.

The experiment demonstrates that two nearby dielectric waveguides can
exchange scalar field through their spatially overlapping fields. A source
excites only the upper guide, while matched monitor windows measure the field
distribution in both guide locations at two longitudinal positions.

The coupled result is compared with an isolated upper-guide reference using
identical numerical and measurement configurations.

---

## 2. Structure

Both configurations use a background refractive index of 1.0 and an upper
straight core with refractive index 1.5.

The isolated reference contains:

```text
one upper dielectric core
```

The directional coupler contains:

```text
one upper dielectric core
one parallel lower dielectric core
```

The nominal geometric parameters are:

```text
upper-core center y = 90
lower-core center y = 76
core height = 12 grid units
center separation = 14 grid units
core gap = 2 grid units
```

The source excites only the upper core.

Because the isolated reference has no lower core, its lower monitor represents
the same spatial window occupied by the lower core in the coupled experiment.
It must not be described as an isolated lower-guide measurement.

---

## 3. Numerical configuration

```text
grid size = 220 x 160
time step = 0.4
simulation steps = 900
sponge width = 20 cells

source kind = finite-aperture sinusoidal line source
source x = 35
source y indices = [85, 96)
source amplitude = 0.5
source frequency = 0.05
source ramp = 4 cycles

analysis steps = [750, 900)
analysis samples = 150
analysis duration = 60
analysis cycles = 3
```

The shortest material wavelength is represented by at least ten grid points,
and the material maps satisfy the existing Courant stability requirement.

---

## 4. Monitor configuration

Four matched vertical-line monitors are used:

```text
first_upper
    x = 90
    y indices = [85, 96)

first_lower
    x = 90
    y indices = [71, 82)

second_upper
    x = 170
    y indices = [85, 96)

second_lower
    x = 170
    y indices = [71, 82)
```

The first pair measures the upstream distribution. The second pair measures
the downstream distribution.

All source and monitor windows remain outside the sponge region.

---

## 5. Measured results

The harmonic-response amplitudes obtained from the three-cycle analysis
window are approximately:

```text
Isolated upper-guide reference
    second_upper = 6.517580
    second_lower = 0.971112
    downstream lower/upper ratio = 0.148999

Directional coupler
    first_upper = 5.312592
    first_lower = 1.386550
    upstream lower/upper ratio = 0.260993

    second_upper = 0.340765
    second_lower = 6.171113
    downstream lower/upper ratio = 18.109586

Matched comparison
    downstream lower-window enhancement = 6.354690
```

The normalized lower-window amplitude shares are approximately:

```text
isolated downstream = 0.130
coupled upstream = 0.207
coupled downstream = 0.948
```

The lower-window enhancement compares the downstream lower spatial window in
the coupled experiment with the identical downstream spatial window in the
isolated reference.

---

## 6. Interpretation

In the isolated reference, the downstream response remains dominated by the
upper guide.

In the coupled structure, the lower-to-upper amplitude ratio increases
between the upstream and downstream monitor positions. At the downstream
position, the lower guide dominates the measured scalar field.

This behavior is consistent with directional coupling. Excitation localized
in one guide can be represented by coupled spatial components whose relative
phase changes during propagation. Their interference changes where the field
is concentrated, producing a transfer between the guides.

The present experiment demonstrates spatial scalar-field redistribution. It
does not calculate electromagnetic modal power or a conserved coupling
efficiency.

---

## 7. Visualization

Four reproducible figures were generated:

```text
outputs/figures/phase_4/2026-08-25_directional_coupler_material_map.png
outputs/figures/phase_4/2026-08-25_directional_coupler_rms_comparison.png
outputs/figures/phase_4/2026-08-25_directional_coupler_monitor_histories.png
outputs/figures/phase_4/2026-08-25_directional_coupler_response_comparison.png
```

They document:

1. the dielectric cores, source, and monitor layout;
2. the matched isolated and coupled RMS fields;
3. the four coupled monitor histories and analysis window;
4. the downstream amplitudes and normalized spatial redistribution.

All four generated artifacts were visually inspected.

---

## 8. Validation

The directional-coupler scenario contains 16 focused configuration and
propagation tests.

They verify:

- the grid, source, timing, boundary, and monitor configuration;
- the positive two-cell core gap;
- construction of the isolated and coupled material maps;
- source placement inside the upper core;
- monitor alignment with the selected spatial windows;
- separation of the two core masks;
- avoidance of the sponge by active measurement components;
- the three-cycle harmonic-analysis window;
- Courant stability and wavelength resolution;
- complete and finite monitor histories;
- detection of nonzero field at all coupled monitors;
- upper-guide dominance in the isolated reference;
- increasing lower-to-upper response during coupled propagation;
- downstream lower-guide dominance;
- enhancement of the downstream lower spatial window.

All 16 focused numerical tests pass.

A separate Matplotlib-dependent validation test verifies creation of all four
documentation figures. The available fallback runtime did not contain
Matplotlib, but the project environment generated the expected PNG files and
the artifacts were inspected manually. A complete Matplotlib-enabled suite
run remains part of the Phase 4 closeout audit.

Run the focused checks with:

```powershell
python -m unittest tests.scenarios.test_directional_coupler_scenario -v
python -m unittest tests.validation.test_coupler_figure_generation -v
```

---

## 9. Files added

Directional-coupler scenario:

```text
simulations/structures/wave2d_directional_coupler/__init__.py
simulations/structures/wave2d_directional_coupler/simulation.py
simulations/structures/wave2d_directional_coupler/figures.py
```

Focused tests:

```text
tests/scenarios/test_directional_coupler_scenario.py
tests/validation/test_coupler_figure_generation.py
```

Generated figures:

```text
outputs/figures/phase_4/2026-08-25_directional_coupler_material_map.png
outputs/figures/phase_4/2026-08-25_directional_coupler_rms_comparison.png
outputs/figures/phase_4/2026-08-25_directional_coupler_monitor_histories.png
outputs/figures/phase_4/2026-08-25_directional_coupler_response_comparison.png
```

Repository documentation extended:

```text
README.md
simulations/READ.md
notes/simulation-logs/READ.md
```

---

## 10. Scientific limitations

The experiment retains the limitations of the current solver:

- the simulated field is a scalar quantity interpreted as $E_z$;
- the solver is not a full-vector Maxwell FDTD implementation;
- the line source is not a calculated waveguide eigenmode source;
- the experiment does not explicitly solve the coupled supermodes;
- monitors record spatially averaged scalar field rather than transverse flux;
- amplitude ratios and shares are not power coefficients;
- the selected gap and propagation length represent one configuration rather
  than a parameter sweep;
- the finite grid and sponge influence the measured response.

The results should therefore be interpreted as a controlled demonstration of
coupled scalar-field redistribution.

---

## 11. Completion status

- [x] Matched isolated-guide reference constructed
- [x] Parallel two-guide structure constructed
- [x] Upper guide excited independently
- [x] Upstream and downstream guide windows monitored
- [x] Numerical constraints validated
- [x] Downstream transfer detected
- [x] Lower guide shown to dominate downstream
- [x] Matched lower-window enhancement calculated
- [x] Reproducible figure generator added
- [x] Figures generated and visually inspected
- [x] Focused scenario tests passed
- [x] Repository documentation updated

Phase 4.7 is complete.

---

## 12. Next checkpoint

The next checkpoint is:

```text
Phase 4.8 — Visualization and reproducible examples
```

This checkpoint should review the complete Phase 4 visualization workflow,
ensure that official advanced-geometry and structure examples can be
reproduced headlessly, and organize the final documentation artifacts before
the Phase 4 closeout audit.
