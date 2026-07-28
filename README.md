# Photonics Simulator

A Python toolkit for learning about, numerically simulating, and visualizing
two-dimensional wave propagation.

The project is being developed progressively. It begins with a scalar wave
equation and establishes the numerical and software foundations needed for
later work on dielectric interfaces, photonic geometries, and electromagnetic
FDTD methods.

## Current status

The project is currently at **Phase 2.2 - Uniform material map**.

- Phase 1 implemented and validated the original two-dimensional scalar-wave
  solver.
- Phase 2.1 reorganized the solver into the reusable `wavesim` package without
  intentionally changing its numerical behavior.
- Phase 2.2 introduced validated refractive-index and wave-speed maps while
  keeping the default domain uniform.

The default Phase 2.2 simulation remains numerically identical to the verified
Phase 2.1 simulation. No material interface has been introduced yet.

## Governing model

The current solver advances the variable-speed scalar wave equation

```math
\frac{\partial^2 u}{\partial t^2}
=
c(x,y)^2
\left(
\frac{\partial^2 u}{\partial x^2}
+
\frac{\partial^2 u}{\partial y^2}
\right).
```

Here:

- \(u(x,y,t)\) is a scalar wave field;
- \(c(x,y)\) is the local propagation speed;
- \(x\) and \(y\) are spatial coordinates;
- \(t\) is time.

The material relationship is

```math
c(x,y)=\frac{c_{\mathrm{ref}}}{n(x,y)},
```

where \(c_{\mathrm{ref}}\) is the reference wave speed and \(n(x,y)\) is the
refractive-index map.

The project currently uses normalized simulation units. The default material
configuration is

```text
c_ref = 1
n(x,y) = 1
c(x,y) = 1
```

throughout the domain.

This remains an abstract scalar model. It must not yet be interpreted as a
specific electromagnetic field component or as a complete Maxwell solver.

## Numerical method

The equation is discretized on a two-dimensional Cartesian grid using
second-order centered finite differences in space and time.

For interior grid cells, the undamped update is

```math
u_{i,j}^{n+1}
=
2u_{i,j}^{n}
-
u_{i,j}^{n-1}
+
\Delta t^2 c_{i,j}^2
\nabla_h^2 u_{i,j}^{n}.
```

Only interior cells are updated. The outermost cells are reserved for the
boundary condition.

For a Gaussian initial field with zero initial velocity, the previous time
level is initialized using

```math
u^{-1}
=
u^0
+
\frac{1}{2}
\Delta t^2 c(x,y)^2
\nabla_h^2 u^0.
```

## Features

The current implementation includes:

- explicit finite-difference time stepping;
- a two-dimensional Cartesian grid;
- spatial refractive-index and wave-speed arrays;
- uniform material-map construction;
- validation of material values and array shapes;
- CFL stability validation using the fastest wave speed in the domain;
- Gaussian and zero-field initial conditions;
- an optional continuous sinusoidal point source;
- fixed reflective boundaries;
- sponge absorbing boundaries;
- animated wave-field visualization;
- refractive-index-map visualization;
- sponge-profile visualization;
- scalar-wave energy diagnostics;
- source wavelength and grid-resolution diagnostics;
- regression tests that preserve the verified Phase 2.1 results.

## Project architecture

The reusable package is named `wavesim`.

```text
photonics-simulator/
|-- wavesim/
|   |-- __init__.py
|   |-- config.py
|   |-- materials.py
|   |-- solver.py
|   `-- visualization.py
|-- simulations/
|   |-- __init__.py
|   `-- wave2d_basic.py
|-- tests/
|   |-- test_materials.py
|   `-- test_phase2_1_regression.py
|-- notes/
|   |-- mathematics/
|   |-- physics/
|   `-- simulation-logs/
|-- outputs/
|   `-- figures/
|-- README.md
`-- requirements.txt
```

### Module responsibilities

`wavesim/config.py`

- frozen configuration dataclasses;
- configuration validation;
- CFL calculation and validation;
- configuration and wavelength reporting.

`wavesim/materials.py`

- `MaterialMap`;
- uniform material-map construction;
- material-array validation.

`wavesim/solver.py`

- finite-difference operators;
- initial-condition construction;
- source application;
- boundary handling;
- damping-profile construction;
- energy calculation;
- simulation state and time stepping.

The solver does not depend on Matplotlib and can be used in tests or future
headless workflows.

`wavesim/visualization.py`

- material and damping profile figures;
- wave animation;
- energy-history plotting;
- the interactive simulation workflow.

`simulations/wave2d_basic.py`

- a thin executable entry point that creates the default configuration and
  launches the interactive workflow.

The intended dependency direction is

```text
config -> materials -> solver -> visualization -> simulation entry points
```

## Configuration

Configuration values are grouped into frozen dataclasses:

- `GridConfig`;
- `TimeConfig`;
- `MaterialConfig`;
- `InitialConditionConfig`;
- `SourceConfig`;
- `BoundaryConfig`;
- `VisualizationConfig`;
- `SimulationConfig`.

The default configuration can be created with

```python
from wavesim.config import create_default_config

config = create_default_config()
```

Because the dataclasses are frozen, variations can be constructed safely with
`dataclasses.replace`:

```python
from dataclasses import replace

from wavesim.config import create_default_config

config = create_default_config()
config = replace(
    config,
    material=replace(
        config.material,
        background_refractive_index=2.0,
    ),
)
```

This example creates a uniform medium with

```math
n=2,
\qquad
c=\frac{1}{2}.
```

### Default numerical configuration

