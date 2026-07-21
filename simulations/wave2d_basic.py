import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# ============================================================
# 1. Grid configuration
# ============================================================

nx = 150  # Number of grid points in the x direction
ny = 150  # Number of grid points in the y direction

dx = 1.0  # Grid spacing in the x direction
dy = 1.0  # Grid spacing in the y direction


# ============================================================
# 2. Time configuration
# ============================================================

c = 1.0      # Wave propagation speed
dt = 0.4     # Time step
steps = 500  # Total number of simulation steps


# ============================================================
# 3. Initial-condition and source configuration
# ============================================================

# Available initial conditions:
# "gaussian" -> localized Gaussian pulse at t = 0
# "zero"     -> field starts from rest, useful with continuous sources
initial_condition_type = "gaussian"

# Gaussian-pulse parameters
x0 = nx // 2  # Initial Gaussian center in x
y0 = ny // 2  # Initial Gaussian center in y
sigma = 8.0   # Width of the Gaussian pulse

# Available source options:
# "none"       -> no continuous source
# "point_sine" -> sinusoidal point source
source_type = "none"

# Point-source parameters
source_x = nx // 2
source_y = ny // 2

source_amplitude = 0.5
source_frequency = 0.03

# ============================================================
# 4. Boundary-condition configuration
# ============================================================

# Available options:
# "fixed"  -> reflective, fixed-value outer boundary
# "sponge" -> smoothly damped layer followed by a fixed outer boundary
boundary_type = "sponge"

# Sponge parameters
damping_width = 50
max_damping = 0.02
damping_exponent = 2

# Diagnostics
show_damping_profile = True
print_energy_interval = 50

# A narrower color range makes weak late-time reflections visible.
# The initial Gaussian will appear saturated, but that is acceptable while diagnosing boundary reflections.
display_limit = 0.5


# ============================================================
# 5. Configuration validation
# ============================================================

VALID_BOUNDARIES = {"fixed", "sponge"}
VALID_INITIAL_CONDITIONS = {"gaussian", "zero"}
VALID_SOURCES = {"none", "point_sine"}

if boundary_type not in VALID_BOUNDARIES:
    raise ValueError(
        f"Unknown boundary type: {boundary_type!r}. "
        f"Available options: {sorted(VALID_BOUNDARIES)}"
    )

if initial_condition_type not in VALID_INITIAL_CONDITIONS:
    raise ValueError(
        f"Unknown initial condition: {initial_condition_type!r}. "
        f"Available options: {sorted(VALID_INITIAL_CONDITIONS)}"
    )

if source_type not in VALID_SOURCES:
    raise ValueError(
        f"Unknown source type: {source_type!r}. "
        f"Available options: {sorted(VALID_SOURCES)}"
    )

if nx < 3 or ny < 3:
    raise ValueError("The grid must contain at least 3 points per direction.")

if dx <= 0 or dy <= 0:
    raise ValueError("Grid spacing dx and dy must be positive.")

if c <= 0:
    raise ValueError("Wave speed c must be positive.")

if dt <= 0:
    raise ValueError("Time step dt must be positive.")

if steps <= 0:
    raise ValueError("The number of time steps must be positive.")

if sigma <= 0:
    raise ValueError("Gaussian width sigma must be positive.")

if not (0 <= source_x < nx):
    raise ValueError("source_x must be inside the simulation grid.")

if not (0 <= source_y < ny):
    raise ValueError("source_y must be inside the simulation grid.")

if source_amplitude < 0:
    raise ValueError("source_amplitude cannot be negative.")

if source_frequency < 0:
    raise ValueError("source_frequency cannot be negative.")

if damping_width < 1:
    raise ValueError("damping_width must be at least 1.")

maximum_damping_width = min(nx, ny) // 2

if damping_width >= maximum_damping_width:
    raise ValueError(
        f"damping_width must be smaller than {maximum_damping_width} for the current grid."
    )

if max_damping < 0:
    raise ValueError("max_damping cannot be negative.")

if damping_exponent <= 0:
    raise ValueError("damping_exponent must be positive.")


# ============================================================
# 6. CFL stability check
# ============================================================

