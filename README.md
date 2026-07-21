# Photonics Simulator

A Python-based numerical simulation project for studying and visualizing two-dimensional wave propagation.

The project is being developed progressively, beginning with the 2D scalar wave equation and moving toward more advanced photonics and electromagnetic simulation tools.

## Current Status

The project is currently in **Phase 1**.

Phase 1 implements a numerical solver for the homogeneous 2D scalar wave equation:

```math
\frac{\partial^2 u}{\partial t^2}
=
c^2
\left(
\frac{\partial^2 u}{\partial x^2}
+
\frac{\partial^2 u}{\partial y^2}
\right).
```

The equation is discretized using second-order centered finite differences in space and time.

This phase is intended to establish the numerical foundations required for later electromagnetic and photonics simulations. It is not yet a full Maxwell-equation or FDTD electromagnetic solver.

## Phase 1 Features

The current simulation includes:

* Explicit finite-difference time stepping
* Two-dimensional Cartesian grid
* CFL stability validation
* Gaussian initial pulse
* Zero-field initial condition
* Continuous sinusoidal point source
* Fixed reflective boundaries
* Sponge absorbing boundaries
* Configurable damping-layer width, strength, and profile exponent
* Animated field visualization
* Approximate scalar-wave energy calculation
* Normalized energy plots for free-propagation simulations
* Absolute energy plots for continuously driven simulations
* Source wavelength and grid-resolution diagnostics
* Configuration validation and numerical warnings

## Available Configurations

### Initial conditions

```python
initial_condition_type = "gaussian"
```

Creates a localized Gaussian pulse at the initial time.

```python
initial_condition_type = "zero"
```

Starts the field from rest. This is normally used with a continuous source.

### Sources

```python
source_type = "none"
```

Runs the simulation without a continuous source.

```python
source_type = "point_sine"
```

Adds a sinusoidal point source at a selected grid position.

The source frequency is expressed in cycles per simulation-time unit:

```python
source_frequency = 0.075
```

The corresponding nominal wavelength is calculated using:

```math
\lambda = \frac{c}{f}.
```

The program also reports the number of grid points per wavelength to help identify insufficient spatial resolution and possible numerical dispersion.

### Boundary conditions

```python
boundary_type = "fixed"
```

Applies homogeneous Dirichlet conditions at the outer boundary:

```math
u = 0.
```

This produces strong wave reflections.

```python
boundary_type = "sponge"
```

Adds a smoothly increasing damping layer near the boundaries.

The sponge region approximately follows the damped wave equation:

```math
u_{tt}+\gamma(x,y)u_t=c^2\nabla^2u,
```

where the damping coefficient (\gamma(x,y)) is zero in the central region and increases toward the domain edges.

The sponge reduces artificial reflections but is not a perfectly matched layer.

## Example Simulations

### Gaussian pulse with sponge boundaries

```python
initial_condition_type = "gaussian"
source_type = "none"
boundary_type = "sponge"
```

This configuration is useful for studying:

* free wave propagation,
* boundary absorption,
* residual reflections,
* and energy decay.

### Continuous source with sponge boundaries

```python
initial_condition_type = "zero"
source_type = "point_sine"
boundary_type = "sponge"
```

This configuration produces circular waves that propagate outward and are attenuated near the computational boundaries.

### Continuous source with fixed boundaries

```python
initial_condition_type = "zero"
source_type = "point_sine"
boundary_type = "fixed"
```

This configuration demonstrates:

* strong boundary reflections,
* interference,
* and wave confinement inside the domain.

## Energy Diagnostics

For a Gaussian pulse without a continuous source, the simulation plots normalized energy:

```math
\frac{E(t)}{E(0)}.
```

This indicates how much of the original wave energy remains inside the domain.

For a continuously driven simulation, the source continuously injects energy. In this case, normalization by the initial energy is not meaningful because the initial field may have zero energy.

The simulation therefore plots the absolute total energy:

```math
E(t).
```

The approximate scalar-wave energy is calculated from:

```math
E
\approx
\sum_{i,j}
\left[
\frac{1}{2}u_t^2
+
\frac{1}{2}c^2
\left(
u_x^2+u_y^2
\right)
\right]
\Delta x\Delta y.
```

This diagnostic is primarily intended for comparing simulations that use the same numerical parameters.

## Project Structure

```text
photonics-simulator/
├── simulations/
│   └── wave2d_basic.py
├── notes/
│   ├── mathematics/
│   ├── physics/
│   ├── simulation_logs/
│   │   └── phase_1/
│   └── next_steps/
├── outputs/
│   └── figures/
│       └── phase_1/
├── README.md
└── requirements.txt
```

The exact structure may continue evolving as the project becomes more modular.

## Requirements

The current simulation requires:

* Python 3
* NumPy
* Matplotlib

Install the dependencies with:

```bash
pip install numpy matplotlib
```

A project virtual environment is recommended.

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install numpy matplotlib
```

## Running the Simulation

From the project root, run:

```bash
python simulations/wave2d_basic.py
```

The program will:

1. Validate the selected configuration.
2. Check the CFL stability condition.
3. Print the simulation and source parameters.
4. Display the sponge damping profile when enabled.
5. Animate the wave field.
6. Display the corresponding energy history after the animation closes.

## Numerical Stability

For the 2D scalar wave equation, the implemented CFL estimate is:

```math
S
=

c\Delta t
\sqrt{
\frac{1}{\Delta x^2}
+
\frac{1}{\Delta y^2}
}.
```

The simulation requires:

```math
S \leq 1.
```

The program stops with an error when the selected parameters violate this condition.

## Current Limitations

The current Phase 1 model:

* is scalar rather than vector electromagnetic,
* assumes a homogeneous medium,
* uses a constant wave speed,
* uses normalized simulation units,
* includes a simple point source,
* uses a sponge layer rather than a PML,
* and does not yet include material interfaces or photonic structures.

These limitations are intentional for the current development phase.

## Documentation

Additional derivations, explanations, and experiment records are stored in:

```text
notes/mathematics/
notes/physics/
notes/simulation_logs/
```

The simulation logs document:

* parameter choices,
* numerical changes,
* test results,
* observed behavior,
* figures,
* limitations,
* and future improvements.

## Roadmap

### Phase 1 — Scalar wave solver

* [x] 2D finite-difference solver
* [x] CFL stability validation
* [x] Gaussian initial condition
* [x] Zero initial condition
* [x] Fixed boundaries
* [x] Sponge absorbing boundaries
* [x] Continuous sinusoidal point source
* [x] Field animation
* [x] Energy diagnostics
* [x] Wavelength-resolution diagnostics
* [x] Final code cleanup
* [x] Final Phase 1 summary

### Future phases

Planned future developments may include:

* Modular source and boundary registries
* Material and refractive-index maps
* Dielectric interfaces
* Simple photonic geometries
* Plane-wave and finite-width sources
* Improved absorbing boundaries
* Perfectly matched layers
* Maxwell-equation FDTD solvers
* TE and TM polarization modes
* Waveguides, resonators, and scattering structures
* Automated result saving and parameter studies

## Purpose

This project is intended as both:

* a learning platform for computational photonics and numerical electromagnetics,
* and a progressively developed simulation toolkit suitable for a technical portfolio.

The emphasis is on understanding the numerical and physical foundations before introducing more advanced electromagnetic models.
