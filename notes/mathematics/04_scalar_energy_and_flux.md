# 04 — Scalar Energy and Flux

> **Status:** Current mathematical and numerical reference for the completed
> Phase 5 scalar energy-flux diagnostics.
>
> **Scope:** Rigorous derivation of the continuous scalar-wave energy law and
> its numerically consistent realization for the centered finite-difference
> solver.

## 1. Purpose

Phase 5 introduces diagnostics for stored scalar-wave energy and transported
scalar-wave power. The formulas must come from the same equation and the same
finite-difference operators as the solver. Otherwise, an apparent failure of
energy conservation could be caused by the diagnostic rather than the wave
update.

This note develops the result in the following order:

1. state the continuous scalar equation and assumptions;
2. derive its local and integral energy laws;
3. write the actual finite-difference equation;
4. establish the discrete counterpart of integration by parts;
5. derive the leapfrog energy invariant step by step;
6. derive the face flux that satisfies a local discrete balance;
7. add fixed boundaries, material interfaces, damping, and sources;
8. state the resulting Phase 5.1 implementation contract.

The diagnostic is a mathematical energy of the scalar second-order equation.
It is not the complete electromagnetic energy or Poynting vector because the
solver does not independently evolve the associated magnetic fields.

---

## 2. Continuous problem and assumptions

Let $u=u(x,y,t)$ be a sufficiently smooth real scalar field on a fixed
two-dimensional region $\Omega$. The solver models:

```math
u_{tt}=c(x,y)^2\nabla^2u,
```

where $c(x,y)$ is finite, positive, and independent of time. Define:

```math
m(x,y)=\frac{1}{c(x,y)^2}.
```

The equation can then be written as:

```math
\boxed{m u_{tt}-\nabla^2u=0.}
```

Writing the coefficient as $m$ makes the structure clearer: the spatially
varying material coefficient multiplies the temporal acceleration, while the
coefficient of the Laplacian is constant.

For the project's reduced $E_z$ interpretation:

```math
m=\mu\varepsilon,
```

with constant permeability $\mu$ and spatially varying permittivity
$\varepsilon$. The derivation below depends on $m_t=0$. It does not require
$m$ to be spatially uniform.

Initially assume:

- no source;
- no damping;
- either a subregion with a measurable boundary flux or a complete domain
  with homogeneous fixed boundary data;
- sufficient regularity to apply the product rule and divergence theorem.

Damping and discrete sources are added after the conservative law is clear.

---

## 3. What a local conservation law says

A local conservation law has the form:

```math
\boxed{\partial_t e+\nabla\cdot\mathbf F=0.}
```

Here:

- $e(x,y,t)$ is energy stored per unit area;
- $\mathbf F(x,y,t)$ is energy flow per unit boundary length per unit time;
- $\partial_t e$ is the local rate of change of stored energy;
- $\nabla\cdot\mathbf F$ is the net outward flow from an infinitesimal
  neighborhood.

The sign follows directly from the equation. If more energy leaves a small
region than enters it, then $\nabla\cdot\mathbf F>0$, which requires
$\partial_t e<0$.

The task is not to guess $e$ and $\mathbf F$. They will be identified by
rewriting the wave equation as a time derivative plus a divergence.

---

## 4. Continuous derivation

### 4.1 Multiply by the field velocity

Start from:

```math
m u_{tt}-\nabla^2u=0.
```

Multiply every term by $u_t$:

```math
m u_tu_{tt}-u_t\nabla^2u=0.
```

Multiplication by velocity is the natural energy operation. For an ordinary
degree of freedom, acceleration times velocity is the rate of change of a
quadratic kinetic energy. The same mechanism works here.

### 4.2 Rewrite the temporal term

Because $m_t=0$:

```math
\partial_t\left(\frac12m u_t^2\right)
=
\frac12m\,\partial_t(u_t^2)
=
m u_tu_{tt}.
```

Therefore:

```math
m u_tu_{tt}
=
\partial_t\left(\frac{u_t^2}{2c^2}\right).
```

This identifies the kinetic-like energy density:

```math
\boxed{e_{\mathrm{kin}}=\frac{u_t^2}{2c^2}.}
```

### 4.3 Rewrite the spatial term

For a scalar $a$ and vector $\mathbf b$, the divergence product rule is:

```math
\nabla\cdot(a\mathbf b)
=
\nabla a\cdot\mathbf b+a\nabla\cdot\mathbf b.
```

Choose $a=u_t$ and $\mathbf b=\nabla u$:

