"""Cross-feature validation for completed Phase 3 infrastructure."""

import unittest

import numpy as np

import wavesim
from simulations.measurements.wave2d_controlled_line_source import (
    create_scenario as create_controlled_scenario,
)
from simulations.measurements.wave2d_interface_measurement import (
    create_scenario_pair,
)
from wavesim.solver import Wave2DSimulation


EXPECTED_PHASE3_PUBLIC_NAMES = {
    "FieldMonitorConfig",
    "FieldMonitorState",
    "HarmonicResponse",
    "estimate_harmonic_response",
}


class Phase3PublicApiTests(unittest.TestCase):
    """Protect the stable Phase 3 package-level API."""

    def test_expected_phase3_names_are_public(self) -> None:
        for name in EXPECTED_PHASE3_PUBLIC_NAMES:
            with self.subTest(name=name):
                self.assertIn(name, wavesim.__all__)
                self.assertTrue(hasattr(wavesim, name))


class Phase3ScenarioContractTests(unittest.TestCase):
    """Verify official Phase 3 scenario construction."""

    def test_controlled_scenario_constructs_with_monitors(self) -> None:
        config, material_map = create_controlled_scenario()

        simulation = Wave2DSimulation(
            config,
            material_map=material_map,
        )

        self.assertEqual(config.source.kind, "line_sine")
        self.assertEqual(
            set(simulation.monitor_states),
            {"first", "second"},
        )
        self.assertFalse(simulation.source_profile.flags.writeable)
        self.assertTrue(
            np.all(np.isfinite(material_map.wave_speed))
        )

    def test_interface_pair_uses_identical_configuration(self) -> None:
        config, reference_map, interface_map = (
            create_scenario_pair()
        )

        reference = Wave2DSimulation(
            config,
            material_map=reference_map,
        )
        interface = Wave2DSimulation(
            config,
            material_map=interface_map,
        )

        self.assertIs(reference.config, interface.config)
        self.assertEqual(
            set(reference.monitor_states),
            set(interface.monitor_states),
        )
        self.assertEqual(
            reference.state.current.shape,
            interface.state.current.shape,
        )

    def test_interface_pair_has_expected_material_ranges(self) -> None:
        _, reference_map, interface_map = (
            create_scenario_pair()
        )

        np.testing.assert_array_equal(
            np.unique(reference_map.refractive_index),
            [1.0],
        )
        np.testing.assert_array_equal(
            np.unique(interface_map.refractive_index),
            [1.0, 1.5],
        )


if __name__ == "__main__":
    unittest.main()
