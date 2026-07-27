"""Core package for the photonics simulator."""

from .config import (
    BoundaryConfig,
    GridConfig,
    InitialConditionConfig,
    SimulationConfig,
    SourceConfig,
    TimeConfig,
    VisualizationConfig,
    create_default_config,
)
from .solver import SimulationState, Wave2DSimulation

__all__ = [
    "BoundaryConfig",
    "GridConfig",
    "InitialConditionConfig",
    "SimulationConfig",
    "SimulationState",
    "SourceConfig",
    "TimeConfig",
    "VisualizationConfig",
    "Wave2DSimulation",
    "create_default_config",
]