```math
\nabla\cdot(u_t\nabla u)
=
\nabla u_t\cdot\nabla u+u_t\nabla^2u.
```

Solve this identity for the term in the wave equation:

```math
-u_t\nabla^2u
=
-\nabla\cdot(u_t\nabla u)
+\nabla u_t\cdot\nabla u.
```

For a sufficiently smooth field, time and spatial differentiation commute:

```math
\nabla u_t=\partial_t(\nabla u).
```

It follows that:

```math
\nabla u_t\cdot\nabla u
=
\frac12\partial_t(\nabla u\cdot\nabla u)
=
\partial_t\left(\frac12|\nabla u|^2\right).
```

Thus:

```math
-u_t\nabla^2u
=
\partial_t\left(\frac12|\nabla u|^2\right)
-\nabla\cdot(u_t\nabla u).
```

The first term is stored potential-like energy. The divergence term is energy
transport.

### 4.4 Collect the terms

Substitute both identities into the velocity-multiplied equation:

```math
\partial_t\left(\frac{u_t^2}{2c^2}\right)
+
\partial_t\left(\frac12|\nabla u|^2\right)
-
\nabla\cdot(u_t\nabla u)
=0.
```

Combine the time derivatives:

```math
\partial_t
\left[
\frac{u_t^2}{2c^2}
+
\frac12|\nabla u|^2
\right]
+
\nabla\cdot(-u_t\nabla u)
=0.
```

Comparison with $\partial_t e+\nabla\cdot\mathbf F=0$ gives:

```math
\boxed{
e=
\frac{u_t^2}{2c^2}
+
\frac12|\nabla u|^2
}
```

and:

```math
\boxed{\mathbf F=-u_t\nabla u.}
```

In Cartesian components:

```math
\boxed{F_x=-u_tu_x,\qquad F_y=-u_tu_y.}
```

The entire continuous derivation can be summarized as:

```text
wave equation × velocity
    = time change of kinetic energy
    + time change of gradient energy
    + divergence of energy flux.
```

---

## 5. Checks on the continuous result

### 5.1 Direction of travel

For a right-traveling one-dimensional wave $u=f(x-ct)$:

```math
u_t=-cf',\qquad u_x=f'.
```

Therefore:

```math
F_x=-u_tu_x=c(f')^2>0.
```

For a left-traveling wave $u=f(x+ct)$:

```math
F_x=-c(f')^2<0.
```

The flux sign therefore agrees with propagation direction.

### 5.2 Harmonic plane wave

For $u=A\cos(kx-\omega t)$:

```math
F_x=A^2\omega k\sin^2(kx-\omega t).
```

Its period average is:

```math
\langle F_x\rangle=\frac12A^2\omega k>0.
```

This also shows why flux must be formed before time averaging. The separate
averages of $u_t$ and $u_x$ vanish, but the average of their product does not.

### 5.3 Material coefficient placement

The material coefficient $1/c^2$ appears in stored kinetic energy, not in the
flux. This is a consequence of the specific equation:

```math
\frac{1}{c^2}u_{tt}-\nabla^2u=0.
```

A different equation, for example
$u_{tt}-\nabla\cdot(c^2\nabla u)=0$, would produce a different energy and flux.
The diagnostic must always be derived from the actual PDE.

---

## 6. Integral energy balance

Define the energy stored in a fixed region $\Omega$:

```math
E_\Omega(t)=\int_\Omega e\,dA.
```

Integrate the local law:

```math
\int_\Omega\partial_t e\,dA
+
\int_\Omega\nabla\cdot\mathbf F\,dA
=0.
```

Because the region is fixed in time:

```math
\int_\Omega\partial_t e\,dA
=
\frac{dE_\Omega}{dt}.
```

The divergence theorem gives:

```math
\int_\Omega\nabla\cdot\mathbf F\,dA
=
\oint_{\partial\Omega}
\mathbf F\cdot\hat{\mathbf n}\,ds.
```

Hence:

```math
\boxed{
\frac{dE_\Omega}{dt}
=
-\oint_{\partial\Omega}
\mathbf F\cdot\hat{\mathbf n}\,ds.
}
```

The normal $\hat{\mathbf n}$ points outward:

- $\mathbf F\cdot\hat{\mathbf n}>0$ is energy leaving $\Omega$;
- $\mathbf F\cdot\hat{\mathbf n}<0$ is energy entering $\Omega$.

This is the continuous statement that a loss of stored energy equals net
outward transported energy.

For homogeneous Dirichlet data $u=0$ on the outer boundary for every time,
$u_t=0$ there. Consequently:

```math
\mathbf F\cdot\hat{\mathbf n}
=
-u_t\frac{\partial u}{\partial n}
=0.
```

The total source-free, undamped energy is then constant.

---

## 7. The finite-difference setting

### 7.1 Grid and time levels

Let:

```math
x_i=i\Delta x,\qquad y_j=j\Delta y,\qquad t^n=n\Delta t,
```

and let $u_{i,j}^n$ approximate $u(x_i,y_j,t^n)$. Fixed outer nodes are zero,
and the wave equation is updated on the interior nodes.

The centered Laplacian is:

```math
\begin{aligned}
\Delta_hu_{i,j}^n
={}&
\frac{u_{i+1,j}^n-2u_{i,j}^n+u_{i-1,j}^n}{\Delta x^2}
\\
&+
\frac{u_{i,j+1}^n-2u_{i,j}^n+u_{i,j-1}^n}{\Delta y^2}.
\end{aligned}
```

The undamped, source-free solver equation is:

```math
\boxed{
m_{i,j}
\frac{u_{i,j}^{n+1}-2u_{i,j}^n+u_{i,j}^{n-1}}{\Delta t^2}
-
\Delta_hu_{i,j}^n
=0.
}
```

### 7.2 Natural time differences

Define the half-step velocities:

```math
v_{i,j}^{n+1/2}
=
\frac{u_{i,j}^{n+1}-u_{i,j}^n}{\Delta t},
```

```math
v_{i,j}^{n-1/2}
=
\frac{u_{i,j}^n-u_{i,j}^{n-1}}{\Delta t}.
```

Then:

```math
\frac{u^{n+1}-2u^n+u^{n-1}}{\Delta t^2}
=
\frac{v^{n+1/2}-v^{n-1/2}}{\Delta t}.
```

The velocity centered at integer time $t^n$ is:

```math
\boxed{
\bar v_{i,j}^n
=
\frac{v_{i,j}^{n+1/2}+v_{i,j}^{n-1/2}}{2}
=
\frac{u_{i,j}^{n+1}-u_{i,j}^{n-1}}{2\Delta t}.
}
```

### 7.3 Natural spatial differences

Define one-cell differences on the faces between nodes:

```math
D_xu_{i+1/2,j}^n
=
\frac{u_{i+1,j}^n-u_{i,j}^n}{\Delta x},
```

```math
D_yu_{i,j+1/2}^n
=
\frac{u_{i,j+1}^n-u_{i,j}^n}{\Delta y}.
```

Their divergence reproduces the solver's Laplacian:

```math
\Delta_hu_{i,j}^n
=
\frac{D_xu_{i+1/2,j}^n-D_xu_{i-1/2,j}^n}{\Delta x}
+
\frac{D_yu_{i,j+1/2}^n-D_yu_{i,j-1/2}^n}{\Delta y}.
```

If `u.shape == (nx, ny)`, then:

```text
D_x u has shape (nx - 1, ny)
D_y u has shape (nx, ny - 1)
```

These face differences, rather than two-cell node-centered gradients, are the
spatial quantities algebraically paired with the five-point Laplacian.

---

## 8. Discrete inner products and summation by parts

Introduce a node inner product:

```math
\langle a,b\rangle_N
=
\sum_{i,j}a_{i,j}b_{i,j}\,\Delta x\Delta y,
```

and corresponding face inner products:

```math
\langle p,q\rangle_X
=
\sum_{x\text{-faces}}p_{i+1/2,j}q_{i+1/2,j}
\,\Delta x\Delta y,
```

```math
\langle r,s\rangle_Y
=
\sum_{y\text{-faces}}r_{i,j+1/2}s_{i,j+1/2}
\,\Delta x\Delta y.
```

For grid functions that vanish on the fixed outer boundary, the discrete
summation-by-parts identity is:

```math
\boxed{
-\langle\Delta_hu,w\rangle_N
=
\langle D_xu,D_xw\rangle_X
+
\langle D_yu,D_yw\rangle_Y.
}
```

This is the exact grid counterpart of:

```math
-\int_\Omega w\nabla^2u\,dA
=
\int_\Omega\nabla w\cdot\nabla u\,dA
```

when the boundary term vanishes.

To see the cancellation explicitly, consider a one-dimensional grid with
nodes $i=0,1,\ldots,N$. The fixed boundary values are:

```math
w_0=w_N=0,
```

and the updated interior nodes are $i=1,\ldots,N-1$. Write:

```math
q_{i+1/2}=\frac{u_{i+1}-u_i}{\Delta x}.
```

