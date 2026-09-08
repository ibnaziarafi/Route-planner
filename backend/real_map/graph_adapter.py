"""Adapter from an OSMnx/NetworkX road graph to the project's graph contract."""

from math import hypot


class OSMGraphAdapter:
    def __init__(self, graph):
        self._graph = graph
        self._positions = {}
        self._adjacency = {str(node): {} for node in graph.nodes}

        for node, data in graph.nodes(data=True):
            node_id = str(node)
            self._positions[node_id] = {
                "lat": float(data["y"]),
                "lon": float(data["x"]),
                "x": float(data["x"]),
                "y": float(data["y"]),
            }

        for source, target, data in graph.edges(data=True):
            source_id = str(source)
            target_id = str(target)
            length = float(data.get("length", 1.0))
            current = self._adjacency[source_id].get(target_id)
            if current is None or length < current:
                self._adjacency[source_id][target_id] = length

    def has_node(self, node: str) -> bool:
        return str(node) in self._adjacency

    def get_nodes(self) -> list[str]:
        return sorted(self._adjacency)

    def get_neighbors(self, node: str) -> list[tuple[str, float]]:
        return list(self._adjacency.get(str(node), {}).items())

    def nearest_node(self, lat: float, lon: float) -> str | None:
        if not self._positions:
            return None
        latitudes = [position["lat"] for position in self._positions.values()]
        longitudes = [position["lon"] for position in self._positions.values()]
        margin = 0.01
        if not (
            min(latitudes) - margin <= lat <= max(latitudes) + margin
            and min(longitudes) - margin <= lon <= max(longitudes) + margin
        ):
            return None
        return min(
            self._positions,
            key=lambda node: hypot(
                self._positions[node]["lat"] - lat,
                self._positions[node]["lon"] - lon,
            ),
        )

    def coordinates(self, node: str) -> dict[str, float]:
        return self._positions[str(node)]

    @property
    def positions(self) -> dict[str, dict[str, float]]:
        return self._positions
