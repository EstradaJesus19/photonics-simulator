"""Generate reproducible Phase 4.7 directional-coupler figures."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from simulations.structures.wave2d_directional_coupler.simulation import (
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
    "2026-08-25_directional_coupler_material_map.png"
)
FIELD_FIGURE_NAME = (
    "2026-08-25_directional_coupler_rms_comparison.png"
)
HISTORY_FIGURE_NAME = (
    "2026-08-25_directional_coupler_monitor_histories.png"
)
RESPONSE_FIGURE_NAME = (
    "2026-08-25_directional_coupler_response_comparison.png"
)


def run_pair_with_rms_fields(
) -> tuple[
    Wave2DSimulation,
    Wave2DSimulation,
    np.ndarray,
    np.ndarray,
]:
    """Run both scenarios and calculate analysis-window RMS fields."""
    config, isolated_map, coupled_map = (
        create_scenario_pair()
    )

    isolated = Wave2DSimulation(
        config,
        material_map=isolated_map,
    )
    coupled = Wave2DSimulation(
        config,
        material_map=coupled_map,
    )

    isolated_sum = np.zeros(config.grid.shape)
    isolated_square_sum = np.zeros(
        config.grid.shape
    )
    coupled_sum = np.zeros(config.grid.shape)
    coupled_square_sum = np.zeros(
        config.grid.shape
    )

    sample_count = 0

    for _ in range(config.time.steps):
        isolated.advance()
        coupled.advance()

        step = isolated.state.step_index

        if (
            ANALYSIS_START_STEP
            <= step
            < ANALYSIS_STOP_STEP
        ):
            isolated_field = (
                isolated.state.current
            )
            coupled_field = (
                coupled.state.current
            )

            isolated_sum += isolated_field
            isolated_square_sum += (
                isolated_field**2
            )

            coupled_sum += coupled_field
            coupled_square_sum += (
                coupled_field**2
            )

            sample_count += 1

    if sample_count == 0:
        raise RuntimeError(
            "The RMS analysis window contains no samples."
        )

    isolated_mean = isolated_sum / sample_count
    coupled_mean = coupled_sum / sample_count

    isolated_variance = (
        isolated_square_sum / sample_count
        - isolated_mean**2
    )
    coupled_variance = (
        coupled_square_sum / sample_count
        - coupled_mean**2
    )

    isolated_rms = np.sqrt(
        np.maximum(isolated_variance, 0.0)
    )
    coupled_rms = np.sqrt(
        np.maximum(coupled_variance, 0.0)
    )

    return (
        isolated,
        coupled,
        isolated_rms,
        coupled_rms,
    )


def create_material_figure(
    coupled: Wave2DSimulation,
):
    """Create the coupler material and measurement layout."""
    figure, axis = plt.subplots(
        figsize=(10.0, 5.8),
        layout="constrained",
    )

    refractive_index = (
        coupled.material_map.refractive_index
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
        coupled,
    )

    axis.set_title(
        "Directional Coupler: "
        "Material and Measurement Layout"
    )
    axis.set_xlabel("x grid index")
    axis.set_ylabel("y grid index")
    axis.legend(loc="upper right")

    figure.colorbar(
        image,
        ax=axis,
        pad=0.02,
        label=r"Refractive index $n(x,y)$",
    )

    return figure


def create_rms_comparison_figure(
    isolated: Wave2DSimulation,
    coupled: Wave2DSimulation,
    isolated_rms: np.ndarray,
    coupled_rms: np.ndarray,
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
            np.max(isolated_rms),
            np.max(coupled_rms),
        )
    )

    field_data = (
        (
            axes[0],
            isolated,
            isolated_rms,
            "Isolated Upper-Guide Reference",
        ),
        (
            axes[1],
            coupled,
            coupled_rms,
            "Directional Coupler",
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
        "Matched Directional-Coupler RMS Comparison\n"
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
    coupled: Wave2DSimulation,
):
    """Create directional-coupler monitor histories."""
    figure = add_monitor_history_figure(
        coupled,
        analysis_start_step=ANALYSIS_START_STEP,
        analysis_stop_step=ANALYSIS_STOP_STEP,
    )

    if figure is None:
        raise RuntimeError(
            "The directional-coupler scenario "
            "has no monitors."
        )

    axis = figure.axes[0]
    axis.set_title(
        "Directional-Coupler Monitor Histories"
    )

    figure.set_size_inches(10.0, 5.8)
    figure.tight_layout()
    return figure


def create_response_figure(
    isolated: Wave2DSimulation,
    coupled: Wave2DSimulation,
):
    """Create matched amplitude and spatial-transfer comparisons."""
    isolated_responses = (
        analyze_monitor_responses(isolated)
    )
    coupled_responses = (
        analyze_monitor_responses(coupled)
    )

    isolated_upper = isolated_responses[
        "second_upper"
    ].amplitude
    isolated_lower = isolated_responses[
        "second_lower"
    ].amplitude

    coupled_first_upper = coupled_responses[
        "first_upper"
    ].amplitude
    coupled_first_lower = coupled_responses[
        "first_lower"
    ].amplitude
    coupled_second_upper = coupled_responses[
        "second_upper"
    ].amplitude
    coupled_second_lower = coupled_responses[
        "second_lower"
    ].amplitude

    lower_window_enhancement = (
        coupled_second_lower / isolated_lower
    )

    isolated_lower_share = (
        isolated_lower
        / (isolated_upper + isolated_lower)
    )
    coupled_upstream_lower_share = (
        coupled_first_lower
        / (
            coupled_first_upper
            + coupled_first_lower
        )
    )
    coupled_downstream_lower_share = (
        coupled_second_lower
        / (
            coupled_second_upper
            + coupled_second_lower
        )
    )

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(11.5, 4.8),
        layout="constrained",
    )

    positions = np.arange(2)
    bar_width = 0.36

    isolated_bars = axes[0].bar(
        positions - bar_width / 2.0,
        [isolated_upper, isolated_lower],
        width=bar_width,
        label="Isolated reference",
    )
    coupled_bars = axes[0].bar(
        positions + bar_width / 2.0,
        [
            coupled_second_upper,
            coupled_second_lower,
        ],
        width=bar_width,
        label="Directional coupler",
    )

    axes[0].set_xticks(
        positions,
        ("Upper window", "Lower window"),
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
        isolated_bars,
        fmt="%.3f",
        padding=3,
    )
    axes[0].bar_label(
        coupled_bars,
        fmt="%.3f",
        padding=3,
    )

    share_labels = (
        "Isolated\n"
        "downstream",
        "Coupled\n"
        "upstream",
        "Coupled\n"
        "downstream",
    )
    share_values = (
        isolated_lower_share,
        coupled_upstream_lower_share,
        coupled_downstream_lower_share,
    )

    share_bars = axes[1].bar(
        share_labels,
        share_values,
    )

    axes[1].set_ylim(0.0, 1.05)
    axes[1].set_ylabel(
        "Lower-window amplitude share"
    )
    axes[1].set_title(
        "Spatial Field Redistribution"
    )
    axes[1].grid(
        axis="y",
        alpha=0.3,
    )
    axes[1].bar_label(
        share_bars,
        fmt="%.3f",
        padding=3,
    )

    figure.suptitle(
        "Directional-Coupler Harmonic Response\n"
        f"Downstream lower-window enhancement: "
        f"{lower_window_enhancement:.3f}×"
    )

    return figure


def generate_figures(
    output_directory: Path = OUTPUT_DIRECTORY,
) -> tuple[Path, ...]:
    """Generate and save all Phase 4.7 documentation figures."""
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        isolated,
        coupled,
        isolated_rms,
        coupled_rms,
    ) = run_pair_with_rms_fields()

    figures_and_names = (
        (
            create_material_figure(coupled),
            MATERIAL_FIGURE_NAME,
        ),
        (
            create_rms_comparison_figure(
                isolated,
                coupled,
                isolated_rms,
                coupled_rms,
            ),
            FIELD_FIGURE_NAME,
        ),
        (
            create_history_figure(coupled),
            HISTORY_FIGURE_NAME,
        ),
        (
            create_response_figure(
                isolated,
                coupled,
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

    print("Generated directional-coupler figures:")

    for output_path in output_paths:
        print(f"  {output_path}")


if __name__ == "__main__":
    main()