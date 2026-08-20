"""Run the default interactive 2D scalar-wave simulation."""

from wavesim.config import create_default_config
from wavesim.visualization import run_interactive_simulation


def main() -> None:
    """Construct and run the default Phase 2.2 simulation."""
    config = create_default_config()
    run_interactive_simulation(config)


if __name__ == "__main__":
    main()
