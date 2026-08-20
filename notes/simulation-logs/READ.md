# Simulation Logs

This directory contains the technical development record of the Photonics
Simulator project.

The logs record:

- what was implemented;
- why it was implemented;
- the numerical and physical parameters used;
- automated and manual validation;
- observed behavior;
- problems and rejected approaches;
- scientific limitations;
- decisions that define the next checkpoint.

They serve as a chronological lab notebook. Mathematics and physics notes
explain reusable concepts, while simulation logs preserve the state and
reasoning of a particular development milestone.

---

## Current structure

```text
notes/simulation-logs/
|-- READ.md
|-- phase_1/
|   |-- 2026-05-21_001_project_setup.md
|   |-- 2026-05-22_001_first_wave_simulation.md
|   |-- 2026-06-17_001_sponge_and_energy_diagnostic.md
|   `-- 2026-07-21_006_continuous_point_source.md
|-- phase_2/
|   |-- 2026-07-28_001_uniform_material_map.md
|   |-- 2026-07-28_002_planar_dielectric_interface.md
|   |-- 2026-07-29_003_rectangular_dielectric_region.md
|   |-- 2026-07-30_004_reusable_geometry_functions.md
|   `-- 2026-07-30_005_phase_2_validation.md
`-- phase_3/
    `-- 2026-08-04_001_controlled_sources_and_field_monitors.md
```

---

## Phase index

### Phase 1 — Scalar-wave foundations

- `2026-05-21_001_project_setup.md` records the initial project structure and
  environment.
- `2026-05-22_001_first_wave_simulation.md` records the first finite-difference
  field evolution.
- `2026-06-17_001_sponge_and_energy_diagnostic.md` documents damping and the
  scalar-wave energy diagnostic.
- `2026-07-21_006_continuous_point_source.md` documents the continuous
  sinusoidal point source inherited by later phases.

### Phase 2 — Material infrastructure

- `2026-07-28_001_uniform_material_map.md` introduces explicit material maps.
- `2026-07-28_002_planar_dielectric_interface.md` introduces the first
  dielectric interface.
- `2026-07-29_003_rectangular_dielectric_region.md` introduces a finite
  dielectric object.
- `2026-07-30_004_reusable_geometry_functions.md` separates reusable geometry
  composition from material finalization.
- `2026-07-30_005_phase_2_validation.md` records the Phase 2 public API,
  scenario matrix, regression status, and milestone validation.

### Phase 3 — Controlled sources and field monitors

- `2026-08-04_001_controlled_sources_and_field_monitors.md` records source
  profiles, the ramped finite-aperture line source, field monitors, harmonic
  analysis, controlled propagation, paired interface measurement,
  visualization, limitations, and closeout status.

---

## Naming convention

Log files use:

```text
YYYY-MM-DD_sequence_short_description.md
```

where:

- `YYYY-MM-DD` is the date of the recorded checkpoint;
- `sequence` orders multiple records created on the same date or within the
  same development series;
- `short_description` identifies the primary experiment or milestone.

The existing sequence numbers are historical identifiers and are not required
to be contiguous across dates.

---

## Historical-record policy

Simulation logs are historical records. Later phases should not silently
rewrite an older log to make it appear as if newer infrastructure already
existed.

Use the following policy:

- preserve historical implementation descriptions and measured results;
- correct simple spelling or broken-link problems when needed;
- add a clearly dated erratum for a substantive factual error;
- link to a newer mathematics or physics note when the interpretation has
  evolved;
- keep the root README current and the scope and status of topical notes
  accurate.

This preserves development history while allowing the topical technical
documentation to improve.

---

## Relationship to topical notes

Foundational derivations, completed model decisions, and current scientific
interpretations belong in:

```text
notes/mathematics/
notes/physics/
```

Their individual roles and maintenance policy are listed in the
[Technical Notes Index](../READ.md).

The Phase 3 topics are explained in:

```text
notes/mathematics/02_harmonic_response_analysis.md
notes/physics/03_controlled_sources_and_field_monitors.md
```

The Phase 3 simulation log should be read as the implementation and validation
record; the two topical notes provide the reusable mathematical and physical
explanations.
