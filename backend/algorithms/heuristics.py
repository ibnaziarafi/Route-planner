import math
from typing import Any


def euclidean_distance(
    node1: str,
    node2: str,
    positions: dict[str, Any],
    scale_factor: float = 250.0
) -> float:
    """
    Calculates the Euclidean distance heuristic between node1 and node2
    using their 2D visual positions.

    `positions` can format node coordinates as either:
    - dict: {"x": 100, "y": 100}
    - tuple / list: (100, 100) or [100, 100]

    `scale_factor` converts canvas pixel coordinates to graph distance scale
    so the heuristic remains admissible (h(n) <= true distance).

    Returns 0.0 if position data is missing for either node.
    """
    if node1 not in positions or node2 not in positions:
        return 0.0

    pos1 = positions[node1]
    pos2 = positions[node2]

    # Extract x, y for node 1
    if isinstance(pos1, dict):
        x1, y1 = pos1.get("x", 0.0), pos1.get("y", 0.0)
    elif isinstance(pos1, (tuple, list)) and len(pos1) >= 2:
        x1, y1 = pos1[0], pos1[1]
    else:
        return 0.0

    # Extract x, y for node 2
    if isinstance(pos2, dict):
        x2, y2 = pos2.get("x", 0.0), pos2.get("y", 0.0)
    elif isinstance(pos2, (tuple, list)) and len(pos2) >= 2:
        x2, y2 = pos2[0], pos2[1]
    else:
        return 0.0

    # Calculate raw Euclidean distance formula sqrt((x2-x1)^2 + (y2-y1)^2)
    raw_dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    # Scale down raw pixel distance to ensure heuristic admissibility
    return raw_dist / scale_factor if scale_factor > 0 else raw_dist