```text
Grid
    nx = 150
    ny = 150
    dx = 1.0
    dy = 1.0

Time
    dt = 0.4
    steps = 500

Material
    reference wave speed = 1.0
    background refractive index = 1.0

Initial condition
    kind = zero
    Gaussian center = grid center
    sigma = 8.0

Source
    kind = point_sine
    position = grid center
    amplitude = 0.5
    frequency = 0.075

Boundary
    kind = sponge
    damping width = 50
    maximum damping = 0.02
    damping exponent = 2
```

## Initial conditions

Supported initial conditions are:

```python
kind = "gaussian"
```

This creates a localized Gaussian pulse with zero initial velocity.

```python
kind = "zero"
```

This starts the field from rest and is normally combined with a continuous
source.

## Sources

Supported source types are:

```python
kind = "none"
```

and

```python
kind = "point_sine"
```

The point source is

```math
s(t)=A\sin(2\pi f t)
```

and is added at one grid cell after the finite-difference wave update. That
source ordering is intentional and is protected by the numerical regression
test.

The nominal wavelength at the source is calculated from the local wave speed:

```math
\lambda=\frac{c_{\mathrm{source}}}{f}.
```

The program reports grid points per wavelength and warns when the spatial
resolution falls below ten points per wavelength.

## Boundary conditions

### Fixed boundary

```python
kind = "fixed"
```

The outermost cells satisfy

```math
u=0.
```

This homogeneous Dirichlet condition produces strong reflections.

### Sponge boundary

```python
kind = "sponge"
```

A spatial damping coefficient \(\gamma(x,y)\) increases smoothly toward the
domain edges. The damped model is approximately

```math
u_{tt}
+
\gamma(x,y)u_t
=
c(x,y)^2\nabla^2u.
```

The sponge reduces artificial reflections but is not a perfectly matched
layer.

## CFL stability

The two-dimensional CFL estimate uses the maximum wave speed anywhere in the
material map:

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

The simulation requires

```math
C\leq 1.
```

The program raises an error when the configured time step is unstable.

## Energy diagnostic

For the selected variable-speed scalar equation, the implemented diagnostic is

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

For a source-free simulation with nonzero initial energy, the program plots
normalized remaining energy:

```math
\frac{E(t)}{E(0)}.
```

For a continuously driven simulation, the source continually injects energy,
so the program plots absolute total energy \(E(t)\).

The diagnostic is primarily intended for comparisons between simulations that
use compatible numerical parameters.

## Requirements

- Python 3;
- NumPy;
- Matplotlib.

Install the dependencies with

```powershell
pip install -r requirements.txt
```

A project virtual environment is recommended. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Running the simulation

Run commands from the repository root.

Activate the virtual environment, then execute:

```powershell
python -m simulations.wave2d_basic
```

Module execution is required because `simulations` imports the reusable
top-level `wavesim` package. Direct execution such as
`python simulations\wave2d_basic.py` may not include the repository root in the
module search path.

The interactive workflow:

1. validates the configuration;
2. constructs and validates the material map;
3. checks CFL stability;
4. prints configuration and material diagnostics;
5. displays the refractive-index map;
6. displays the sponge profile when enabled;
7. animates the wave field;
8. displays the energy history after the animation closes.

## Running the tests

From the repository root:

```powershell
python -m unittest discover -s tests -v
```

The tests cover:

- default and non-unit uniform materials;
- material ownership by the simulation;
- spatial wave-speed use during time stepping;
- material-aware energy calculation;
- CFL validation using the maximum material speed;
- invalid configuration values;
- invalid material shapes and values;
- the complete verified Phase 2.1 numerical regression.

For the default 500-step simulation, the protected energy checkpoints are
approximately:

```text
Step 1:     0.03182002983188608
Step 50:   10.861960749063872
Step 100:  22.499974544196014
Step 250:  50.83918140302646
Step 500:  70.13486394160974
```

## Current limitations

The current Phase 2.2 model:

- is scalar rather than vector electromagnetic;
- constructs only uniform material maps;
- does not yet contain material interfaces or dielectric geometries;
- has not selected a TE or TM electromagnetic interpretation;
- should not yet be used to claim quantitatively accurate Fresnel behavior;
- uses normalized simulation units;
- uses a localized single-cell source;
- uses a sponge layer rather than a PML;
- does not model material dispersion or loss.

Before implementing or quantitatively interpreting a discontinuous interface,
the project must document the precise variable-coefficient PDE, its physical
meaning, and its implied interface conditions.

## Documentation

Additional derivations, explanations, and experiment records are stored in:

```text
notes/mathematics/
notes/physics/
notes/simulation-logs/
```

Simulation logs record parameter choices, numerical changes, tests, observed
behavior, limitations, and future work.

## Roadmap

### Phase 1 - Scalar-wave foundations

- [x] Two-dimensional finite-difference solver
- [x] CFL stability validation
- [x] Gaussian and zero initial conditions
- [x] Fixed and sponge boundaries
- [x] Continuous sinusoidal point source
- [x] Field animation
- [x] Energy and wavelength diagnostics

### Phase 2 - Material infrastructure

- [x] Phase 2.1: Modular refactor
- [x] Phase 2.2: Uniform material map
- [ ] Phase 2.3: Planar material interface
- [ ] Phase 2.4: Rectangular dielectric region
- [ ] Phase 2.5: Reusable geometry functions
- [ ] Phase 2.6: Phase validation

### Possible future phases

- controlled line, beam, or plane-wave sources;
- conservative interface discretizations;
- improved absorbing boundaries and PML;
- TE and TM electromagnetic FDTD solvers;
- waveguides, resonators, and scattering structures;
- automated result saving and parameter studies.

## Purpose

This project is both:

- a structured learning platform for computational photonics and numerical
  electromagnetics;
- a progressively developed technical portfolio project.

The emphasis is on understanding and validating each numerical and physical
step before introducing more advanced models.
