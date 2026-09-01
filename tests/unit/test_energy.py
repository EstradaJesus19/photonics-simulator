"""Tests for leapfrog-consistent scalar-wave energy."""

from dataclasses import replace
import unittest

import numpy as np

from wavesim.config import GridConfig, create_default_config
from wavesim.materials import (
    create_rectangular_material_map,
    create_uniform_material_map,
)
from wavesim.solver import (
    Wave2DSimulation,
    compute_energy,
    compute_energy_density,
    compute_energy_flux,
    step_wave,
)


class LeapfrogEnergyCalculationTest(unittest.TestCase):
    """Verify the terms in the half-step energy invariant."""

    def setUp(self) -> None:
        base = create_default_config()
        self.grid = GridConfig(
            nx=4,
            ny=3,
            dx=2.0,
            dy=0.5,
        )
        self.config = replace(
            base,
            grid=self.grid,
            initial_condition=replace(
                base.initial_condition,
                x0=2,
                y0=1,
            ),
            source=replace(
                base.source,
                kind="none",
                x=2,
                y=1,
            ),
            boundary=replace(base.boundary, kind="fixed"),
        )
        self.material_map = create_uniform_material_map(
            self.grid,
            self.config.material,
        )

    def test_zero_fields_have_zero_energy(self) -> None:
        field = np.zeros(self.grid.shape)

        energy = compute_energy(
            field,
            field,
            self.config,
            self.material_map,
        )

        self.assertEqual(energy, 0.0)

    def test_uniform_change_has_only_kinetic_energy(self) -> None:
        previous = np.zeros(self.grid.shape)
        current = np.full(self.grid.shape, 3.0)

        energy = compute_energy(
            previous,
            current,
            self.config,
            self.material_map,
        )

        velocity = 3.0 / self.config.time.dt
        expected = (
            0.5
            * velocity**2
            * self.grid.nx
            * self.grid.ny
            * self.grid.dx
            * self.grid.dy
        )
        self.assertAlmostEqual(energy, expected)

    def test_cross_time_face_gradients_set_potential_energy(
        self,
    ) -> None:
        x = np.arange(self.grid.nx)[:, np.newaxis]
        y = np.arange(self.grid.ny)[np.newaxis, :]
        previous = 2.0 * x + 3.0 * y
        current = previous.copy()

        energy = compute_energy(
            previous,
            current,
            self.config,
            self.material_map,
        )

        gradient_x = 2.0 / self.grid.dx
        gradient_y = 3.0 / self.grid.dy
        expected_x = (
            0.5
            * gradient_x**2
            * (self.grid.nx - 1)
            * self.grid.ny
            * self.grid.dx
            * self.grid.dy
        )
        expected_y = (
            0.5
            * gradient_y**2
            * self.grid.nx
            * (self.grid.ny - 1)
            * self.grid.dx
            * self.grid.dy
        )
        self.assertAlmostEqual(energy, expected_x + expected_y)

    def test_material_speed_affects_only_kinetic_term(self) -> None:
        slow_material = replace(
            self.config.material,
            background_refractive_index=2.0,
        )
        slow_config = replace(self.config, material=slow_material)
        slow_map = create_uniform_material_map(
            self.grid,
            slow_material,
        )
        previous = np.zeros(self.grid.shape)
        current = np.ones(self.grid.shape)

        reference_energy = compute_energy(
            previous,
            current,
            self.config,
            self.material_map,
        )
        slow_energy = compute_energy(
            previous,
            current,
            slow_config,
            slow_map,
        )

        self.assertAlmostEqual(slow_energy, 4.0 * reference_energy)

    def test_energy_density_integrates_to_total_energy(self) -> None:
        x = np.arange(self.grid.nx)[:, np.newaxis]
        y = np.arange(self.grid.ny)[np.newaxis, :]

        previous = x + 2.0 * y
        current = 1.5 * x - y

        energy_density = compute_energy_density(
            previous,
            current,
            self.config,
            self.material_map,
        )

        total_energy = compute_energy(
            previous,
            current,
            self.config,
            self.material_map,
        )

        integrated_density = float(
            np.sum(energy_density)
            * self.grid.dx
            * self.grid.dy
        )

        self.assertEqual(
            energy_density.shape,
            self.grid.shape,
        )
        self.assertAlmostEqual(
            integrated_density,
            total_energy,
        )


