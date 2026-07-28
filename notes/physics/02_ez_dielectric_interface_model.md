# 2D $E_z$-Polarized Dielectric Interface Model

## 1. Purpose

This note defines the physical interpretation selected for Phase 2.3 of the
Photonics Simulator project.

Phase 2.2 introduced spatial refractive-index and wave-speed maps while keeping
the domain uniform. Phase 2.3 will place one planar discontinuity in that map.
Before introducing the discontinuity, the scalar field, governing equation,
and interface conditions must be defined explicitly.

The selected interpretation is:

```text
The simulated scalar field u(x,y,t) represents the out-of-plane electric-field component E_z(x,y,t) in a two-dimensional dielectric system.
```

This is a reduced electromagnetic model. It is more physically specific than
an abstract scalar wave, but it is not a complete vector Maxwell FDTD solver.

---

## 2. Coordinate system and assumptions

The computational domain is the $xy$ plane.

All fields are independent of $z$:

```math
\frac{\partial}{\partial z}=0.
```

The electric field has only an out-of-plane component:

```math
\mathbf{E}
=
\left(0,0,E_z(x,y,t)\right).
```

The associated magnetic field lies in the computational plane:

```math
\mathbf{H}
=
\left(H_x(x,y,t),H_y(x,y,t),0\right).
```

The material assumptions are:

1. The dielectric is linear.
2. The dielectric is isotropic.
3. The dielectric is lossless.
4. The dielectric is nondispersive.
5. The electric permittivity $\varepsilon(x,y)$ may vary spatially.
6. The magnetic permeability $\mu$ is spatially constant.
7. There are no free charges.
8. There are no free currents.
9. There are no surface charges or surface currents at the dielectric
   interface.

The model uses normalized units, so the numerical values do not currently
represent a specific SI unit system.

---

## 3. Relevant Maxwell equations

Under the stated source-free assumptions, the time-domain curl equations are:

```math
\nabla\times\mathbf{E}
=
-\mu\frac{\partial\mathbf{H}}{\partial t}
```

and:

```math
\nabla\times\mathbf{H}
=
\varepsilon(x,y)
\frac{\partial\mathbf{E}}{\partial t}.
```

For the selected field components, Faraday's law gives:

```math
\mu\frac{\partial H_x}{\partial t}
=
-\frac{\partial E_z}{\partial y}
```

and:

```math
\mu\frac{\partial H_y}{\partial t}
=
\frac{\partial E_z}{\partial x}.
```

The $z$-component of Ampere's law gives:

```math
\varepsilon(x,y)
\frac{\partial E_z}{\partial t}
=
\frac{\partial H_y}{\partial x}
-
\frac{\partial H_x}{\partial y}.
```

These three first-order equations form the two-dimensional $E_z$-polarized
Maxwell subsystem:

```text
E_z, H_x, H_y
```

The current project does not evolve all three fields directly. Instead, it
evolves the second-order equation for $E_z$.

---

## 4. Derivation of the scalar $E_z$ equation

Differentiate the $E_z$ form of Ampere's law with respect to time:

```math
\varepsilon(x,y)
\frac{\partial^2 E_z}{\partial t^2}
=
\frac{\partial}{\partial x}
\left(
\frac{\partial H_y}{\partial t}
\right)
-
\frac{\partial}{\partial y}
\left(
\frac{\partial H_x}{\partial t}
\right).
```

The permittivity is time independent, so it remains outside the time
derivative.

Substituting the two components obtained from Faraday's law gives:

```math
\varepsilon(x,y)
\frac{\partial^2 E_z}{\partial t^2}
=
\frac{\partial}{\partial x}
\left(
\frac{1}{\mu}
\frac{\partial E_z}{\partial x}
\right)
+
\frac{\partial}{\partial y}
\left(
\frac{1}{\mu}
\frac{\partial E_z}{\partial y}
\right).
```

This can be written as:

```math
\varepsilon(x,y)
\frac{\partial^2 E_z}{\partial t^2}
=
\nabla\cdot
\left(
\frac{1}{\mu}\nabla E_z
\right).
```

Because $\mu$ is assumed constant:

```math
\varepsilon(x,y)
\frac{\partial^2 E_z}{\partial t^2}
=
\frac{1}{\mu}\nabla^2E_z.
```

Therefore:

```math
\frac{\partial^2 E_z}{\partial t^2}
=
\frac{1}{\mu\varepsilon(x,y)}
\nabla^2E_z.
```

Defining the local wave speed by:

```math
c(x,y)
=
\frac{1}{\sqrt{\mu\varepsilon(x,y)}},
```

the equation becomes:

```math
\frac{\partial^2 E_z}{\partial t^2}
=
c(x,y)^2\nabla^2E_z.
```

