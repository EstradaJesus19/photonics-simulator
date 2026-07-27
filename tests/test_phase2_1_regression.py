"""Regression test for the verified Phase 2.1 default simulation."""

import unittest

from wavesim.config import create_default_config
from wavesim.solver import Wave2DSimulation


class DefaultSimulationRegressionTest(unittest.TestCase):
    """Confirm that modularization does not change numerical results."""

    def test_default_energy_checkpoints(self) -> None:
        simulation = Wave2DSimulation(create_default_config())

        expected_energy = {
            1: 0.03182002983188608,
            50: 10.861960749063872,
            100: 22.499974544196014,
            250: 50.83918140302646,
            500: 70.13486394160974,
        }

        for step in range(1, 501):
            simulation.advance()

            if step in expected_energy:
                self.assertAlmostEqual(
                    simulation.current_energy,
                    expected_energy[step],
                    places=10,
                )

        self.assertEqual(simulation.state.step_index, 500)
        self.assertEqual(len(simulation.state.energy_history), 501)
        self.assertAlmostEqual(
            float(simulation.state.current.min()),
            -0.5893284375273641,
            places=10,
        )
        self.assertAlmostEqual(
            float(simulation.state.current.max()),
            0.365929446861314,
            places=10,
        )


if __name__ == "__main__":
    unittest.main()