class LeapfrogEnergyConservationTest(unittest.TestCase):
    """Verify the invariant across a nonuniform fixed-boundary run."""

    def test_source_free_composite_run_conserves_energy(self) -> None:
        base = create_default_config()
        grid = GridConfig(nx=61, ny=51, dx=1.0, dy=1.25)
        config = replace(
            base,
            grid=grid,
            time=replace(base.time, dt=0.35, steps=250),
            initial_condition=replace(
                base.initial_condition,
                kind="gaussian",
                x0=18,
                y0=25,
                sigma=5.0,
            ),
            source=replace(
                base.source,
                kind="none",
                x=18,
                y=25,
            ),
            boundary=replace(base.boundary, kind="fixed"),
        )
        material_map = create_rectangular_material_map(
            grid,
            config.material,
            x_start=27,
            x_stop=46,
            y_start=12,
            y_stop=39,
            rectangle_refractive_index=1.7,
        )
        simulation = Wave2DSimulation(
            config,
            material_map=material_map,
        )
        initial_energy = simulation.initial_energy

        for _ in range(config.time.steps):
            simulation.advance()

        energy_history = np.asarray(simulation.state.energy_history)
        relative_error = np.abs(
            (energy_history - initial_energy) / initial_energy
        )

        self.assertTrue(np.all(np.isfinite(energy_history)))
        self.assertLess(float(np.max(relative_error)), 1e-12)

    def test_interior_control_volume_obeys_local_balance(
        self,
    ) -> None:
        base = create_default_config()
        grid = GridConfig(
            nx=61,
            ny=51,
            dx=1.0,
            dy=1.25,
        )
        config = replace(
            base,
            grid=grid,
            time=replace(
                base.time,
                dt=0.35,
                steps=20,
            ),
            initial_condition=replace(
                base.initial_condition,
                kind="gaussian",
                x0=25,
                y0=25,
                sigma=5.0,
            ),
            source=replace(
                base.source,
                kind="none",
                x=25,
                y=25,
            ),
            boundary=replace(
                base.boundary,
                kind="fixed",
            ),
        )
        material_map = create_rectangular_material_map(
            grid,
            config.material,
            x_start=27,
            x_stop=46,
            y_start=12,
            y_stop=39,
            rectangle_refractive_index=1.7,
        )
        simulation = Wave2DSimulation(
            config,
            material_map=material_map,
        )

        # Move away from the time-symmetric initial instant so the
        # selected control volume has nonzero transported power.
        for _ in range(12):
            simulation.advance()

        previous = simulation.state.previous
        current = simulation.state.current

        next_field = step_wave(
            previous,
            current,
            config,
            material_map,
            simulation.damping_profile,
        )

        previous_density = compute_energy_density(
            previous,
            current,
            config,
            material_map,
        )
        next_density = compute_energy_density(
            current,
            next_field,
            config,
            material_map,
        )
        flux_x, flux_y = compute_energy_flux(
            previous,
            current,
            next_field,
            config,
        )

        i_start = 18
        i_stop = 36
        j_start = 17
        j_stop = 34

        energy_change_rate = float(
            np.sum(
                next_density[
                    i_start:i_stop,
                    j_start:j_stop,
                ]
                - previous_density[
                    i_start:i_stop,
                    j_start:j_stop,
                ]
            )
            * grid.dx
            * grid.dy
            / config.time.dt
        )

        right_power = float(
            np.sum(
                flux_x[
                    i_stop - 1,
                    j_start:j_stop,
                ]
            )
            * grid.dy
        )
        left_power = float(
            -np.sum(
                flux_x[
                    i_start - 1,
                    j_start:j_stop,
                ]
            )
            * grid.dy
        )
        top_power = float(
            np.sum(
                flux_y[
                    i_start:i_stop,
                    j_stop - 1,
                ]
            )
            * grid.dx
        )
        bottom_power = float(
            -np.sum(
                flux_y[
                    i_start:i_stop,
                    j_start - 1,
                ]
            )
            * grid.dx
        )

        outward_power = (
            right_power
            + left_power
            + top_power
            + bottom_power
        )

        residual = energy_change_rate + outward_power
        scale = max(
            abs(energy_change_rate),
            abs(outward_power),
            1.0,
        )

        self.assertLess(
            abs(residual) / scale,
            1e-12,
        )