courant = c * dt * np.sqrt(1.0 / dx**2 + 1.0 / dy**2)

if courant > 1.0:
    raise ValueError(
        f"Simulation unstable: Courant number = {courant:.3f}. Reduce dt or increase dx and/or dy."
    )

print("Simulation configuration")
print("------------------------")
print(f"Grid:               {nx} × {ny}")
print(f"Courant number:     {courant:.3f}")
print(f"Boundary condition: {boundary_type}")

if boundary_type == "sponge":
    print(f"Damping width:      {damping_width}")
    print(f"Maximum damping:    {max_damping}")
    print(f"Damping exponent:   {damping_exponent}")

print(f"Initial condition:  {initial_condition_type}")
print(f"Source type:        {source_type}")

if source_type == "point_sine":
    print(f"Source position:    ({source_x}, {source_y})")
    print(f"Source amplitude:   {source_amplitude}")
    print(f"Source frequency:   {source_frequency}")

# ============================================================
# 7. Numerical helper functions
# ============================================================

def apply_fixed_boundaries(field):
    """
    Force the outermost grid points to zero.

    This is a homogeneous Dirichlet boundary condition:

        u = 0

    For the fixed-boundary case, this produces strong reflection.

    For the sponge case, the outgoing wave should be attenuated before
    reaching this outer boundary, so the reflected amplitude should be
    much smaller.
    """
    field[0, :] = 0.0
    field[-1, :] = 0.0
    field[:, 0] = 0.0
    field[:, -1] = 0.0


def compute_laplacian(field):
    """
    Compute the 2D finite-difference Laplacian on interior points.

    The second derivatives are approximated using centered differences:

        d²u/dx² ≈ (u[i+1,j] - 2u[i,j] + u[i-1,j]) / dx²

        d²u/dy² ≈ (u[i,j+1] - 2u[i,j] + u[i,j-1]) / dy²
    """
    laplacian = np.zeros_like(field)

    laplacian[1:-1, 1:-1] = (
        (
            field[2:, 1:-1]
            - 2.0 * field[1:-1, 1:-1]
            + field[:-2, 1:-1]
        )
        / dx**2
        +
        (
            field[1:-1, 2:]
            - 2.0 * field[1:-1, 1:-1]
            + field[1:-1, :-2]
        )
        / dy**2
    )

    return laplacian


def create_gaussian_pulse():
    """
    Create the initial 2D Gaussian field distribution.
    """
    x = np.arange(nx)
    y = np.arange(ny)

    X, Y = np.meshgrid(x, y, indexing="ij")

    pulse = np.exp(
        -(
            (X - x0) ** 2
            + (Y - y0) ** 2
        )
        / (2.0 * sigma**2)
    )

    apply_fixed_boundaries(pulse)

    return pulse

def create_zero_field():
    """
    Create a zero initial field.

    This is useful when the simulation is driven by a continuous source.
    """
    return np.zeros((nx, ny))

def create_damping_profile():
    """
    Create the spatial damping coefficient gamma(x,y).

    The damping coefficient is:

    - zero in the central physical region,
    - smoothly increasing inside the sponge layer,
    - equal to approximately max_damping at the outer boundary.

    The profile follows:

        gamma = max_damping * normalized_depth**damping_exponent

    A higher exponent makes the damping begin more gently but increase
    more strongly near the outer edge.
    """
    x_indices = np.arange(nx)
    y_indices = np.arange(ny)

    distance_x = np.minimum(x_indices, nx - 1 - x_indices)  # Distance to the nearest x-boundary
    distance_y = np.minimum(y_indices, ny - 1 - y_indices)  # Distance to the nearest y-boundary

    distance_to_edge = np.minimum( # Create a 2D array of distances to the nearest edge
        distance_x[:, np.newaxis],
        distance_y[np.newaxis, :],
    )

    normalized_depth = np.clip(
        (damping_width - distance_to_edge) / damping_width,
        0.0,
        1.0,
    )

    gamma = max_damping * normalized_depth**damping_exponent

    return gamma


