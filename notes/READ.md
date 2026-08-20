# Technical Notes Index

The topical notes in this directory do not all describe the same project
checkpoint. This index distinguishes foundational explanations, completed
design records, and current technical references.

## Document roles

| Note | Role | Scope |
| --- | --- | --- |
| [Finite Difference Method](mathematics/01_finite_difference_method.md) | Foundational note | Phase 1 derivation, with implementation updates verified through Phase 3 |
| [Harmonic Response Analysis](mathematics/02_harmonic_response_analysis.md) | Current technical reference | Phase 3 monitor-history and harmonic analysis |
| [The Two-Dimensional Wave Equation](physics/01_2d_wave_equation.md) | Foundational note | Physical interpretation of the homogeneous Phase 1 model |
| [$E_z$-Polarized Dielectric Interface Model](physics/02_ez_dielectric_interface_model.md) | Completed design record | Phase 2.3 model choice and interface contract, with a Phase 3 status update |
| [Controlled Sources and Field Monitors](physics/03_controlled_sources_and_field_monitors.md) | Current technical reference | Phase 3 source, monitor, and scattering-measurement model |

## Maintenance policy

- Foundational notes preserve the assumptions and teaching sequence of the
  phase in which the model was introduced. Statements about the current code
  are updated or explicitly scoped to that phase.
- Completed design records preserve the reasoning and limits of the original
  decision. A status note identifies which planned work was later completed.
- Current technical references describe the latest validated implementation
  and should evolve when that implementation changes.
- Historical experiment results belong in
  [simulation logs](simulation-logs/READ.md). Those records are not rewritten
  merely because the project later evolves.

For the project-wide overview and public API, see the root
[README](../README.md).