This is the variable-speed equation already implemented by the Phase 2.2
solver:

```math
u_{tt}
=
c(x,y)^2\nabla^2u,
```

with the identification:

```math
u=E_z.
```

---

## 5. Relationship between refractive index and wave speed

For an isotropic material:

```math
n^2
=
\varepsilon_r\mu_r.
```

The project assumes a nonmagnetic dielectric:

```math
\mu_r=1.
```

Therefore:

```math
n^2=\varepsilon_r.
```

If $c_{\mathrm{ref}}$ is the propagation speed in the reference material
with $n=1$, then:

```math
c(x,y)
=
\frac{c_{\mathrm{ref}}}{n(x,y)}.
```

This is the relationship implemented in `wavesim/materials.py`.

---

## 6. Electromagnetic interface conditions

Consider a boundary between two finite, lossless dielectric materials. There
are no free surface charges or surface currents.

Maxwell's equations require continuity of the tangential electric field:

```math
\hat{\mathbf{n}}
\times
\left(
\mathbf{E}_2-\mathbf{E}_1
\right)
=
0.
```

The interface normal $\hat{\mathbf{n}}$ lies in the $xy$ plane. The
$E_z$ component is therefore tangential to any interface contained in this
two-dimensional domain.

Consequently:

```math
E_{z,1}=E_{z,2}.
```

The tangential magnetic field must also be continuous:

```math
\hat{\mathbf{n}}
\times
\left(
\mathbf{H}_2-\mathbf{H}_1
\right)
=
0.
```

For the $E_z$ subsystem, the tangential magnetic field is related to the
normal derivative of $E_z$. This gives:

```math
\frac{1}{\mu_1}
\frac{\partial E_{z,1}}{\partial n}
=
\frac{1}{\mu_2}
\frac{\partial E_{z,2}}{\partial n}.
```

Because Phase 2.3 assumes the same permeability in both materials:

```math
\mu_1=\mu_2=\mu,
```

the second condition reduces to:

```math
\frac{\partial E_{z,1}}{\partial n}
=
\frac{\partial E_{z,2}}{\partial n}.
```

The selected continuous interface conditions are therefore:

```math
E_z
\quad\text{continuous},
```

and:

```math
\frac{\partial E_z}{\partial n}
\quad\text{continuous}.
```

---

## 7. Why the coefficient remains outside the Laplacian

The current solver uses:

```math
E_{z,tt}
=
\frac{1}{\mu\varepsilon(x,y)}
\nabla^2E_z.
```

Equivalently:

```math
E_{z,tt}
=
c(x,y)^2\nabla^2E_z.
```

This form is appropriate for the selected $E_z$ polarization when
permeability is constant.

The more general expression before applying constant permeability is:

```math
\varepsilon(x,y)E_{z,tt}
=
\nabla\cdot
\left(
\frac{1}{\mu(x,y)}
\nabla E_z
\right).
```

If permeability varied spatially, the factor $1/\mu$ would have to remain
inside the divergence operator.

A different two-dimensional polarization, such as an $H_z$-polarized
formulation with spatial permittivity, also leads to a different
variable-coefficient operator. That formulation is not selected for Phase
2.3.

The project should therefore describe the current model specifically as
$E_z$-polarized rather than treating all scalar electromagnetic polarizations
as interchangeable.

---

## 8. Finite-difference interpretation

The current interior update is:

```math
E_{z,i,j}^{n+1}
=
2E_{z,i,j}^{n}
-
E_{z,i,j}^{n-1}
+
\Delta t^2
c_{i,j}^2
\nabla_h^2E_{z,i,j}^{n}.
```

The refractive index and wave speed are stored at cell-centered grid points.
The ordinary centered Laplacian is:

```math
\nabla_h^2E_{z,i,j}
\approx
\frac{
E_{z,i+1,j}-2E_{z,i,j}+E_{z,i-1,j}
}{
\Delta x^2
}
+
\frac{
E_{z,i,j+1}-2E_{z,i,j}+E_{z,i,j-1}
}{
\Delta y^2
}.
```

For a grid-aligned vertical interface at `interface_index`, the proposed
material convention is:

```python
refractive_index[:interface_index, :] = n_left
refractive_index[interface_index:, :] = n_right
```

The discrete interface then lies between:

```text
x index interface_index - 1
```

and:

```text
x index interface_index
```

This convention must be documented in the material-map constructor and tested
explicitly.

Because the coefficient associated with the spatial derivative is
$1/\mu$, which is constant in the selected model, Phase 2.3 does not require
a harmonic average of permittivity at derivative faces.

The discontinuous permittivity instead appears in the time-acceleration or
mass term through:

```math
c^2
=
\frac{1}{\mu\varepsilon}.
```