Start with the weighted sum of the discrete divergence over the interior:

```math
S=
\sum_{i=1}^{N-1}
w_i\frac{q_{i+1/2}-q_{i-1/2}}{\Delta x}\,\Delta x.
```

Cancel $\Delta x$ and split the two terms:

```math
S=
\sum_{i=1}^{N-1}w_iq_{i+1/2}
-
\sum_{i=1}^{N-1}w_iq_{i-1/2}.
```

For a concrete grid with nodes $0,1,2,3,4$, this is:

```math
\begin{aligned}
S={}&w_1(q_{3/2}-q_{1/2})
+w_2(q_{5/2}-q_{3/2})
+w_3(q_{7/2}-q_{5/2})
\\
={}&-w_1q_{1/2}
+(w_1-w_2)q_{3/2}
+(w_2-w_3)q_{5/2}
+w_3q_{7/2}.
\end{aligned}
```

The boundary values allow the first and last terms to be written in the same
form as the interior terms:

```math
-w_1q_{1/2}=-q_{1/2}(w_1-w_0),
```

```math
w_3q_{7/2}=-q_{7/2}(w_4-w_3).
```

Consequently, for the general grid:

```math
\boxed{
S=
-\sum_{i=0}^{N-1}
q_{i+1/2}(w_{i+1}-w_i).
}
```

The cancellation is now visible. An interior face such as $i+1/2$ contributes
$+w_iq_{i+1/2}$ from its left node and $-w_{i+1}q_{i+1/2}$ from its right
node. Their sum is:

```math
-q_{i+1/2}(w_{i+1}-w_i).
```

Finally define the face difference:

```math
D_xw_{i+1/2}=\frac{w_{i+1}-w_i}{\Delta x}.
```

Restoring $q=D_xu$ and the face quadrature factor $\Delta x$ gives:

```math
\boxed{
\sum_{i=1}^{N-1}
w_i\Delta_hu_i\,\Delta x
=
-\sum_{i=0}^{N-1}
D_xu_{i+1/2}D_xw_{i+1/2}\,\Delta x.
}
```

This is discrete integration by parts in one dimension. The two-dimensional
identity is obtained by applying this argument to every grid row in $x$ and
every grid column in $y$, then adding the results.

This identity is the mathematical reason that the energy must use face
differences. It is also the mechanism by which internal face fluxes cancel.

---

## 9. Global discrete energy derivation

### 9.1 Rewrite the update with velocities

The solver equation becomes:

```math
m_{i,j}
\frac{v_{i,j}^{n+1/2}-v_{i,j}^{n-1/2}}{\Delta t}
-
\Delta_hu_{i,j}^n
=0.
```

Take its node inner product with $\bar v^n$:

```math
\left\langle
m\frac{v^{n+1/2}-v^{n-1/2}}{\Delta t},
\bar v^n
\right\rangle_N
-
\langle\Delta_hu^n,\bar v^n\rangle_N
=0.
```

The two terms are treated separately.

### 9.2 Temporal term becomes kinetic-energy change

Use:

```math
(a-b)\frac{a+b}{2}=\frac{a^2-b^2}{2}.
```

Since $\bar v^n=(v^{n+1/2}+v^{n-1/2})/2$:

```math
\begin{aligned}
&\left\langle
m\frac{v^{n+1/2}-v^{n-1/2}}{\Delta t},
\bar v^n
\right\rangle_N
\\
&\qquad=
\frac{1}{\Delta t}
\left[
\frac12\langle mv^{n+1/2},v^{n+1/2}\rangle_N
-
\frac12\langle mv^{n-1/2},v^{n-1/2}\rangle_N
\right].
\end{aligned}
```

Define:

```math
\boxed{
K_h^{n+1/2}
=
\frac12\langle mv^{n+1/2},v^{n+1/2}\rangle_N.
}
```

The temporal term is exactly:

```math
\frac{K_h^{n+1/2}-K_h^{n-1/2}}{\Delta t}.
```

### 9.3 Spatial term becomes potential-energy change

Apply summation by parts:

```math
-\langle\Delta_hu^n,\bar v^n\rangle_N
=
\langle D_xu^n,D_x\bar v^n\rangle_X
+
\langle D_yu^n,D_y\bar v^n\rangle_Y.
```

Because spatial differences are linear and commute with time differences:

```math
D_x\bar v^n
=
\frac{D_xu^{n+1}-D_xu^{n-1}}{2\Delta t},
```

with the same identity in $y$. Therefore:

