"""Material maps for the 2D scalar-wave solver."""

from dataclasses import dataclass

import numpy as np

from .config import GridConfig, MaterialConfig


@dataclass
class MaterialMap:
    """Spatial material properties defined over the simulation grid."""

    refractive_index: np.ndarray
    wave_speed: np.ndarray


def validate_material_map(
    material_map: MaterialMap,
    grid: GridConfig,
) -> None:
    """Validate material-array shapes and numerical values."""
    expected_shape = grid.shape

    if material_map.refractive_index.shape != expected_shape:
        raise ValueError(
            "Refractive-index map must have shape "
            f"{expected_shape}, received "
            f"{material_map.refractive_index.shape}."
        )

    if material_map.wave_speed.shape != expected_shape:
        raise ValueError(
            "Wave-speed map must have shape "
            f"{expected_shape}, received "
            f"{material_map.wave_speed.shape}."
        )

    if not np.all(np.isfinite(material_map.refractive_index)):
        raise ValueError(
            "Refractive-index map must contain only finite values."
        )

    if not np.all(np.isfinite(material_map.wave_speed)):
        raise ValueError(
            "Wave-speed map must contain only finite values."
        )

    if np.any(material_map.refractive_index <= 0):
        raise ValueError(
            "All refractive-index values must be positive."
        )

    if np.any(material_map.wave_speed <= 0):
        raise ValueError(
            "All wave-speed values must be positive."
        )


def create_uniform_material_map(
    grid: GridConfig,
    material: MaterialConfig,
) -> MaterialMap:
    """Create a uniform material map from the material configuration."""
    refractive_index = np.full(
        grid.shape,
        material.background_refractive_index,
        dtype=float,
    )

    wave_speed = (
        material.reference_wave_speed / refractive_index
    )

    material_map = MaterialMap(
        refractive_index=refractive_index,
        wave_speed=wave_speed,
    )

    validate_material_map(material_map, grid)
    return material_map

