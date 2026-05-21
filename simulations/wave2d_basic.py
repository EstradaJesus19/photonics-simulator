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
    raise ValueError("Simulation unstable: reduce dt or increase dx/dy.")

# Wave fields
u_prev = np.zeros((nx, ny)) # u at time t-dt
u_curr = np.zeros((nx, ny)) # u at time t
u_next = np.zeros((nx, ny)) # u at time t+dt

# Initial Gaussian pulse
x0, y0 = nx // 3, ny // 3
sigma = 8.0

x = np.arange(nx)
y = np.arange(ny)
X, Y = np.meshgrid(x, y, indexing="ij")

u_curr = np.exp(-((X - x0) ** 2 + (Y - y0) ** 2) / (2 * sigma**2))
u_prev = u_curr.copy()

# Figure setup
fig, ax = plt.subplots()
image = ax.imshow(
    u_curr,
    cmap="RdBu",
    vmin=-1,
    vmax=1,
    origin="lower",
    animated=True,
)

ax.set_title("2D Wave Equation Simulation")
plt.colorbar(image, ax=ax)


def update(frame):
    global u_prev, u_curr, u_next

    laplacian = (
        (np.roll(u_curr, 1, axis=0) - 2 * u_curr + np.roll(u_curr, -1, axis=0)) / dx**2
        + (np.roll(u_curr, 1, axis=1) - 2 * u_curr + np.roll(u_curr, -1, axis=1)) / dy**2
    )

    u_next = 2 * u_curr - u_prev + (c * dt) ** 2 * laplacian

    # Simple fixed boundary conditions
    u_next[0, :] = 0
    u_next[-1, :] = 0
    u_next[:, 0] = 0
    u_next[:, -1] = 0

    u_prev, u_curr = u_curr, u_next.copy()

    image.set_array(u_curr)
    ax.set_xlabel(f"Step: {frame}")
    return [image]


animation = FuncAnimation(fig, update, frames=steps, interval=30, blit=True)
plt.show()