```math
\begin{aligned}
\langle D_xu^n,D_x\bar v^n\rangle_X
={}&
\frac{1}{2\Delta t}
\left[
\langle D_xu^{n+1},D_xu^n\rangle_X
\right.
\\
&\left.
-\langle D_xu^n,D_xu^{n-1}\rangle_X
\right].
\end{aligned}
```

The same calculation applies to $y$. Define the half-step discrete potential
energy:

```math
\boxed{
\begin{aligned}
P_h^{n+1/2}
={}&
\frac12\langle D_xu^{n+1},D_xu^n\rangle_X
\\
&+
\frac12\langle D_yu^{n+1},D_yu^n\rangle_Y.
\end{aligned}
}
```

Then the spatial term is exactly:

```math
\frac{P_h^{n+1/2}-P_h^{n-1/2}}{\Delta t}.
```

The cross-time products are not guessed approximations. They are the terms
that arise when the centered update is multiplied by the centered velocity.

### 9.4 Combine both changes

Substitution into the inner-product equation gives:

```math
\frac{K_h^{n+1/2}-K_h^{n-1/2}}{\Delta t}
+
\frac{P_h^{n+1/2}-P_h^{n-1/2}}{\Delta t}
=0.
```

Define:

```math
\boxed{E_h^{n+1/2}=K_h^{n+1/2}+P_h^{n+1/2}.}
```

It follows immediately that:

```math
\boxed{E_h^{n+1/2}=E_h^{n-1/2}.}
```

This equality is exact in arithmetic for the source-free, undamped discrete
equation with fixed boundaries. A numerical implementation should differ
only through floating-point roundoff.

---

## 10. Meaning of the cross-time potential energy

The continuous potential energy contains $|\nabla u|^2/2$, whereas the exact
leapfrog invariant contains $D u^{n+1}D u^n/2$. Their connection follows from:

```math
ab=\left(\frac{a+b}{2}\right)^2
-\left(\frac{a-b}{2}\right)^2.
```

For one face difference:

```math
\frac12D u^{n+1}D u^n
=
\frac12
\left[D\left(\frac{u^{n+1}+u^n}{2}\right)\right]^2
-
\frac{\Delta t^2}{8}(D v^{n+1/2})^2.
```

Thus the invariant is a centered approximation to the continuous energy at
$t^{n+1/2}$ plus a time-step-dependent correction imposed by leapfrog. The
correction vanishes quadratically as $\Delta t\to0$.

A simpler sum of positive squares may be useful as an approximation to the
continuous energy, but it is not exactly conserved by this update. Phase 5.1
should keep those two concepts distinct:

- **continuous-energy estimate:** intuitive and pointwise nonnegative;
- **leapfrog invariant:** exactly paired with the numerical update.

The leapfrog invariant is the authoritative conservation diagnostic.

---

## 11. Local discrete balance and face flux

Global conservation alone does not determine where energy moves. Flux
monitors require a local balance for the control volume surrounding each
node.

### 11.1 Allocate energy to a nodal control volume

At half time $n+1/2$, assign the node its kinetic density and half of the
potential density on each of its four adjacent faces:

```math
\begin{aligned}
e_{i,j}^{n+1/2}
={}&
\frac{m_{i,j}}{2}(v_{i,j}^{n+1/2})^2
\\
&+\frac14
\left[
D_xu_{i+1/2,j}^{n+1}D_xu_{i+1/2,j}^{n}
+D_xu_{i-1/2,j}^{n+1}D_xu_{i-1/2,j}^{n}
\right]
\\
&+\frac14
\left[
D_yu_{i,j+1/2}^{n+1}D_yu_{i,j+1/2}^{n}
+D_yu_{i,j-1/2}^{n+1}D_yu_{i,j-1/2}^{n}
\right].
\end{aligned}
```

The factor $1/4$ contains:

- the $1/2$ in the potential-energy definition;
- another $1/2$ because the face is shared by two neighboring control
  volumes.

Summing these densities over all control volumes reproduces the global
discrete energy, with the usual boundary-control-volume convention.

### 11.2 Derive the flux on one x-face

Let:

```math
q_{i+1/2,j}^n=D_xu_{i+1/2,j}^n.
```

The change of the right-face share of node $(i,j)$ is:

```math
\begin{aligned}
&\frac{1}{\Delta t}
\frac14
\left(
q_{i+1/2,j}^{n+1}q_{i+1/2,j}^{n}
-q_{i+1/2,j}^{n}q_{i+1/2,j}^{n-1}
\right)
\\
&\qquad=
\frac{q_{i+1/2,j}^n}{2}
\frac{\bar v_{i+1,j}^n-\bar v_{i,j}^n}{\Delta x}.
\end{aligned}
```

