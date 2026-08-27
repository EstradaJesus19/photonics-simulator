"""Generate reproducible Phase 4.6 waveguide figures."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from simulations.structures.wave2d_straight_waveguide.simulation import (
    ANALYSIS_START_STEP,
    ANALYSIS_STOP_STEP,
    analyze_monitor_responses,
    create_scenario_pair,
)
from wavesim.solver import Wave2DSimulation
from wavesim.visualization import (
    add_monitor_history_figure,
    add_source_and_monitor_overlays,
)


OUTPUT_DIRECTORY = Path(
    "outputs/figures/phase_4"
)

MATERIAL_FIGURE_NAME = (
    "2026-08-22_straight_waveguide_material_map.png"
)
FIELD_FIGURE_NAME = (
    "2026-08-22_straight_waveguide_rms_comparison.png"
)
HISTORY_FIGURE_NAME = (
    "2026-08-22_straight_waveguide_monitor_histories.png"
)
RESPONSE_FIGURE_NAME = (
    "2026-08-22_straight_waveguide_response_comparison.png"
)


def run_pair_with_rms_fields(
) -> tuple[
    Wave2DSimulation,
    Wave2DSimulation,
    np.ndarray,
    np.ndarray,
]:
    """Run the pair and calculate analysis-window RMS fields."""
    config, reference_map, waveguide_map = (
        create_scenario_pair()
    )

    reference = Wave2DSimulation(
        config,
        material_map=reference_map,
    )
    waveguide = Wave2DSimulation(
        config,
        material_map=waveguide_map,
    )

    reference_sum = np.zeros(config.grid.shape)
    reference_square_sum = np.zeros(
        config.grid.shape
    )
    waveguide_sum = np.zeros(config.grid.shape)
    waveguide_square_sum = np.zeros(
        config.grid.shape
    )

    sample_count = 0

    for _ in range(config.time.steps):
        reference.advance()
        waveguide.advance()

        step = reference.state.step_index

        if (
            ANALYSIS_START_STEP
            <= step
            < ANALYSIS_STOP_STEP
        ):
            reference_field = (
                reference.state.current
            )
            waveguide_field = (
                waveguide.state.current
            )

            reference_sum += reference_field
            reference_square_sum += (
                reference_field**2
            )

            waveguide_sum += waveguide_field
            waveguide_square_sum += (
                waveguide_field**2
            )

            sample_count += 1

    if sample_count == 0:
        raise RuntimeError(
            "The RMS analysis window contains no samples."
        )

    reference_mean = (
        reference_sum / sample_count
    )
    waveguide_mean = (
        waveguide_sum / sample_count
    )

    reference_variance = (
        reference_square_sum / sample_count
        - reference_mean**2
    )
    waveguide_variance = (
        waveguide_square_sum / sample_count
        - waveguide_mean**2
    )

    reference_rms = np.sqrt(
        np.maximum(reference_variance, 0.0)
    )
    waveguide_rms = np.sqrt(
        np.maximum(waveguide_variance, 0.0)
    )

    return (
        reference,
        waveguide,
        reference_rms,
        waveguide_rms,
    )


def create_material_figure(
    waveguide: Wave2DSimulation,
):
    """Create the waveguide material and measurement layout."""
    figure, axis = plt.subplots(
        figsize=(10.0, 5.5)
    )

    refractive_index = (
        waveguide.material_map.refractive_index
    )

    image = axis.imshow(
        refractive_index.T,
        origin="lower",
        cmap="viridis",
        vmin=float(refractive_index.min()),
        vmax=float(refractive_index.max()),
        aspect="equal",
    )

    add_source_and_monitor_overlays(
        axis,
        waveguide,
    )

    axis.set_title(
        "Straight Dielectric Waveguide: "
        "Material and Measurement Layout"
    )
    axis.set_xlabel("x grid index")
    axis.set_ylabel("y grid index")
    axis.legend(loc="upper right")

    figure.colorbar(
        image,
        ax=axis,
        label=r"Refractive index $n(x,y)$",
    )

    figure.tight_layout()
    return figure


def create_rms_comparison_figure(
    reference: Wave2DSimulation,
    waveguide: Wave2DSimulation,
    reference_rms: np.ndarray,
    waveguide_rms: np.ndarray,
):
    """Create matched RMS-field panels with one color scale."""
    figure, axes = plt.subplots(
        2,
        1,
        figsize=(10.0, 7.5),
        sharex=True,
        sharey=True,
        layout="constrained",
        gridspec_kw={
            "hspace": 0.08,
        },
    )

    shared_maximum = float(
        max(
            np.max(reference_rms),
            np.max(waveguide_rms),
        )
    )

    field_data = (
        (
            axes[0],
            reference,
            reference_rms,
            "Uniform Reference",
        ),
        (
            axes[1],
            waveguide,
            waveguide_rms,
            "Straight Dielectric Waveguide",
        ),
    )

    image = None

    for (
        axis,
        simulation,
        rms_field,
        title,
    ) in field_data:
        image = axis.imshow(
            rms_field.T,
            origin="lower",
            cmap="magma",
            vmin=0.0,
            vmax=shared_maximum,
            aspect="equal",
        )

        refractive_index = (
            simulation.material_map.refractive_index
        )

        if np.unique(refractive_index).size > 1:
            interface_level = 0.5 * (
                float(refractive_index.min())
                + float(refractive_index.max())
            )

            axis.contour(
                refractive_index.T,
                levels=[interface_level],
                colors="cyan",
                linewidths=1.0,
            )

        add_source_and_monitor_overlays(
            axis,
            simulation,
        )

        sponge_width = (
            simulation.config.boundary.damping_width
        )
        grid = simulation.config.grid

        axis.set_xlim(
            sponge_width,
            grid.nx - sponge_width - 1,
        )
        axis.set_ylim(
            sponge_width,
            grid.ny - sponge_width - 1,
        )

        axis.set_title(title)
        axis.set_ylabel("y grid index")

    axes[0].tick_params(
        axis="x",
        labelbottom=False,
    )
    axes[1].set_xlabel("x grid index")

    figure.colorbar(
        image,
        ax=axes,
        location="right",
        fraction=0.035,
        pad=0.02,
        aspect=35,
        label=r"Analysis-window RMS $E_z$",
    )

    title = figure.suptitle(
        "Matched RMS Field Comparison\n"
        f"Analysis steps "
        f"[{ANALYSIS_START_STEP}, "
        f"{ANALYSIS_STOP_STEP})"
    )

    figure.canvas.draw()

    panel_left = axes[0].get_position().x0
    panel_right = axes[0].get_position().x1

    title.set_x(
        0.5 * (panel_left + panel_right)
    )

    return figure


def create_history_figure(
    waveguide: Wave2DSimulation,
):
    """Create the waveguide monitor-history figure."""
    figure = add_monitor_history_figure(
        waveguide,
        analysis_start_step=ANALYSIS_START_STEP,
        analysis_stop_step=ANALYSIS_STOP_STEP,
    )

    if figure is None:
        raise RuntimeError(
            "The waveguide scenario has no monitors."
        )

    axis = figure.axes[0]
    axis.set_title(
        "Straight-Waveguide Monitor Histories"
    )

    figure.set_size_inches(10.0, 5.5)
    figure.tight_layout()
    return figure


def create_response_figure(
    reference: Wave2DSimulation,
    waveguide: Wave2DSimulation,
):
    """Create harmonic-amplitude and contrast comparisons."""
    reference_responses = (
        analyze_monitor_responses(reference)
    )
    waveguide_responses = (
        analyze_monitor_responses(waveguide)
    )

    reference_center = reference_responses[
        "second_center"
    ].amplitude
    reference_offset = reference_responses[
        "second_offset"
    ].amplitude

    waveguide_core = waveguide_responses[
        "second_center"
    ].amplitude
    waveguide_cladding = waveguide_responses[
        "second_offset"
    ].amplitude

    reference_contrast = (
        reference_center / reference_offset
    )
    waveguide_contrast = (
        waveguide_core / waveguide_cladding
    )

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(11.0, 4.8),
    )

    positions = np.arange(2)
    bar_width = 0.36

    reference_bars = axes[0].bar(
        positions - bar_width / 2.0,
        [reference_center, reference_offset],
        width=bar_width,
        label="Uniform reference",
    )
    waveguide_bars = axes[0].bar(
        positions + bar_width / 2.0,
        [waveguide_core, waveguide_cladding],
        width=bar_width,
        label="Dielectric waveguide",
    )

    axes[0].set_xticks(
        positions,
        ("Center/core", "Offset/cladding"),
    )
    axes[0].set_ylabel(
        r"Harmonic field amplitude $|E_z|$"
    )
    axes[0].set_title(
        "Downstream Monitor Amplitudes"
    )
    axes[0].grid(
        axis="y",
        alpha=0.3,
    )
    axes[0].legend()

    axes[0].bar_label(
        reference_bars,
        fmt="%.3f",
        padding=3,
    )
    axes[0].bar_label(
        waveguide_bars,
        fmt="%.3f",
        padding=3,
    )

    contrast_bars = axes[1].bar(
        ("Uniform reference", "Waveguide"),
        (
            reference_contrast,
            waveguide_contrast,
        ),
    )

    axes[1].set_ylabel(
        "Center-to-offset amplitude contrast"
    )
    axes[1].set_title(
        "Spatial Confinement Contrast"
    )
    axes[1].grid(
        axis="y",
        alpha=0.3,
    )
    axes[1].bar_label(
        contrast_bars,
        fmt="%.3f",
        padding=3,
    )

    contrast_improvement = (
        waveguide_contrast / reference_contrast
    )

    figure.suptitle(
        "Straight-Waveguide Harmonic Response\n"
        f"Contrast improvement: "
        f"{contrast_improvement:.3f}×"
    )

    figure.tight_layout()
    return figure


def generate_figures(
    output_directory: Path = OUTPUT_DIRECTORY,
) -> tuple[Path, ...]:
    """Generate and save all Phase 4.6 documentation figures."""
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        reference,
        waveguide,
        reference_rms,
        waveguide_rms,
    ) = run_pair_with_rms_fields()

    figures_and_names = (
        (
            create_material_figure(waveguide),
            MATERIAL_FIGURE_NAME,
        ),
        (
            create_rms_comparison_figure(
                reference,
                waveguide,
                reference_rms,
                waveguide_rms,
            ),
            FIELD_FIGURE_NAME,
        ),
        (
            create_history_figure(waveguide),
            HISTORY_FIGURE_NAME,
        ),
        (
            create_response_figure(
                reference,
                waveguide,
            ),
            RESPONSE_FIGURE_NAME,
        ),
    )

    output_paths = []

    for figure, filename in figures_and_names:
        output_path = output_directory / filename

        figure.savefig(
            output_path,
            dpi=180,
            bbox_inches="tight",
        )
        plt.close(figure)

        output_paths.append(output_path)

    return tuple(output_paths)


def main() -> None:
    """Generate and report documentation-figure paths."""
    output_paths = generate_figures()

    print("Generated straight-waveguide figures:")

    for output_path in output_paths:
        print(f"  {output_path}")


if __name__ == "__main__":
    main()