def initialize_fields():
    """
    Construct u at t = 0 and at t = -dt.

    The wave equation is second order in time, so two time states are needed.

    For a Gaussian initial condition, the initial velocity is assumed to be zero.
    A second-order Taylor expansion is used to initialize the previous field.

    For a zero initial condition, both fields are zero.
    This is useful when the wave is generated by a continuous source.
    """
    if initial_condition_type == "gaussian":
        current = create_gaussian_pulse()
        initial_laplacian = compute_laplacian(current)

        previous = current + 0.5 * (c * dt) ** 2 * initial_laplacian

    elif initial_condition_type == "zero":
        current = create_zero_field()
        previous = create_zero_field()

    else:
        raise ValueError(
            f"Unknown initial condition: {initial_condition_type}. "
            "Use 'gaussian' or 'zero'."
        )

    apply_fixed_boundaries(current)
    apply_fixed_boundaries(previous)

    return previous, current


def compute_energy(previous, current):
    """
    Estimate the total scalar-wave energy in the domain.

    The continuous wave energy density is proportional to:

        0.5 * u_t² + 0.5 * c² * |grad(u)|²

    This diagnostic is useful for comparing boundaries:

    - fixed boundaries should retain most energy in the domain,
    - sponge boundaries should remove energy as the wave exits.

    The discrete energy is approximate, but it is sufficient for
    comparing simulations using the same grid and time step.
    """
    velocity = (current - previous) / dt

    gradient_x = np.zeros_like(current)
    gradient_y = np.zeros_like(current)

    gradient_x[1:-1, 1:-1] = (
        current[2:, 1:-1] - current[:-2, 1:-1]
    ) / (2.0 * dx)

    gradient_y[1:-1, 1:-1] = (
        current[1:-1, 2:] - current[1:-1, :-2]
    ) / (2.0 * dy)

    energy_density = 0.5 * velocity**2 + 0.5 * c**2 * (
        gradient_x**2 + gradient_y**2
    )

    return float(np.sum(energy_density) * dx * dy)

def apply_source(field, step_index):
    """
    Apply the selected continuous source to the field.

    The current implementation uses a hard point source:

        u[source_x, source_y] += A sin(2π f n)

    where:
    - A is the source amplitude,
    - f is the discrete source frequency in cycles per time step,
    - n is the time-step index.

    This is a simple source model for Phase 1.
    """
    if source_type == "none":
        return

    if source_type == "point_sine":
        source_value = source_amplitude * np.sin(
            2.0 * np.pi * source_frequency * step_index
        )

        field[source_x, source_y] += source_value
        return

    raise ValueError(
        f"Unknown source type: {source_type}. "
        "Use 'none' or 'point_sine'."
    )

# ============================================================
# 8. Create the damping profile
# ============================================================

if boundary_type == "sponge":
    damping_profile = create_damping_profile()
else:
    damping_profile = np.zeros((nx, ny))

print(f"Profile minimum:    {damping_profile.min():.6f}")
print(f"Profile maximum:    {damping_profile.max():.6f}")


# ============================================================
# 9. Initialize the wave fields
# ============================================================

u_prev, u_curr = initialize_fields()


# ============================================================
# 10. Time-stepping function
# ============================================================

def step_wave(previous, current):
    """
    Advance the scalar wave equation by one time step.

    Fixed-boundary equation:

        u_tt = c² laplacian(u)

    Sponge equation:

        u_tt + gamma(x,y) * u_t = c² laplacian(u)

    The damped equation is discretized with a centered approximation
    for both u_tt and u_t.
    """
    laplacian = compute_laplacian(current)
    next_field = np.zeros_like(current)

    if boundary_type == "fixed":
        next_field[1:-1, 1:-1] = (
            2.0 * current[1:-1, 1:-1]
            - previous[1:-1, 1:-1]
            + (c * dt) ** 2 * laplacian[1:-1, 1:-1]
        )

    elif boundary_type == "sponge":
        gamma = damping_profile[1:-1, 1:-1]

        next_field[1:-1, 1:-1] = (
            2.0 * current[1:-1, 1:-1]
            - (1.0 - gamma * dt / 2.0)
            * previous[1:-1, 1:-1]
            + (c * dt) ** 2
            * laplacian[1:-1, 1:-1]
        ) / (1.0 + gamma * dt / 2.0)

    apply_fixed_boundaries(next_field)

    return next_field