The corresponding expression from the neighboring control volume contains
the complementary half. Combining these edge terms with the two nodal wave
equations leaves the transport term:

```math
-q_{i+1/2,j}^n
\frac{\bar v_{i,j}^n+\bar v_{i+1,j}^n}{2}.
```

This identifies the natural symmetric face flux associated with this energy
allocation:

```math
\boxed{
F_{x,i+1/2,j}^n
=
-D_xu_{i+1/2,j}^n
\frac{\bar v_{i,j}^n+\bar v_{i+1,j}^n}{2}.
}
```

Repeating the argument in $y$ gives:

```math
\boxed{
F_{y,i,j+1/2}^n
=
-D_yu_{i,j+1/2}^n
\frac{\bar v_{i,j}^n+\bar v_{i,j+1}^n}{2}.
}
```

These formulas have a simple interpretation: evaluate the gradient on its
natural face, average the centered nodal velocity to that same face, and form
the discrete version of $-u_t\nabla u$.

### 11.3 Local conservation equation

The nodal control-volume energy and face fluxes obey:

```math
\boxed{
\frac{e_{i,j}^{n+1/2}-e_{i,j}^{n-1/2}}{\Delta t}
+
\frac{F_{x,i+1/2,j}^n-F_{x,i-1/2,j}^n}{\Delta x}
+
\frac{F_{y,i,j+1/2}^n-F_{y,i,j-1/2}^n}{\Delta y}
=0.
}
```

When the equation is summed over several neighboring control volumes, every
shared face appears once as an outward flux and once as an inward flux. Those
internal terms cancel exactly. Only fluxes on the boundary of the selected
set remain. This is the discrete counterpart of the divergence theorem.

---

## 12. Array placement and flux integration

For `u.shape == (nx, ny)`, the natural flux arrays are:

```text
F_x.shape == (nx - 1, ny)
F_y.shape == (nx, ny - 1)
```

Each face is represented exactly once. Expanding both fluxes to the nodal
field shape would create unused entries or duplicate physical faces.

A vertical monitor lies on one $x$-face. Its instantaneous scalar power is:

```math
\boxed{
P_x^n
=
\sum_{j=j_0}^{j_1}
F_{x,i+1/2,j}^n\,\Delta y.
}
```

A horizontal monitor lies on one $y$-face:

```math
\boxed{
P_y^n
=
\sum_{i=i_0}^{i_1}
F_{y,i,j+1/2}^n\,\Delta x.
}
```

Coordinate-oriented signs are:

- positive $P_x$: transport toward $+x$;
- negative $P_x$: transport toward $-x$;
- positive $P_y$: transport toward $+y$;
- negative $P_y$: transport toward $-y$.

For a control-volume balance, coordinate flux must instead be dotted with the
outward normal. For example, outward flux on the left side is $-F_x$.

For a harmonic result, form instantaneous power first and average afterward:

```math
\boxed{
\langle P\rangle
=
\frac{1}{N}\sum_{n=n_0}^{n_1}P^n.
}
```

Do not average velocity and gradient separately before multiplying them.

### 12.1 From stored profiles to signed power

Each configured flux monitor stores the selected face profile rather than only
its integral. For an x-directed monitor, its instantaneous signed power is
derived using:

```math
P_x^n
=
\Delta y
\sum_{j=j_0}^{j_1-1}
F_{x,i+1/2,j}^n.
```

For a y-directed monitor:

```math
P_y^n
=
\Delta x
\sum_{i=i_0}^{i_1-1}
F_{y,i,j+1/2}^n.
```

Keeping the profiles preserves the transverse distribution. Integrated power,
mean flux density, sub-aperture power, and later modal projections can all be
derived without rerunning the simulation. Full-domain flux arrays remain
temporary and are not stored.

### 12.2 Time-windowed average power

For the half-open integer-time window $n_0:n_1$, let:

```math
N=n_1-n_0.
```

The arithmetic time average is:

```math
\boxed{
\overline P
=
\frac{1}{N}
\sum_{n=n_0}^{n_1-1}P^n.
}
```

Because the samples are uniformly separated by $\Delta t$, the represented
window duration is:

```math
T=N\Delta t.
```

The corresponding rectangular-rule estimate of signed transported energy is:

```math
\boxed{
W
=
\Delta t
\sum_{n=n_0}^{n_1-1}P^n
=
\overline P\,T.
}
```