The simple grid-aligned discretization is sufficient for the qualitative goals
of Phase 2.3. Its interface error and convergence should be studied before
using it for high-accuracy reflection measurements.

---

## 9. Expected qualitative behavior

When a wave reaches a boundary from material 1 to material 2, part of the wave
is reflected and part is transmitted.

For:

```text
n_2 > n_1
```

the transmitted wave has:

- lower propagation speed;
- shorter wavelength at the same temporal frequency;
- a changed propagation direction at oblique incidence;
- a different amplitude.

The reflected wave propagates back into material 1 and interferes with the
incident field.

For normal incidence between nonmagnetic dielectrics, the expected electric
field reflection coefficient is:

```math
r
=
\frac{n_1-n_2}{n_1+n_2}.
```

For:

```text
n_1 = 1.0
n_2 = 1.5
```

this gives:

```math
r=-0.2.
```

The negative sign represents a phase reversal of the reflected electric
field.

The corresponding ideal reflected power fraction is:

```math
R=|r|^2=0.04.
```

These analytical values are useful future references, but Phase 2.3 will not
claim that the current point-source simulation has measured them accurately.

---

## 10. Source limitation

The current `point_sine` source radiates in many directions.

It is useful for observing:

- reflected wavefronts;
- transmitted wavefronts;
- wavelength changes;
- slower propagation in the higher-index material;
- qualitative refraction.

It is not ideal for measuring a single normal-incidence reflection
coefficient because:

1. The incident field is circular rather than planar.
2. Many incidence angles reach the interface simultaneously.
3. Incident and reflected fields can overlap.
4. The source continues injecting energy.
5. The sponge and finite domain influence the observed field.

Quantitative Fresnel validation should wait for a controlled excitation such
as:

- a line source;
- a finite-width beam;
- a plane-wave-like source;
- or a total-field/scattered-field formulation.

---

## 11. Energy-diagnostic interpretation

The current project calculates the mathematical energy associated with the
second-order wave equation:

```math
E_{\mathrm{wave}}
=
\int
\left[
\frac{1}{2c(x,y)^2}
\left(
\frac{\partial E_z}{\partial t}
\right)^2
+
\frac{1}{2}
\left|
\nabla E_z
\right|^2
\right]
dA.
```

Since:

```math
\frac{1}{c^2}=\mu\varepsilon,
```

this is a conserved energy-like quantity for the source-free, undamped
second-order equation under suitable boundary conditions.

It is not directly the instantaneous Maxwell electromagnetic energy:

```math
E_{\mathrm{EM}}
=
\int
\left[
\frac{1}{2}\varepsilon|\mathbf{E}|^2
+
\frac{1}{2}\mu|\mathbf{H}|^2
\right]
dA.
```

The solver does not currently store $H_x$ and $H_y$, so it cannot compute
the full Maxwell energy directly.

The existing diagnostic remains useful for:

- regression testing;
- detecting numerical growth;
- comparing compatible scalar-wave simulations;
- observing energy removal by the sponge.

It should continue to be described as a scalar-wave or wave-equation energy
diagnostic, not as a complete electromagnetic energy measurement.

---

## 12. CFL condition at the interface

The stability calculation remains:

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

The fastest material controls the global explicit time step.

For ordinary nonmagnetic materials with:

```text
n >= 1
```

the lowest-index material has the highest wave speed.

For the planned interface:

```text
n_left = 1.0
n_right = 1.5
```

the maximum speed remains:

```text
c_max = 1.0
```

and the existing default time step remains stable.

The spatial-resolution diagnostic must also consider the shorter wavelength in
the higher-index material. A grid that adequately resolves material 1 may not
adequately resolve material 2.

---

## 13. Boundary and geometry placement

The material interface should remain well inside the non-damped physical
region.

The transmitted field needs enough distance to propagate after crossing the
interface before entering the sponge.

The current default grid and sponge use:

```text
nx = 150
ny = 150
damping_width = 50
```

This leaves a relatively narrow undamped central region. A dedicated Phase 2.3
scenario should therefore use either:

- a larger grid;
- a narrower sponge;
- or both.

A reasonable initial qualitative scenario is:

```text
nx = 240
ny = 160
dx = 1.0
dy = 1.0
dt = 0.4
damping_width = 25

source position = (60, 80)
interface index = 120

n_left = 1.0
n_right = 1.5
```

This places the source, interface, and transmitted region away from the sponge
while preserving the stable default spatial and temporal step sizes.

These values are initial design parameters and should be adjusted after visual
inspection.

---

## 14. Phase 2.3 implementation contract

Phase 2.3 should implement only one grid-aligned planar interface.

The initial implementation should:

