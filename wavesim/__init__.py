"""Public API for the photonics simulator."""

from .config import (
    BoundaryConfig,
    GridConfig,
    InitialConditionConfig,
    MaterialConfig,
    SimulationConfig,
    SourceConfig,
    TimeConfig,
    VisualizationConfig,
    create_default_config,
)
from .materials import (
    MaterialMap,
    add_rectangular_region,
    create_background_refractive_index_array,
    create_material_map_from_refractive_index,
    create_planar_interface_material_map,
    create_rectangular_material_map,
    create_uniform_material_map,
    validate_material_map,
    validate_refractive_index_array,
)
from .solver import SimulationState, Wave2DSimulation


__all__ = [
    "BoundaryConfig",
    "GridConfig",
    "InitialConditionConfig",
    "MaterialConfig",
    "MaterialMap",
    "SimulationConfig",
    "SimulationState",
    "SourceConfig",
    "TimeConfig",
    "VisualizationConfig",
    "Wave2DSimulation",
    "add_rectangular_region",
    "create_background_refractive_index_array",
    "create_default_config",
    "create_material_map_from_refractive_index",
    "create_planar_interface_material_map",
    "create_rectangular_material_map",
    "create_uniform_material_map",
    "validate_material_map",
    "validate_refractive_index_array",
]