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

## Controlled measurements

`measurements/` contains scenarios designed for monitor-based quantitative
analysis:

```powershell
python -m simulations.measurements.wave2d_controlled_line_source
python -m simulations.measurements.wave2d_interface_measurement
```

The controlled-line-source module validates propagation in a uniform medium.
The interface-measurement module runs matched reference and dielectric
experiments and derives harmonic scattering estimates.

Run module commands from the repository root so the top-level `wavesim`
package is importable.
