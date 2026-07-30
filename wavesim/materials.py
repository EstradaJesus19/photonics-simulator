"""Material maps for the 2D scalar-wave solver."""

from dataclasses import dataclass

import numpy as np

from .config import GridConfig, MaterialConfig


@dataclass
class MaterialMap:
    """Spatial material properties defined over the simulation grid."""

    refractive_index: np.ndarray
    wave_speed: np.ndarray


def validate_refractive_index_array(
    refractive_index: np.ndarray,
    grid: GridConfig,
) -> None:
    """Validate one refractive-index array."""
    expected_shape = grid.shape

    if refractive_index.shape != expected_shape:
        raise ValueError(
            "Refractive-index map must have shape "
            f"{expected_shape}, received "
            f"{refractive_index.shape}."
        )

    if not np.all(np.isfinite(refractive_index)):
        raise ValueError(
            "Refractive-index map must contain only finite values."
        )

    if np.any(refractive_index <= 0):
        raise ValueError(
            "All refractive-index values must be positive."
        )


def validate_material_map(
    material_map: MaterialMap,
    grid: GridConfig,
) -> None:
    """Validate material-array shapes and numerical values."""
    validate_refractive_index_array(
        material_map.refractive_index,
        grid,
    )

    expected_shape = grid.shape

    if material_map.wave_speed.shape != expected_shape:
        raise ValueError(
            "Wave-speed map must have shape "
            f"{expected_shape}, received "
            f"{material_map.wave_speed.shape}."
        )

    if not np.all(np.isfinite(material_map.wave_speed)):
        raise ValueError(
            "Wave-speed map must contain only finite values."
        )

    if np.any(material_map.wave_speed <= 0):
        raise ValueError(
            "All wave-speed values must be positive."
        )


def create_material_map_from_refractive_index(
    grid: GridConfig,
    material: MaterialConfig,
    refractive_index: np.ndarray,
) -> MaterialMap:
    """Create a validated material map from a completed index array."""
    refractive_index_copy = np.array(
        refractive_index,
        dtype=float,
        copy=True,
    )

    validate_refractive_index_array(
        refractive_index_copy,
        grid,
    )

    wave_speed = (
        material.reference_wave_speed
        / refractive_index_copy
    )

    material_map = MaterialMap(
        refractive_index=refractive_index_copy,
        wave_speed=wave_speed,
    )

    validate_material_map(material_map, grid)
    return material_map


def create_background_refractive_index_array(
    grid: GridConfig,
    material: MaterialConfig,
) -> np.ndarray:
    """Create a validated background refractive-index array."""
    refractive_index = np.full(
        grid.shape,
        material.background_refractive_index,
        dtype=float,
    )

    validate_refractive_index_array(
        refractive_index,
        grid,
    )

    return refractive_index


def add_rectangular_region(
    refractive_index: np.ndarray,
    grid: GridConfig,
    *,
    x_start: int,
    x_stop: int,
    y_start: int,
    y_stop: int,
    region_refractive_index: float,
) -> np.ndarray:
    """Return a copy with one rectangular region applied.

    Bounds use half-open NumPy slices. Unlike the dedicated embedded
    rectangle constructor, this general operation may touch a grid edge.
    A later operation overwrites earlier values in overlapping cells.
    """
    validate_refractive_index_array(
        refractive_index,
        grid,
    )

    bounds = {
        "x_start": x_start,
        "x_stop": x_stop,
        "y_start": y_start,
        "y_stop": y_stop,
    }

    for name, value in bounds.items():
        if isinstance(value, bool) or not isinstance(
            value,
            (int, np.integer),
        ):
            raise TypeError(f"{name} must be an integer.")

    if not 0 <= x_start < x_stop <= grid.nx:
        raise ValueError(
            "Rectangle x bounds must define a nonempty region "
            "inside the grid."
        )

    if not 0 <= y_start < y_stop <= grid.ny:
        raise ValueError(
            "Rectangle y bounds must define a nonempty region "
            "inside the grid."
        )

    if (
        not np.isfinite(region_refractive_index)
        or region_refractive_index <= 0
    ):
        raise ValueError(
            "region_refractive_index must be finite and positive."
        )

    updated_refractive_index = np.array(
        refractive_index,
        dtype=float,
        copy=True,
    )

    updated_refractive_index[
        x_start:x_stop,
        y_start:y_stop,
    ] = region_refractive_index

    validate_refractive_index_array(
        updated_refractive_index,
        grid,
    )

    return updated_refractive_index


