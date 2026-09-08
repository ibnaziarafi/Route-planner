"""Real-road distance matrix built with one single-source run per node."""

from backend.pdp.distance_matrix import DistanceMatrix


class RealMapDistanceMatrix(DistanceMatrix):
    """Named adapter documenting that weights are real road metres."""

    pass
