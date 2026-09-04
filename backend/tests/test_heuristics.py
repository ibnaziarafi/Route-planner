import math
from backend.algorithms.heuristics import euclidean_distance


def test_euclidean_distance_dict_positions():
    positions = {
        "A": {"x": 100, "y": 100},
        "B": {"x": 100, "y": 600},
    }
    # Unscaled (scale_factor=1.0)
    dist = euclidean_distance("A", "B", positions, scale_factor=1.0)
    assert dist == 500.0

    # Default scaled (scale_factor=250.0)
    dist_scaled = euclidean_distance("A", "B", positions)
    assert dist_scaled == 2.0


def test_euclidean_distance_tuple_positions():
    positions = {
        "P1": (0, 0),
        "P2": (300, 400),
    }
    dist = euclidean_distance("P1", "P2", positions, scale_factor=1.0)
    assert math.isclose(dist, 500.0)

    dist_scaled = euclidean_distance("P1", "P2", positions, scale_factor=250.0)
    assert math.isclose(dist_scaled, 2.0)


def test_euclidean_distance_missing_nodes():
    positions = {
        "A": {"x": 100, "y": 100},
    }
    assert euclidean_distance("A", "NON_EXISTENT", positions) == 0.0
    assert euclidean_distance("MISSING_1", "MISSING_2", positions) == 0.0
