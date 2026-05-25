import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# ============================================================
# 1. Grid parameters
# ============================================================

nx = 150  # Number of grid points in x direction
ny = 150  # Number of grid points in y direction
dx = 1.0  # Grid spacing in x direction
dy = 1.0  # Grid spacing in y direction


# ============================================================
# 2. Time parameters
# ============================================================

c = 1.0      # Wave speed
dt = 0.4     # Time step
steps = 500  # Number of time steps


# ============================================================
# 3. Boundary condition parameters
# ============================================================

# Available options:
# "fixed"  -> fixed zero-value boundaries
# "damped" -> damping layer near the edges + fixed outer boundary
boundary_type = "damped"

damping_width = 20
damping_strength = 0.030


# ============================================================
# 4. Stability condition estimate for 2D wave equation
# ============================================================

courant = c * dt * np.sqrt(1 / dx**2 + 1 / dy**2)

if courant > 1:
    raise ValueError(
        f"Simulation unstable: Courant number = {courant:.3f}. "
        "Reduce dt or increase dx/dy."
    )

print(f"Courant number: {courant:.3f}")
print(f"Boundary condition: {boundary_type}")


# ============================================================
# 5. Wave fields
# ============================================================

u_prev = np.zeros((nx, ny))  # u at time t-dt
u_curr = np.zeros((nx, ny))  # u at time t
u_next = np.zeros((nx, ny))  # u at time t+dt


# ============================================================
# 6. Initial Gaussian pulse
# ============================================================

x0, y0 = nx // 2, ny // 2
sigma = 8.0

x = np.arange(nx)
y = np.arange(ny)
X, Y = np.meshgrid(x, y, indexing="ij")

u_curr = np.exp(-((X - x0) ** 2 + (Y - y0) ** 2) / (2 * sigma**2))
u_prev = u_curr.copy()


# ============================================================
# 7. Boundary condition functions
# ============================================================

def apply_fixed_boundaries(u):
    # Apply fixed zero-value boundary conditions.
    u[0, :] = 0.0
    u[-1, :] = 0.0
    u[:, 0] = 0.0
    u[:, -1] = 0.0


def create_damping_mask(nx, ny, damping_width=20, damping_strength=0.015):
    #Create a damping mask to reduce reflections near the boundaries.
    #The mask is equal to 1 in the central region and becomes smaller near the edges of the domain.

    mask = np.ones((nx, ny))

    for i in range(nx):
        for j in range(ny):
            distance_to_edge = min(i, j, nx - 1 - i, ny - 1 - j)

            if distance_to_edge < damping_width:
                mask[i, j] = np.exp(
                    -damping_strength * (damping_width - distance_to_edge) ** 2
                )

    return mask


def apply_boundary_condition(u):

    if boundary_type == "fixed":
        apply_fixed_boundaries(u)

    elif boundary_type == "damped":
        u *= damping_mask
        apply_fixed_boundaries(u)

    else:
        raise ValueError(
            f"Unknown boundary type: {boundary_type}. "
            "Use 'fixed' or 'damped'."
        )


# Create damping mask.
# If the selected boundary type is fixed, this mask is just not used.
damping_mask = create_damping_mask(
    nx,
    ny,
    damping_width=damping_width,
    damping_strength=damping_strength,
)


# Apply boundary condition to the initial fields
apply_boundary_condition(u_curr)
apply_boundary_condition(u_prev)


# ============================================================
# 8. Helper function: compute one time step
# ============================================================

def step_wave(u_prev, u_curr):

    #Compute one time step of the 2D scalar wave equation.
    u_next = np.zeros_like(u_curr)
    laplacian = np.zeros_like(u_curr)

    laplacian[1:-1, 1:-1] = (
        (u_curr[2:, 1:-1] - 2 * u_curr[1:-1, 1:-1] + u_curr[:-2, 1:-1]) / dx**2
        +
        (u_curr[1:-1, 2:] - 2 * u_curr[1:-1, 1:-1] + u_curr[1:-1, :-2]) / dy**2
    )

    u_next[1:-1, 1:-1] = (
        2 * u_curr[1:-1, 1:-1]
        - u_prev[1:-1, 1:-1]
        + (c * dt) ** 2 * laplacian[1:-1, 1:-1]
    )

    apply_boundary_condition(u_next)

    return u_next


# ============================================================
# 9. Set up the plot
# ============================================================

fig, ax = plt.subplots()

image = ax.imshow(
    u_curr.T,
    cmap="RdBu",
    vmin=-1,
    vmax=1,
    origin="lower",
    animated=True,
)

ax.set_title(f"2D Scalar Wave Equation — Boundary: {boundary_type}")
ax.set_xlabel("x grid index")
ax.set_ylabel("y grid index")

plt.colorbar(image, ax=ax, label="Wave amplitude")


# ============================================================
# 10. Animation update function
# ============================================================

def update(frame):
    global u_prev, u_curr

    u_next = step_wave(u_prev, u_curr)

    u_prev = u_curr.copy()
    u_curr = u_next.copy()

    image.set_array(u_curr.T)
    ax.set_title(f"2D Scalar Wave Equation — Boundary: {boundary_type} — Step {frame}")

    return [image]


animation = FuncAnimation(
    fig,
    update,
    frames=steps,
    interval=30,
    blit=False,
)

plt.show()