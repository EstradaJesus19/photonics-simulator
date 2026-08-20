"""Tests for paired scalar-interface measurements."""

import unittest

import numpy as np

from simulations.measurements.wave2d_interface_measurement import (
    ANALYSIS_START_STEP,
    ANALYSIS_STOP_STEP,
    DOWNSTREAM_MONITOR_X,
    INTERFACE_INDEX,
    MONITOR_Y_START,
    MONITOR_Y_STOP,
    RIGHT_REFRACTIVE_INDEX,
    SOURCE_X,
    SOURCE_Y_START,
    SOURCE_Y_STOP,
    UPSTREAM_MONITOR_X,
    analyze_scattering,
    create_scenario_pair,
    run_to_completion,
)
from wavesim.config import (
    compute_courant_number,
    validate_config,
)
from wavesim.solver import Wave2DSimulation


class InterfaceMeasurementConfigurationTests(unittest.TestCase):
    """Verify construction of the paired experiment."""

    def setUp(self) -> None:
        (
            self.config,
            self.reference_map,
            self.interface_map,
        ) = create_scenario_pair()

    def test_both_maps_share_one_configuration(self) -> None:
        validate_config(self.config)

        self.assertEqual(self.config.grid.nx, 340)
        self.assertEqual(self.config.grid.ny, 180)
        self.assertEqual(self.config.time.steps, 900)
        self.assertEqual(self.config.source.kind, "line_sine")

    def test_reference_map_is_uniform(self) -> None:
        np.testing.assert_array_equal(
            self.reference_map.refractive_index,
            np.ones(self.config.grid.shape),
        )
        np.testing.assert_array_equal(
            self.reference_map.wave_speed,
            np.ones(self.config.grid.shape),
        )

    def test_interface_map_has_expected_materials(self) -> None:
        refractive_index = self.interface_map.refractive_index

        np.testing.assert_array_equal(
            refractive_index[:INTERFACE_INDEX, :],
            np.ones(
                (
                    INTERFACE_INDEX,
                    self.config.grid.ny,
                )
            ),
        )
        np.testing.assert_array_equal(
            refractive_index[INTERFACE_INDEX:, :],
            np.full(
                (
                    self.config.grid.nx - INTERFACE_INDEX,
                    self.config.grid.ny,
                ),
                RIGHT_REFRACTIVE_INDEX,
            ),
        )

    def test_geometry_order_is_correct(self) -> None:
        self.assertLess(SOURCE_X, UPSTREAM_MONITOR_X)
        self.assertLess(UPSTREAM_MONITOR_X, INTERFACE_INDEX)
        self.assertLess(INTERFACE_INDEX, DOWNSTREAM_MONITOR_X)

    def test_source_and_monitors_avoid_the_sponge(self) -> None:
        sponge_width = self.config.boundary.damping_width
        right_sponge_start = (
            self.config.grid.nx - sponge_width
        )
        top_sponge_start = (
            self.config.grid.ny - sponge_width
        )

        self.assertGreater(SOURCE_X, sponge_width)
        self.assertGreater(SOURCE_Y_START, sponge_width)
        self.assertLess(SOURCE_Y_STOP, top_sponge_start)

        self.assertLess(
            DOWNSTREAM_MONITOR_X,
            right_sponge_start,
        )
        self.assertGreater(MONITOR_Y_START, sponge_width)
        self.assertLess(MONITOR_Y_STOP, top_sponge_start)

    def test_analysis_window_contains_three_cycles(self) -> None:
        sample_count = (
            ANALYSIS_STOP_STEP - ANALYSIS_START_STEP
        )
        duration = sample_count * self.config.time.dt
        cycles = duration * self.config.source.frequency

        self.assertEqual(sample_count, 150)
        self.assertAlmostEqual(cycles, 3.0)

    def test_both_maps_satisfy_cfl(self) -> None:
        for name, material_map in (
            ("reference", self.reference_map),
            ("interface", self.interface_map),
        ):
            with self.subTest(name=name):
                maximum_speed = float(
                    np.max(material_map.wave_speed)
                )
                courant = compute_courant_number(
                    self.config,
                    maximum_speed,
                )
                self.assertLessEqual(courant, 1.0)


class InterfaceMeasurementPropagationTests(unittest.TestCase):
    """Verify separated harmonic interface responses."""

    @classmethod
    def setUpClass(cls) -> None:
        (
            cls.config,
            reference_map,
            interface_map,
        ) = create_scenario_pair()

        cls.reference = Wave2DSimulation(
            cls.config,
            material_map=reference_map,
        )
        cls.interface = Wave2DSimulation(
            cls.config,
            material_map=interface_map,
        )

        run_to_completion(cls.reference)
        run_to_completion(cls.interface)

        cls.response = analyze_scattering(
            cls.reference,
            cls.interface,
        )

    def test_histories_are_complete_and_finite(self) -> None:
        expected_length = self.config.time.steps + 1

        for simulation in (
            self.reference,
            self.interface,
        ):
            self.assertEqual(
                simulation.state.step_index,
                self.config.time.steps,
            )

            for state in simulation.monitor_states.values():
                self.assertEqual(
                    len(state.values),
                    expected_length,
                )
                self.assertTrue(
                    np.all(np.isfinite(state.values))
                )

    def test_incident_response_is_nonzero(self) -> None:
        self.assertGreater(
            abs(self.response.incident),
            1e-4,
        )

    def test_reflected_response_is_nonzero(self) -> None:
        self.assertGreater(
            abs(self.response.reflected),
            1e-4,
        )

    def test_transmitted_response_is_nonzero(self) -> None:
        self.assertGreater(
            abs(self.response.transmitted),
            1e-4,
        )

    def test_reflection_amplitude_is_physically_reasonable(self) -> None:
        measured = abs(
            self.response.reflection_amplitude
        )

        # Scalar-model prediction is |r| = 0.2.
        self.assertGreater(measured, 0.10)
        self.assertLess(measured, 0.35)

    def test_transmission_amplitude_is_physically_reasonable(self) -> None:
        measured = abs(
            self.response.transmission_amplitude
        )

        # The infinite-plane-wave scalar prediction is |t| = 0.8.
        # Finite-aperture diffraction and line averaging reduce the
        # measured value in this experiment.
        self.assertGreater(measured, 0.50)
        self.assertLess(measured, 1.00)

    def test_estimated_fluxes_are_finite_and_positive(self) -> None:
        reflectance = self.response.reflectance
        transmittance = self.response.transmittance
        measured_total = reflectance + transmittance

        self.assertTrue(np.isfinite(reflectance))
        self.assertTrue(np.isfinite(transmittance))
        self.assertTrue(np.isfinite(measured_total))

        self.assertGreater(reflectance, 0.0)
        self.assertGreater(transmittance, 0.0)

        # This finite-aperture line-monitor measurement does not
        # integrate the complete flux across the domain.
        self.assertLess(measured_total, 1.25)

    def test_analytical_scalar_coefficients_conserve_flux(self) -> None:
        n1 = 1.0
        n2 = RIGHT_REFRACTIVE_INDEX

        reflection = (n1 - n2) / (n1 + n2)
        transmission = 2.0 * n1 / (n1 + n2)

        reflectance = abs(reflection) ** 2
        transmittance = (
            n2 / n1 * abs(transmission) ** 2
        )

        self.assertAlmostEqual(reflection, -0.2)
        self.assertAlmostEqual(transmission, 0.8)
        self.assertAlmostEqual(reflectance, 0.04)
        self.assertAlmostEqual(transmittance, 0.96)
        self.assertAlmostEqual(
            reflectance + transmittance,
            1.0,
        )
