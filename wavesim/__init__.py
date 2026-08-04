"""Public API for the photonics simulator."""

from .analysis import (
    HarmonicResponse,
    estimate_harmonic_response,
)
from .config import (
    BoundaryConfig,
    FieldMonitorConfig,
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
from .monitors import FieldMonitorState
from .solver import SimulationState, Wave2DSimulation


__all__ = [
    "BoundaryConfig",
    "FieldMonitorConfig",
    "FieldMonitorState",
    "GridConfig",
    "HarmonicResponse",
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
    "estimate_harmonic_response",
    "validate_material_map",
    "validate_refractive_index_array",
]