class EnergyFluxCalculationTest(unittest.TestCase):
    """Verify face placement, scaling, and flux direction."""

    def setUp(self) -> None:
        base = create_default_config()
        self.grid = GridConfig(
            nx=6,
            ny=5,
            dx=2.0,
            dy=0.5,
        )
        self.config = replace(
            base,
            grid=self.grid,
            initial_condition=replace(
                base.initial_condition,
                x0=3,
                y0=2,
            ),
            source=replace(
                base.source,
                kind="none",
                x=3,
                y=2,
            ),
            boundary=replace(
                base.boundary,
                kind="fixed",
            ),
        )

    def test_zero_fields_have_zero_flux(self) -> None:
        field = np.zeros(self.grid.shape)

        flux_x, flux_y = compute_energy_flux(
            field,
            field,
            field,
            self.config,
        )

        self.assertEqual(
            flux_x.shape,
            (self.grid.nx - 1, self.grid.ny),
        )
        self.assertEqual(
            flux_y.shape,
            (self.grid.nx, self.grid.ny - 1),
        )
        np.testing.assert_array_equal(
            flux_x,
            np.zeros_like(flux_x),
        )
        np.testing.assert_array_equal(
            flux_y,
            np.zeros_like(flux_y),
        )

    def test_right_traveling_pattern_has_positive_x_flux(
        self,
    ) -> None:
        x = (
            np.arange(self.grid.nx)[:, np.newaxis]
            * self.grid.dx
        )
        current = np.broadcast_to(
            x,
            self.grid.shape,
        ).copy()

        previous = current + self.config.time.dt
        next_field = current - self.config.time.dt

        flux_x, flux_y = compute_energy_flux(
            previous,
            current,
            next_field,
            self.config,
        )

        np.testing.assert_allclose(flux_x, 1.0)
        np.testing.assert_allclose(flux_y, 0.0)

    def test_left_traveling_pattern_has_negative_x_flux(
        self,
    ) -> None:
        x = (
            np.arange(self.grid.nx)[:, np.newaxis]
            * self.grid.dx
        )
        current = np.broadcast_to(
            x,
            self.grid.shape,
        ).copy()

        previous = current - self.config.time.dt
        next_field = current + self.config.time.dt

        flux_x, flux_y = compute_energy_flux(
            previous,
            current,
            next_field,
            self.config,
        )

        np.testing.assert_allclose(flux_x, -1.0)
        np.testing.assert_allclose(flux_y, 0.0)

    def test_upward_pattern_has_positive_y_flux(
        self,
    ) -> None:
        y = (
            np.arange(self.grid.ny)[np.newaxis, :]
            * self.grid.dy
        )
        current = np.broadcast_to(
            y,
            self.grid.shape,
        ).copy()

        previous = current + self.config.time.dt
        next_field = current - self.config.time.dt

        flux_x, flux_y = compute_energy_flux(
            previous,
            current,
            next_field,
            self.config,
        )

        np.testing.assert_allclose(flux_x, 0.0)
        np.testing.assert_allclose(flux_y, 1.0)


if __name__ == "__main__":
    unittest.main()