1. Preserve the default uniform-material simulation.
2. Add a planar-interface material-map constructor.
3. Use an explicit convention for which cells belong to each material.
4. Validate the interface index and both refractive indices.
5. Allow an active simulation to receive the constructed material map.
6. Add a separate planar-interface scenario file.
7. Display the interface through the existing material visualization.
8. Preserve the Phase 2.1 numerical regression.
9. Add tests for map shape, orientation, values, and wave speeds.
10. Restrict interpretation to qualitative interface behavior.

Phase 2.3 should not yet add:

- rectangular objects;
- reusable general geometry registries;
- arbitrary rotated interfaces;
- material dispersion;
- magnetic materials;
- a PML;
- a plane-wave source;
- automated Fresnel-coefficient measurements;
- a full vector Maxwell solver.

Those additions belong to later phases.

---

## 15. Required Phase 2.3 tests

At minimum, the planar-interface tests should confirm:

1. The material arrays have `grid.shape`.
2. Cells before the interface contain $n_{\mathrm{left}}$.
3. Cells from the interface onward contain $n_{\mathrm{right}}$.
4. The derived speed on each side satisfies $c=c_{\mathrm{ref}}/n$.
5. An interface at or outside the outer boundary is rejected.
6. An interface that leaves no cells for one material is rejected.
7. Non-finite or nonpositive refractive indices are rejected.
8. The default uniform material regression remains unchanged.
9. A simulation can own and use a supplied planar material map.
10. CFL validation uses the fastest speed from both materials.

---

## 16. Terminology

To avoid ambiguity, project documentation should use:

```text
E_z-polarized 2D model
```

or:

```text
out-of-plane electric-field model
```

Some references label two-dimensional polarizations using TE or TM
terminology, but the naming convention can depend on which axis or plane is
called transverse.

The explicit field-component name $E_z$ avoids this ambiguity.

The project should not describe Phase 2.3 as a full electromagnetic FDTD
solver. It advances a reduced, second-order equation for one electric-field
component rather than the staggered first-order Maxwell system.

---

## 17. Selected decision

Phase 2.3 will use the following model:

```text
Field:
    u = E_z

Geometry:
    two-dimensional xy plane

Material:
    isotropic, lossless, nondispersive dielectric

Permeability:
    spatially constant

Permittivity:
    epsilon(x,y) = epsilon_ref * n(x,y)^2

Wave speed:
    c(x,y) = c_ref / n(x,y)

Governing equation:
    E_z,tt = c(x,y)^2 * Laplacian(E_z)

Interface conditions:
    E_z continuous
    normal derivative of E_z continuous

Initial Phase 2.3 use:
    qualitative reflection, transmission, and wavelength observation
```

This decision permits the existing Phase 2.2 spatial update to be used for the
first planar interface without changing to a different variable-coefficient
operator.

---

## 18. References

The following sources support the polarization and interface model:

1. [Meep documentation - Polarizations in 2D](https://meep.readthedocs.io/en/latest/Exploiting_Symmetry/#polarizations-in-2d)
   describes the two independent two-dimensional field sets, including
   $E_z,H_x,H_y$.

2. [MIT OpenCourseWare - Waves and Imaging, Chapter 1](https://ocw.mit.edu/courses/18-325-topics-in-applied-mathematics-waves-and-imaging-fall-2015/42852dfe83c5197f19ce740818fb92a1_MIT18_325F15_Chapter1.pdf)
   presents Maxwell wave equations in spatial materials and the electromagnetic
   jump conditions at dielectric interfaces.

3. [MIT OpenCourseWare - Reflection and Refraction at Material Interfaces](https://ocw.mit.edu/courses/3-024-electronic-optical-and-magnetic-properties-of-materials-spring-2013/480e12b984eb21a5e88b8ee5cc051ef8_MIT3_024S13_2012lec22.pdf)
   summarizes tangential field continuity, phase matching, reflection,
   refraction, and Snell's law at dielectric boundaries.

---

## 19. Summary

The scalar field used by the project now has a precise Phase 2.3
interpretation:

```math
u(x,y,t)=E_z(x,y,t).
```

For a two-dimensional, nonmagnetic dielectric with constant permeability, the
reduced Maxwell equations give:

```math
E_{z,tt}
=
\frac{1}{\mu\varepsilon(x,y)}
\nabla^2E_z
=
\frac{c_{\mathrm{ref}}^2}{n(x,y)^2}
\nabla^2E_z.
```

At a dielectric interface, $E_z$ and its normal derivative are continuous
under the selected assumptions.

This model justifies using the existing Phase 2.2 variable-speed scalar update
for the first planar dielectric interface. It also establishes clear limits:
the current source and energy diagnostic are suitable for qualitative
interface study and regression testing, but not yet for a complete
quantitative Maxwell or Fresnel analysis.
