"""Generate the Phase 4 advanced-geometry gallery."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from simulations.materials.wave2d_geometry_gallery.maps import (
    BACKGROUND_REFRACTIVE_INDEX,
    COMPOSITION_CIRCLE_INDEX,
    COMPOSITION_POLYGON_INDEX,
    COMPOSITION_RECTANGLE_INDEX,
    create_gallery_maps,
)


OUTPUT_DIRECTORY = Path(
    "outputs/figures/phase_4"
)

GALLERY_FIGURE_NAME = (
    "2026-08-27_advanced_geometry_gallery.png"
)

CASE_TITLES = {
    "circle": "Circle",
    "ellipse": "Ellipse",
    "rotated_rectangle": (
        "Rotated Rectangle\n"
        r"$\theta = 30^\circ$"
    ),
    "rotated_ellipse": (
        "Rotated Ellipse\n"
        r"$\theta = 35^\circ$"
    ),
    "concave_polygon": "Concave Polygon",
    "ordered_composition": (
        "Ordered Composition\n"
        "circle → rectangle → polygon"
    ),
}


def create_gallery_figure():
    """Create the six-panel advanced-geometry gallery."""
    grid, gallery_maps = create_gallery_maps()

    figure, axes = plt.subplots(
        2,
        3,
        figsize=(12.0, 7.2),
        sharex=True,
        sharey=True,
        layout="constrained",
    )

    shared_minimum = BACKGROUND_REFRACTIVE_INDEX
    shared_maximum = COMPOSITION_POLYGON_INDEX

    image = None

    for index, (
        name,
        material_map,
    ) in enumerate(gallery_maps.items()):
        row, column = divmod(index, 3)
        axis = axes[row, column]

        refractive_index = (
            material_map.refractive_index
        )

        image = axis.imshow(
            refractive_index.T,
            origin="lower",
            cmap="viridis",
            vmin=shared_minimum,
            vmax=shared_maximum,
            aspect="equal",
            interpolation="nearest",
        )

        unique_indices = np.unique(
            refractive_index
        )

        if unique_indices.size > 1:
            interface_levels = 0.5 * (
                unique_indices[:-1]
                + unique_indices[1:]
            )

            axis.contour(
                refractive_index.T,
                levels=interface_levels,
                colors="white",
                linewidths=0.8,
            )

        axis.set_title(CASE_TITLES[name])
        axis.set_xlim(0, grid.nx - 1)
        axis.set_ylim(0, grid.ny - 1)

        if row == 1:
            axis.set_xlabel("x grid index")

        if column == 0:
            axis.set_ylabel("y grid index")

    if image is None:
        raise RuntimeError(
            "The geometry gallery contains no panels."
        )

    colorbar = figure.colorbar(
        image,
        ax=axes,
        location="right",
        fraction=0.03,
        pad=0.02,
        ticks=(
            BACKGROUND_REFRACTIVE_INDEX,
            COMPOSITION_CIRCLE_INDEX,
            1.5,
            COMPOSITION_RECTANGLE_INDEX,
            COMPOSITION_POLYGON_INDEX,
        ),
        label=r"Refractive index $n(x,y)$",
    )

    colorbar.ax.set_yticklabels(
        ("1.0", "1.3", "1.5", "1.6", "2.0")
    )

    title = figure.suptitle(
        "Phase 4 Advanced-Geometry Gallery\n"
        "Physical-coordinate masks and "
        "ordered material composition"
    )

    figure.canvas.draw()

    panel_left = axes[0, 0].get_position().x0
    panel_right = axes[0, 2].get_position().x1

    title.set_x(
        0.5 * (panel_left + panel_right)
    )

    return figure


def generate_figures(
    output_directory: Path = OUTPUT_DIRECTORY,
) -> tuple[Path, ...]:
    """Generate and save the geometry-gallery figure."""
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure = create_gallery_figure()
    output_path = (
        output_directory / GALLERY_FIGURE_NAME
    )

    figure.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(figure)

    return (output_path,)


def main() -> None:
    """Generate and report the gallery figure path."""
    output_paths = generate_figures()

    print("Generated advanced-geometry figures:")

    for output_path in output_paths:
        print(f"  {output_path}")


if __name__ == "__main__":
    main()