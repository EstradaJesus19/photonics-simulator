"""Shared geometry conventions for material-map construction."""

import numpy as np

from .config import GridConfig

from numbers import Real

from collections.abc import Sequence


def create_grid_coordinate_arrays(
    grid: GridConfig,
) -> tuple[np.ndarray, np.ndarray]:
    """Return physical coordinates for every grid sample.

    Array axis 0 is x and axis 1 is y. Sample ``(i, j)`` is located at
    ``(i * dx, j * dy)``. The returned arrays both have ``grid.shape`` and
    use NumPy's ``ij`` indexing convention.
    """
    x = np.arange(grid.nx, dtype=float) * grid.dx
    y = np.arange(grid.ny, dtype=float) * grid.dy
    return np.meshgrid(x, y, indexing="ij")


def validate_geometry_mask(
    mask: np.ndarray,
    grid: GridConfig,
) -> None:
    """Validate a boolean mask aligned with the simulation grid."""
    if not isinstance(mask, np.ndarray):
        raise TypeError("Geometry mask must be a NumPy array.")

    if mask.shape != grid.shape:
        raise ValueError(
            "Geometry mask must have shape "
            f"{grid.shape}, received {mask.shape}."
        )

    if not np.issubdtype(mask.dtype, np.bool_):
        raise TypeError("Geometry mask must have boolean dtype.")

    if not np.any(mask):
        raise ValueError("Geometry mask must select at least one grid sample.")


def _validate_finite_geometry_value(
    name: str,
    value: float,
) -> None:
    """Validate one finite real geometry parameter."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real scalar.")

    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite.")


def _validate_positive_geometry_value(
    name: str,
    value: float,
) -> None:
    """Validate one finite, positive geometry parameter."""
    _validate_finite_geometry_value(name, value)

    if value <= 0:
        raise ValueError(f"{name} must be positive.")


def create_elliptical_mask(
    grid: GridConfig,
    *,
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    angle_degrees: float = 0.0,
) -> np.ndarray:
    """Create a filled, possibly rotated elliptical geometry mask.

    The radii are measured along the ellipse's local axes. A positive angle
    rotates the ellipse counterclockwise in physical coordinates.
    """
    _validate_finite_geometry_value("center_x", center_x)
    _validate_finite_geometry_value("center_y", center_y)
    _validate_positive_geometry_value("radius_x", radius_x)
    _validate_positive_geometry_value("radius_y", radius_y)
    _validate_finite_geometry_value(
        "angle_degrees",
        angle_degrees,
    )

    x, y = create_grid_coordinate_arrays(grid)

    local_x, local_y = _rotate_coordinates_into_local_frame(
        x,
        y,
        center_x=center_x,
        center_y=center_y,
        angle_degrees=angle_degrees,
    )

    normalized_distance_squared = (
        (local_x / radius_x) ** 2
        + (local_y / radius_y) ** 2
    )

    mask = normalized_distance_squared <= 1.0
    validate_geometry_mask(mask, grid)
    return mask


def create_circular_mask(
    grid: GridConfig,
    *,
    center_x: float,
    center_y: float,
    radius: float,
) -> np.ndarray:
    """Create a filled circular geometry mask in physical coordinates."""
    return create_elliptical_mask(
        grid,
        center_x=center_x,
        center_y=center_y,
        radius_x=radius,
        radius_y=radius,
    )


def create_rectangular_mask(
    grid: GridConfig,
    *,
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    angle_degrees: float = 0.0,
) -> np.ndarray:
    """Create a filled, possibly rotated physical rectangle mask.

    Width and height are measured along the rectangle's local x and y axes.
    Samples on the analytical rectangle boundary are included.
    """
    _validate_finite_geometry_value("center_x", center_x)
    _validate_finite_geometry_value("center_y", center_y)
    _validate_positive_geometry_value("width", width)
    _validate_positive_geometry_value("height", height)
    _validate_finite_geometry_value(
        "angle_degrees",
        angle_degrees,
    )

    x, y = create_grid_coordinate_arrays(grid)

    local_x, local_y = _rotate_coordinates_into_local_frame(
        x,
        y,
        center_x=center_x,
        center_y=center_y,
        angle_degrees=angle_degrees,
    )

    mask = (
        (np.abs(local_x) <= width / 2.0)
        & (np.abs(local_y) <= height / 2.0)
    )

    validate_geometry_mask(mask, grid)
    return mask


def _rotate_coordinates_into_local_frame(
    x: np.ndarray,
    y: np.ndarray,
    *,
    center_x: float,
    center_y: float,
    angle_degrees: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Express global coordinates in a rotated shape's local frame."""
    angle_radians = np.deg2rad(angle_degrees)
    cosine = np.cos(angle_radians)
    sine = np.sin(angle_radians)

    displaced_x = x - center_x
    displaced_y = y - center_y

    local_x = (
        cosine * displaced_x
        + sine * displaced_y
    )
    local_y = (
        -sine * displaced_x
        + cosine * displaced_y
    )

    return local_x, local_y