Both quantities remain signed. A negative result indicates net transport in
the negative coordinate direction; taking an absolute value would destroy
that information and would invalidate control-volume balances.

For a harmonic source of frequency $f$, the window contains:

```math
N_{\mathrm{cycles}}=Tf
```

cycles. Requiring a minimum cycle count protects against averages dominated by
short transients. Choosing an integer number of steady-state cycles further
reduces residual oscillatory error, but it is an experimental recommendation
rather than a mathematical requirement of the averaging function.

### 12.3 Implemented indexed monitor contract

The implementation keeps field and flux monitors as separate concepts.
`FluxMonitorConfig` uses an axis, one face index, and a half-open transverse
index interval. An x-directed monitor samples:

```text
flux_x[face_index, transverse_start:transverse_stop]
```

and a y-directed monitor samples:

```text
flux_y[transverse_start:transverse_stop, face_index]
```

Each history entry stores an immutable copy of this face-flux profile. This
preserves the transverse distribution; signed aperture power and later
spatial reductions are derived from the stored profile. Full-domain flux
arrays are not retained after sampling.

The three-level flux calculated during an advance belongs to the old/current
integer step $n$. It is recorded after the source has modified $u^{n+1}$ and
before the simulation promotes that field. A monitor whose face aperture
directly touches an active source cell is rejected so transported flux is not
silently mixed with local discrete source injection.

---

## 13. Material interfaces

The face flux contains no explicit average of $c$:

```math
\mathbf F=-u_t\nabla u.
```

That is consistent with the selected constant-permeability $E_z$ equation.
At an ideal material interface, $u$ and its normal derivative are continuous.
Since the interface is fixed in time, $u_t$ is also continuous, so the normal
energy flux is continuous in the absence of a source or loss at the interface.

Material variation still affects stored energy through:

```math
\frac{1}{2c^2}u_t^2.
```

No harmonic or arithmetic speed average should be introduced into the Phase
5 flux unless the governing spatial operator itself is changed.

---

## 14. Centered sponge damping

The implemented sponge update is equivalent at an interior node to:

```math
\frac{u^{n+1}-2u^n+u^{n-1}}{\Delta t^2}
+
\gamma
\frac{u^{n+1}-u^{n-1}}{2\Delta t}
=
c^2\Delta_hu^n.
```

After division by $c^2$:

```math
m\,\delta_{tt}u^n+m\gamma\bar v^n-\Delta_hu^n=0.
```

Multiply by $\bar v^n$ and repeat the conservative derivation. The additional
term is:

```math
m\gamma(\bar v^n)^2\geq0.
```

Therefore the exact discrete global balance for the centered damping update
is:

```math
\boxed{
\frac{E_h^{n+1/2}-E_h^{n-1/2}}{\Delta t}
+D_h^n
=0,
}
```

where:

```math
\boxed{
D_h^n
=
\sum_{i,j}
\frac{\gamma_{i,j}}{c_{i,j}^2}
(\bar v_{i,j}^n)^2\Delta x\Delta y.
}
```

For $\gamma\geq0$, $D_h^n$ is nonnegative, so damping cannot increase the
discrete energy through this balance.

For a subdomain, the complete equation includes both terms:

```math
\text{energy-change rate}
+\text{net outward power}
+\text{damping loss}
=0.
```

---

## 15. Discrete source work

The current source is applied after the ordinary finite-difference update. It
does not appear as a force term inside the update equation. Denote the
provisional wave-update result by $u_*^{n+1}$ and the field after source
application by $u^{n+1}$.

The most direct source-work measurement is the energy jump caused by that
operation:

```math
\boxed{
W_{\mathrm{src}}^{n+1/2}
=
E_h(u^{n+1},u^n)
-
E_h(u_*^{n+1},u^n).
}
```

This definition follows the implemented algorithm rather than assigning an
unimplemented continuous force model to the source. It works for additive
and overwrite-style sources.

The work can be negative during an individual step. A prescribed source may
oppose and remove part of a field already present at the source cells. Net
work over a suitable interval is the meaningful injected-energy quantity.

With both damping and a source, the conceptual balance is:

```math
\boxed{
\text{energy change}
+\text{outward transported energy}
+\text{dissipated energy}
=
\text{source work}.
}
```

---

## 16. Relation to the existing diagnostic

The current diagnostic uses:

```math
\frac{u^n-u^{n-1}}{\Delta t}
```

for velocity and node-centered two-cell differences such as:

```math
\frac{u_{i+1,j}^n-u_{i-1,j}^n}{2\Delta x}
```

