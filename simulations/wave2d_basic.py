import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# Grid parameters
nx = 150 # Number of grid points in x direction
ny = 150 # Number of grid points in y direction
dx = 1.0 # Grid spacing in x direction
dy = 1.0 # Grid spacing in y direction

# Time parameters
c = 1.0 # Wave speed
dt = 0.4 # Time step
steps = 500 # Number of time steps

# Stability condition estimate for 2D wave equation
courant = c * dt * np.sqrt(1 / dx**2 + 1 / dy**2)

if courant > 1:
    raise ValueError(
        f"Simulation unstable: Courant number = {courant:.3f}. "
        "Reduce dt or increase dx/dy."
    )

print(f"Courant number: {courant:.3f}")

# Wave fields
u_prev = np.zeros((nx, ny)) # u at time t-dt
u_curr = np.zeros((nx, ny)) # u at time t
u_next = np.zeros((nx, ny)) # u at time t+dt

# Initial Gaussian pulse
x0, y0 = nx // 2, ny // 2
sigma = 8.0

x = np.arange(nx)
y = np.arange(ny)
X, Y = np.meshgrid(x, y, indexing="ij")

u_curr = np.exp(-((X - x0) ** 2 + (Y - y0) ** 2) / (2 * sigma**2))
u_prev = u_curr.copy()

# Helper function: apply fixed boundary conditions
def apply_fixed_boundaries(u):
    # Apply fixed zero-value boundary conditions.
    u[0, :] = 0.0
    u[-1, :] = 0.0
    u[:, 0] = 0.0
    u[:, -1] = 0.0

# Apply boundary condition to the initial fields
apply_fixed_boundaries(u_curr)
apply_fixed_boundaries(u_prev)

# Helper function: compute one time step of the wave equation
def step_wave(u_prev, u_curr):
    # The Laplacian is computed only on interior points.
    # Boundaries are handled separately.
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

    apply_fixed_boundaries(u_next)

    return u_next

# Set up the plot
fig, ax = plt.subplots()

image = ax.imshow(
    u_curr.T,
    cmap="RdBu",
    vmin=-1,
    vmax=1,
    origin="lower",
    animated=True,
)

ax.set_title("2D Scalar Wave Equation — Explicit Interior Update")
ax.set_xlabel("x grid index")
ax.set_ylabel("y grid index")

plt.colorbar(image, ax=ax, label="Wave amplitude")


# Animation update function
def update(frame):
    global u_prev, u_curr

    u_next = step_wave(u_prev, u_curr)

    u_prev = u_curr.copy()
    u_curr = u_next.copy()

    image.set_array(u_curr.T)
    ax.set_title(f"2D Scalar Wave Equation — Step {frame}")

    return [image]


animation = FuncAnimation(
    fig,
    update,
    frames=steps,
    interval=30,
    blit=False,
)

plt.show()