# Phase 4.1 — Geometry Conventions and Baseline

**Date:** 2026-08-20
**Status:** Implemented and core suite validated; visualization dependency unavailable

## Objective

Phase 4 extends the material infrastructure with advanced shapes and then uses
those shapes to construct photonic structures. Phase 4.1 establishes one
unambiguous geometry contract before individual shape algorithms are added.
It does not change the wave equation, finite-difference update, source,
boundary, monitor, or harmonic-analysis behavior validated in Phase 3.

## Coordinate convention

Material and field arrays retain shape `(nx, ny)`. Axis 0 is x and axis 1 is y.
Grid sample `(i, j)` has physical coordinates

```math
x_i=i\,\Delta x, \qquad y_j=j\,\Delta y.
```

The finite coordinate domain is therefore
`0 <= x <= (nx - 1) * dx` and `0 <= y <= (ny - 1) * dy`. The helper
`create_grid_coordinate_arrays` returns two arrays with `grid.shape` using
NumPy `ij` indexing. Geometry membership is evaluated at these grid samples;
the arrays are not interpreted as pixel cells with half-grid offsets.

## Mask convention

An advanced geometry operation is represented by a NumPy Boolean array with
exactly `grid.shape`. A true value selects a grid sample. Masks with another
shape or dtype are rejected. An empty mask is also rejected because silently
applying a shape that does not affect the domain is usually a configuration
error.

Shape constructors may extend beyond the coordinate domain. Clipping is
defined by evaluating membership only at the finite grid samples. A partially
visible shape therefore produces a naturally clipped mask. A completely
outside shape produces an empty mask and is rejected when applied.

## Boundary convention

Each shape must document a closed analytical membership rule: samples on its
mathematical boundary belong to the shape. Floating-point comparisons should
be expressed directly through that rule without an arbitrary global tolerance.
Axis-aligned index rectangles retain their established half-open NumPy slice
contract; this historical API is not reinterpreted as a physical-coordinate
shape.

## Composition convention

`add_masked_region` validates the input refractive-index array and mask, returns
a defensive floating-point copy, and changes only selected samples. The input
is never mutated. Geometry operations are ordered, and a later operation wins
where masks overlap. The result continues to require finite, positive
refractive indices.

Material finalization remains separate: compose regions in a refractive-index
array, then call `create_material_map_from_refractive_index` to derive the wave
speed and create a validated `MaterialMap`.

## Public foundation

Phase 4.1 adds these package-level functions:

- `create_grid_coordinate_arrays`;
- `validate_geometry_mask`;
- `add_masked_region`.

The existing rectangular functions and every Phase 1–3 public name remain
available without changed call signatures.

## Validation

Focused tests cover:

- anisotropic physical coordinate spacing and `(x, y)` array orientation;
- mask type, shape, Boolean dtype, and nonempty selection;
- immutable masked material assignment;
- later-operation-wins overlap behavior;
- finite, positive refractive-index validation.

The bundled Python 3.12 runtime executed 142 discovered tests. All 141 tests
that could import passed, including the Phase 2.1 numerical regression and all
new Phase 4.1 tests. The remaining visualization test module could not import
because that auxiliary runtime does not include Matplotlib. The repository's
checked-in virtual environment could not be launched in this execution session,
so the Matplotlib-dependent test remains to be rerun in the project environment.

## Next checkpoint

Phase 4.2 will use this contract to implement filled circular and elliptical
regions. Their centers and radii will use physical coordinates, their
boundaries will be closed, and partial out-of-domain shapes will follow the
clipping rule defined here.