for gradients. These are individually valid second-order derivative
approximations, but they are not collocated in time and the spatial gradient
is not the face operator whose divergence produces the solver's Laplacian.

The result approximates continuous scalar energy and is useful for broad
behavior and regression checks. It is not the exact invariant derived in
Section 9. This explains why previous validation allowed noticeable energy
drift even for source-free fixed-boundary runs.

Phase 5.1 should either replace it or preserve it under a name that clearly
distinguishes it from the leapfrog-conserved energy.

---

## 17. Validation consequences

The derivation produces identities that can be tested directly.

### 17.1 Global conservative test

For fixed boundaries with no source or damping:

```math
E_h^{n+1/2}-E_h^{n-1/2}\approx0.
```

The tolerance should be based on floating-point accumulation, not the current
five-percent drift allowance.

### 17.2 Local control-volume test

For any interior rectangular control volume:

```math
\frac{E_{\Omega,h}^{n+1/2}-E_{\Omega,h}^{n-1/2}}{\Delta t}
+P_{\partial\Omega,h}^n
\approx0.
```

This test verifies energy placement, face signs, and aperture spacing
together.

### 17.3 Direction test

A right-traveling plane-wave-like field must produce positive $x$ power; a
left-traveling field must produce negative $x$ power.

### 17.4 Damping test

For a source-free sponge run:

```math
\frac{E_h^{n+1/2}-E_h^{n-1/2}}{\Delta t}+D_h^n\approx0.
```

### 17.5 Source-work test

The difference between post-source and provisional half-step energy must equal
the reported discrete source work.

### 17.6 Material-interface test

The balance should remain valid for discontinuous $c(x,y)$ because $m=1/c^2$
is retained at the nodes and no unsupported face averaging is introduced.

---

## 18. Phase 5 implementation contract

The derivation establishes the following design decisions:

1. Keep the governing equation and wave update unchanged.
2. Use the leapfrog half-step invariant as the authoritative energy.
3. Associate each energy sample with time $t^{n+1/2}$.
4. Compute spatial energy with one-cell face differences.
5. Compute `F_x` with shape `(nx - 1, ny)`.
6. Compute `F_y` with shape `(nx, ny - 1)`.
7. Compute integer-time flux from $u^{n-1}$, $u^n$, and $u^{n+1}$.
8. Integrate vertical power with $\Delta y$ and horizontal power with
   $\Delta x$.
9. Define every monitor's direction and sign convention explicitly.
10. Average instantaneous power products over time.
11. Report damping loss and source work as separate balance terms.
12. Describe the result as scalar-wave energy and flux, not complete
    electromagnetic energy or Poynting flux.
13. Configure flux monitors by explicit integer face indices and half-open
    transverse index intervals.
14. Store immutable aperture profiles and derive integrated power from them.
15. Reject direct overlap between flux apertures and active source cells.
16. Derive instantaneous signed power from stored profiles using the correct
    transverse grid spacing.
17. Average power over explicit half-open sample windows and preserve its sign.
18. Report optional harmonic cycle metadata without requiring a frequency for
    nonharmonic simulations.

---

## 19. Summary of the derivation

The continuous argument is:

```text
m u_tt - Laplacian(u) = 0
    -> multiply by u_t
    -> use the ordinary product rule
    -> identify d/dt of stored energy
    -> identify divergence of flux.
```

It gives:

```math
\boxed{
e=\frac{u_t^2}{2c^2}+\frac12|\nabla u|^2,
\qquad
\mathbf F=-u_t\nabla u.
}
```

The discrete argument follows the same structure:

```text
centered finite-difference equation
    -> multiply by centered velocity
    -> use difference of squares in time
    -> use summation by parts in space
    -> identify half-step energy and face flux.
```

It gives the exact invariant:

```math
\boxed{
E_h^{n+1/2}
=
\frac12\langle mv^{n+1/2},v^{n+1/2}\rangle_N
+
\frac12\langle D_xu^{n+1},D_xu^n\rangle_X
+
\frac12\langle D_yu^{n+1},D_yu^n\rangle_Y,
}
```

and the matching face fluxes:

```math
\boxed{
F_x^n=-D_xu^n\,\operatorname{avg}_x(\bar v^n),
\qquad
F_y^n=-D_yu^n\,\operatorname{avg}_y(\bar v^n).
}
```

The essential principle is that the update, energy, and flux must use one
compatible set of time differences and spatial operators. Their shared
algebra—not resemblance to the continuous formulas alone—is what guarantees
numerical conservation.