def create_uniform_material_map(
    grid: GridConfig,
    material: MaterialConfig,
) -> MaterialMap:
    """Create a uniform material map from the material configuration."""
    refractive_index = (
        create_background_refractive_index_array(
            grid,
            material,
        )
    )

    return create_material_map_from_refractive_index(
        grid,
        material,
        refractive_index,
    )


def create_planar_interface_material_map(
    grid: GridConfig,
    material: MaterialConfig,
    interface_index: int,
    right_refractive_index: float,
) -> MaterialMap:
    """Create a vertical interface between uniform left and right media.

    The background refractive index fills cells before ``interface_index``.
    The right refractive index fills cells from ``interface_index`` onward,
    so the interface lies between x indices ``interface_index - 1`` and
    ``interface_index``.
    """
    if isinstance(interface_index, bool) or not isinstance(
        interface_index,
        (int, np.integer),
    ):
        raise TypeError("interface_index must be an integer.")

    if not 1 <= interface_index < grid.nx:
        raise ValueError(
            "interface_index must leave at least one x cell "
            "on each side of the interface."
        )

    if (
        not np.isfinite(right_refractive_index)
        or right_refractive_index <= 0
    ):
        raise ValueError(
            "right_refractive_index must be finite and positive."
        )

    refractive_index = (
        create_background_refractive_index_array(
            grid,
            material,
        )
    )

    refractive_index = add_rectangular_region(
        refractive_index,
        grid,
        x_start=interface_index,
        x_stop=grid.nx,
        y_start=0,
        y_stop=grid.ny,
        region_refractive_index=right_refractive_index,
    )

    return create_material_map_from_refractive_index(
        grid,
        material,
        refractive_index,
    )


def create_rectangular_material_map(
    grid: GridConfig,
    material: MaterialConfig,
    x_start: int,
    x_stop: int,
    y_start: int,
    y_stop: int,
    rectangle_refractive_index: float,
) -> MaterialMap:
    """Create a uniform background with one embedded rectangle.

    Rectangle bounds use half-open slices:
    ``[x_start:x_stop, y_start:y_stop]``.
    The rectangle must remain strictly inside the grid.
    """
    bounds = {
        "x_start": x_start,
        "x_stop": x_stop,
        "y_start": y_start,
        "y_stop": y_stop,
    }

    for name, value in bounds.items():
        if isinstance(value, bool) or not isinstance(
            value,
            (int, np.integer),
        ):
            raise TypeError(f"{name} must be an integer.")

    if not 1 <= x_start < x_stop <= grid.nx - 1:
        raise ValueError(
            "Rectangle x bounds must define a nonempty region "
            "strictly inside the grid."
        )

    if not 1 <= y_start < y_stop <= grid.ny - 1:
        raise ValueError(
            "Rectangle y bounds must define a nonempty region "
            "strictly inside the grid."
        )

    if (
        not np.isfinite(rectangle_refractive_index)
        or rectangle_refractive_index <= 0
    ):
        raise ValueError(
            "rectangle_refractive_index must be finite and positive."
        )

    refractive_index = (
        create_background_refractive_index_array(
            grid,
            material,
        )
    )

    refractive_index = add_rectangular_region(
        refractive_index,
        grid,
        x_start=x_start,
        x_stop=x_stop,
        y_start=y_start,
        y_stop=y_stop,
        region_refractive_index=(
            rectangle_refractive_index
        ),
    )

    return create_material_map_from_refractive_index(
        grid,
        material,
        refractive_index,
    )