def _polygon_signed_area(vertices: np.ndarray) -> float:
    """Return twice the polygon's signed area."""
    x = vertices[:, 0]
    y = vertices[:, 1]

    return float(
        np.sum(
            x * np.roll(y, -1)
            - np.roll(x, -1) * y
        )
    )


def _orientation(
    first: np.ndarray,
    second: np.ndarray,
    third: np.ndarray,
) -> float:
    """Return the signed orientation of three points."""
    return float(
        (second[0] - first[0])
        * (third[1] - first[1])
        - (second[1] - first[1])
        * (third[0] - first[0])
    )


def _point_lies_on_segment(
    point: np.ndarray,
    start: np.ndarray,
    stop: np.ndarray,
) -> bool:
    """Return whether a point lies on a closed line segment."""
    if _orientation(start, stop, point) != 0.0:
        return False

    return (
        min(start[0], stop[0])
        <= point[0]
        <= max(start[0], stop[0])
        and min(start[1], stop[1])
        <= point[1]
        <= max(start[1], stop[1])
    )


def _segments_intersect(
    first_start: np.ndarray,
    first_stop: np.ndarray,
    second_start: np.ndarray,
    second_stop: np.ndarray,
) -> bool:
    """Return whether two closed line segments intersect."""
    orientation_1 = _orientation(
        first_start,
        first_stop,
        second_start,
    )
    orientation_2 = _orientation(
        first_start,
        first_stop,
        second_stop,
    )
    orientation_3 = _orientation(
        second_start,
        second_stop,
        first_start,
    )
    orientation_4 = _orientation(
        second_start,
        second_stop,
        first_stop,
    )

    if (
        orientation_1 * orientation_2 < 0.0
        and orientation_3 * orientation_4 < 0.0
    ):
        return True

    if (
        orientation_1 == 0.0
        and _point_lies_on_segment(
            second_start,
            first_start,
            first_stop,
        )
    ):
        return True

    if (
        orientation_2 == 0.0
        and _point_lies_on_segment(
            second_stop,
            first_start,
            first_stop,
        )
    ):
        return True

    if (
        orientation_3 == 0.0
        and _point_lies_on_segment(
            first_start,
            second_start,
            second_stop,
        )
    ):
        return True

    if (
        orientation_4 == 0.0
        and _point_lies_on_segment(
            first_stop,
            second_start,
            second_stop,
        )
    ):
        return True

    return False


