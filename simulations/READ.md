# Simulation Scenarios

The executable scenarios are grouped by scientific purpose rather than by the
phase in which they were introduced.

## Foundations

`foundations/` contains the default homogeneous scalar-wave simulation:

```powershell
python -m simulations.foundations.wave2d_basic
```

## Material geometries

`materials/` contains qualitative dielectric-material experiments:

```powershell
python -m simulations.materials.wave2d_planar_interface
python -m simulations.materials.wave2d_rectangular_dielectric
python -m simulations.materials.wave2d_composite_geometry
```

Each module exposes a headless-compatible `create_scenario()` function and an
interactive `main()` entry point.

The Phase 4.8 advanced-geometry gallery is a static material-map example, so
it separates map construction from figure generation instead of advancing a
wave simulation:

```powershell
python -m simulations.materials.wave2d_geometry_gallery.maps
python -m simulations.materials.wave2d_geometry_gallery.figures
```

The first command reports the six validated gallery cases. The second saves a
shared-scale comparison of the circle, ellipse, rotated rectangle, rotated
ellipse, concave polygon, and ordered composition under
`outputs/figures/phase_4/`.

## Controlled measurements

`measurements/` contains scenarios designed for monitor-based quantitative
analysis:

```powershell
python -m simulations.measurements.wave2d_controlled_line_source
python -m simulations.measurements.wave2d_interface_measurement
python -m simulations.measurements.wave2d_flux_propagation
python -m simulations.measurements.wave2d_flux_interface_transmission
```

The controlled-line-source module validates propagation in a uniform medium.
The interface-measurement module runs matched reference and dielectric
experiments and derives harmonic scattering estimates.

The scalar-flux propagation module launches a symmetric finite-aperture line
source in a uniform medium. Indexed face monitors verify negative left-going
power, positive right-going power, approximate launch symmetry, and
consistency between downstream measurement planes.

The scalar interface-transmission module runs a uniform reference and a
planar-interface experiment with identical source, grid, boundary, and flux-
monitor configurations. Dividing the transmitted mean power in the interface
run by the power at the same face in the reference run gives a measured scalar
transmission of approximately `0.95275` for `n = 1.0 -> 1.5`, compared with
the analytical value `0.96`. The approximately `0.76%` relative error is
within the scenario's `2%` validation tolerance.

## Photonic structures

Scenarios that require multiple related modules live in dedicated subfolders
under `structures/`. The straight-waveguide package contains separate
simulation and documentation-figure entry points:

```powershell
python -m simulations.structures.wave2d_straight_waveguide.simulation
python -m simulations.structures.wave2d_straight_waveguide.figures
```

The first command runs and reports the matched uniform-reference and dielectric-
waveguide experiment. The second saves the material layout, RMS-field
comparison, monitor histories, and harmonic-response comparison under
`outputs/figures/phase_4/`.

Run module commands from the repository root so the top-level `wavesim`
package is importable.

The Phase 4.7 directional-coupler package contains a matched isolated-guide
reference and parallel-guide coupling experiment:

```powershell
python -m simulations.structures.wave2d_directional_coupler.simulation
```

The source excites only the upper guide. Upstream and downstream upper/lower
monitor windows measure the evolution of scalar harmonic field transfer along
the coupled structure.

Generate the Phase 4.7 documentation figures with:

```powershell
python -m simulations.structures.wave2d_directional_coupler.figures
```

The generator saves the coupled material layout, matched RMS-field comparison,
monitor histories, and harmonic-response comparison under
`outputs/figures/phase_4/`.