# ============================================================
# 11. Diagnostic storage
# ============================================================

energy_history = [compute_energy(u_prev, u_curr)]
initial_energy = energy_history[0]

ENERGY_EPSILON = 1e-12

print(f"Initial energy:     {initial_energy:.6f}")


# ============================================================
# 12. Optional damping-profile visualization
# ============================================================

if boundary_type == "sponge" and show_damping_profile:
    profile_figure, profile_axis = plt.subplots()

    profile_image = profile_axis.imshow(
        damping_profile.T,
        origin="lower",
        cmap="viridis",
    )

    profile_axis.set_title(
        "Sponge damping profile\n"
        f"width={damping_width}, "
        f"max={max_damping}, "
        f"exponent={damping_exponent}"
    )

    profile_axis.set_xlabel("x grid index")
    profile_axis.set_ylabel("y grid index")

    profile_figure.colorbar(
        profile_image,
        ax=profile_axis,
        label=r"Damping coefficient $\gamma(x,y)$",
    )


# ============================================================
# 13. Wave-field animation
# ============================================================

figure, axis = plt.subplots()

field_image = axis.imshow(
    u_curr.T,
    cmap="RdBu",
    vmin=-display_limit,
    vmax=display_limit,
    origin="lower",
    animated=True,
)

axis.set_xlabel("x grid index")
axis.set_ylabel("y grid index")

figure.colorbar(
    field_image,
    ax=axis,
    label="Wave amplitude",
)


def update(frame):
    """
    Advance the simulation, record energy, and refresh the animation.
    """
    global u_prev, u_curr

    u_next = step_wave(u_prev, u_curr)

    # Inject the selected source after the wave update.
    apply_source(u_next, frame + 1)

    current_energy = compute_energy(u_curr, u_next)
    energy_history.append(current_energy)

    if source_type == "none" and initial_energy > ENERGY_EPSILON:
        relative_energy = current_energy / initial_energy

        energy_text = (
            f"Remaining energy: "
            f"{100.0 * relative_energy:.2f}%"
        )
    else:
        energy_text = f"Total energy: {current_energy:.4f}"

    u_prev, u_curr = u_curr, u_next

    field_image.set_array(u_curr.T)

    axis.set_title(
        f"2D Scalar Wave Equation — {boundary_type.capitalize()} Boundary\n"
        f"Step {frame + 1} | {energy_text} | Source: {source_type}"
    )

    if (
        frame == 0
        or (frame + 1) % print_energy_interval == 0
        or frame == steps - 1
    ):
        if source_type == "none" and initial_energy > ENERGY_EPSILON:
            relative_energy = current_energy / initial_energy

            print(
                f"Step {frame + 1:4d}: "
                f"energy = {current_energy:.6f}, "
                f"remaining = {100.0 * relative_energy:.2f}%"
            )

        else:
            print(
                f"Step {frame + 1:4d}: "
                f"total energy = {current_energy:.6f}"
            )

    return [field_image]


animation = FuncAnimation(
    figure,
    update,
    frames=steps,
    interval=30,
    blit=False,
    repeat=False,
)

plt.show()


# ============================================================
# 14. Energy-history plot
# ============================================================

energy_array = np.asarray(energy_history)

energy_figure, energy_axis = plt.subplots()

if source_type == "none" and initial_energy > ENERGY_EPSILON:
    plotted_energy = energy_array / initial_energy

    energy_axis.set_title(
        f"Normalized Wave Energy — "
        f"{boundary_type.capitalize()} Boundary"
    )

    energy_axis.set_ylabel("Energy / initial energy")

else:
    plotted_energy = energy_array

    energy_axis.set_title(
        f"Total Wave Energy — "
        f"{boundary_type.capitalize()} Boundary, "
        f"Source: {source_type}"
    )

    energy_axis.set_ylabel("Total wave energy")

energy_axis.plot(
    np.arange(len(plotted_energy)),
    plotted_energy,
)

energy_axis.set_xlabel("Time step")
energy_axis.grid(True)

plt.show()