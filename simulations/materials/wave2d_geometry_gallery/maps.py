"""Construct material maps for the advanced-geometry gallery."""

import numpy as np

from wavesim.config import GridConfig, MaterialConfig
from wavesim.geometry import (
    create_circular_mask,
    create_elliptical_mask,
    create_polygon_mask,
    create_rectangular_mask,
)
from wavesim.materials import (
    MaterialMap,
    MaterialRegion,
    compose_material_regions,
    create_background_refractive_index_array,
    create_material_map_from_refractive_index,
)


GRID_NX = 90
GRID_NY = 70

BACKGROUND_REFRACTIVE_INDEX = 1.0
SINGLE_REGION_REFRACTIVE_INDEX = 1.5

COMPOSITION_CIRCLE_INDEX = 1.3
COMPOSITION_RECTANGLE_INDEX = 1.6
COMPOSITION_POLYGON_INDEX = 2.0

GALLERY_CASE_NAMES = (
    "circle",
    "ellipse",
    "rotated_rectangle",
    "rotated_ellipse",
    "concave_polygon",
    "ordered_composition",
)


def _finalize_regions(
    grid: GridConfig,
    material: MaterialConfig,
    regions: tuple[MaterialRegion, ...],
) -> MaterialMap:
    """Compose and finalize one gallery material map."""
    background = (
        create_background_refractive_index_array(
            grid,
            material,
        )
    )

    refractive_index = compose_material_regions(
        background,
        grid,
        regions=regions,
    )

    return create_material_map_from_refractive_index(
        grid,
        material,
        refractive_index,
    )


def create_gallery_maps(
) -> tuple[GridConfig, dict[str, MaterialMap]]:
    """Create all material maps shown in the gallery."""
    grid = GridConfig(
        nx=GRID_NX,
        ny=GRID_NY,
    )
    material = MaterialConfig(
        reference_wave_speed=1.0,
        background_refractive_index=(
            BACKGROUND_REFRACTIVE_INDEX
        ),
    )

    center_x = (grid.nx - 1) * grid.dx / 2.0
    center_y = (grid.ny - 1) * grid.dy / 2.0

    circle_mask = create_circular_mask(
        grid,
        center_x=center_x,
        center_y=center_y,
        radius=18.0,
    )

    ellipse_mask = create_elliptical_mask(
        grid,
        center_x=center_x,
        center_y=center_y,
        radius_x=25.0,
        radius_y=12.0,
    )

    rotated_rectangle_mask = (
        create_rectangular_mask(
            grid,
            center_x=center_x,
            center_y=center_y,
            width=46.0,
            height=16.0,
            angle_degrees=30.0,
        )
    )

    rotated_ellipse_mask = (
        create_elliptical_mask(
            grid,
            center_x=center_x,
            center_y=center_y,
            radius_x=25.0,
            radius_y=10.0,
            angle_degrees=35.0,
        )
    )

    concave_polygon_mask = create_polygon_mask(
        grid,
        vertices=(
            (18.0, 18.0),
            (71.0, 18.0),
            (71.0, 31.0),
            (51.0, 31.0),
            (51.0, 55.0),
            (37.0, 55.0),
            (37.0, 31.0),
            (18.0, 31.0),
        ),
    )

    composition_circle_mask = (
        create_circular_mask(
            grid,
            center_x=35.0,
            center_y=35.0,
            radius=22.0,
        )
    )

    composition_rectangle_mask = (
        create_rectangular_mask(
            grid,
            center_x=49.0,
            center_y=35.0,
            width=50.0,
            height=14.0,
            angle_degrees=30.0,
        )
    )

    composition_polygon_mask = (
        create_polygon_mask(
            grid,
            vertices=(
                (46.0, 14.0),
                (76.0, 35.0),
                (46.0, 56.0),
            ),
        )
    )

    single_region_masks = {
        "circle": circle_mask,
        "ellipse": ellipse_mask,
        "rotated_rectangle": (
            rotated_rectangle_mask
        ),
        "rotated_ellipse": rotated_ellipse_mask,
        "concave_polygon": (
            concave_polygon_mask
        ),
    }

    gallery_maps = {
        name: _finalize_regions(
            grid,
            material,
            regions=(
                MaterialRegion(
                    mask=mask,
                    refractive_index=(
                        SINGLE_REGION_REFRACTIVE_INDEX
                    ),
                ),
            ),
        )
        for name, mask in single_region_masks.items()
    }

    gallery_maps["ordered_composition"] = (
        _finalize_regions(
            grid,
            material,
            regions=(
                MaterialRegion(
                    mask=composition_circle_mask,
                    refractive_index=(
                        COMPOSITION_CIRCLE_INDEX
                    ),
                ),
                MaterialRegion(
                    mask=(
                        composition_rectangle_mask
                    ),
                    refractive_index=(
                        COMPOSITION_RECTANGLE_INDEX
                    ),
                ),
                MaterialRegion(
                    mask=composition_polygon_mask,
                    refractive_index=(
                        COMPOSITION_POLYGON_INDEX
                    ),
                ),
            ),
        )
    )

    if tuple(gallery_maps) != GALLERY_CASE_NAMES:
        raise RuntimeError(
            "Geometry-gallery cases were created "
            "in an unexpected order."
        )

    return grid, gallery_maps


def main() -> None:
    """Report the generated gallery material maps."""
    grid, gallery_maps = create_gallery_maps()

    print()
    print("Two-dimensional advanced-geometry gallery")
    print("-----------------------------------------")
    print(f"Grid: {grid.nx} x {grid.ny}")

    for name, material_map in gallery_maps.items():
        unique_indices = np.unique(
            material_map.refractive_index
        )

        formatted_indices = ", ".join(
            f"{value:.3f}"
            for value in unique_indices
        )

        print(
            f"{name}: refractive indices "
            f"[{formatted_indices}]"
        )


if __name__ == "__main__":
    main()