def _validate_simple_polygon(
    vertices: np.ndarray,
) -> None:
    """Validate ordered vertices defining one simple polygon."""
    if vertices.ndim != 2 or vertices.shape[1] != 2:
        raise ValueError(
            "Polygon vertices must have shape (number_of_vertices, 2)."
        )

    if vertices.shape[0] < 3:
        raise ValueError(
            "Polygon must contain at least three vertices."
        )

    if not np.all(np.isfinite(vertices)):
        raise ValueError(
            "Polygon vertices must contain only finite values."
        )

    unique_vertices = np.unique(vertices, axis=0)

    if unique_vertices.shape[0] != vertices.shape[0]:
        raise ValueError(
            "Polygon vertices must not contain duplicates."
        )

    edge_count = vertices.shape[0]

    for first_edge in range(edge_count):
        first_start = vertices[first_edge]
        first_stop = vertices[
            (first_edge + 1) % edge_count
        ]

        for second_edge in range(
            first_edge + 1,
            edge_count,
        ):
            edges_are_adjacent = (
                second_edge == first_edge + 1
                or (
                    first_edge == 0
                    and second_edge == edge_count - 1
                )
            )

            if edges_are_adjacent:
                continue

            second_start = vertices[second_edge]
            second_stop = vertices[
                (second_edge + 1) % edge_count
            ]

            if _segments_intersect(
                first_start,
                first_stop,
                second_start,
                second_stop,
            ):
                raise ValueError(
                    "Polygon must not self-intersect."
                )

    if _polygon_signed_area(vertices) == 0.0:
        raise ValueError(
            "Polygon vertices must enclose a nonzero area."
        )


def _points_on_polygon_boundary(
    x: np.ndarray,
    y: np.ndarray,
    vertices: np.ndarray,
) -> np.ndarray:
    """Return a mask selecting samples on the polygon boundary."""
    boundary = np.zeros(x.shape, dtype=bool)

    for index in range(vertices.shape[0]):
        start = vertices[index]
        stop = vertices[
            (index + 1) % vertices.shape[0]
        ]

        edge_x = stop[0] - start[0]
        edge_y = stop[1] - start[1]

        relative_x = x - start[0]
        relative_y = y - start[1]

        cross_product = (
            edge_x * relative_y
            - edge_y * relative_x
        )

        within_x_bounds = (
            (x >= min(start[0], stop[0]))
            & (x <= max(start[0], stop[0]))
        )
        within_y_bounds = (
            (y >= min(start[1], stop[1]))
            & (y <= max(start[1], stop[1]))
        )

        boundary |= (
            (cross_product == 0.0)
            & within_x_bounds
            & within_y_bounds
        )

    return boundary


def create_polygon_mask(
    grid: GridConfig,
    *,
    vertices: Sequence[tuple[float, float]],
) -> np.ndarray:
    """Create a filled mask from ordered simple-polygon vertices.

    Vertices use physical coordinates. Clockwise and counterclockwise ordering
    are both supported. Samples on polygon edges and vertices are included.
    Concave polygons are supported, but self-intersecting polygons are rejected.
    """
    try:
        vertex_array = np.asarray(
            vertices,
            dtype=float,
        )
    except (TypeError, ValueError) as error:
        raise TypeError(
            "Polygon vertices must be real coordinate pairs."
        ) from error

    _validate_simple_polygon(vertex_array)

    x, y = create_grid_coordinate_arrays(grid)

    inside = np.zeros(grid.shape, dtype=bool)

    for index in range(vertex_array.shape[0]):
        start = vertex_array[index]
        stop = vertex_array[
            (index + 1) % vertex_array.shape[0]
        ]

        edge_straddles_y = (
            (start[1] > y) != (stop[1] > y)
        )

        intersection_x = np.zeros(
            grid.shape,
            dtype=float,
        )

        np.divide(
            (stop[0] - start[0])
            * (y - start[1]),
            stop[1] - start[1],
            out=intersection_x,
            where=edge_straddles_y,
        )

        intersection_x += start[0]

        ray_crosses_edge = (
            edge_straddles_y
            & (x < intersection_x)
        )

        inside ^= ray_crosses_edge

    boundary = _points_on_polygon_boundary(
        x,
        y,
        vertex_array,
    )

    mask = inside | boundary
    validate_geometry_mask(mask, grid)
    return mask