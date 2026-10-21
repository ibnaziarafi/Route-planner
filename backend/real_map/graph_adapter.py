"""Adapter from an OSMnx/NetworkX road graph to the project's graph contract."""

from math import isfinite, radians, sin, cos, asin, sqrt


class OSMGraphAdapter:
    def __init__(self, graph, max_snap_distance_m: float = 500.0):
        self._graph = graph
        self.max_snap_distance_m = max_snap_distance_m
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
            if "length" not in data:
                raise ValueError(f"Road edge {source_id}->{target_id} has no length in metres.")
            length = float(data["length"])
            if not isfinite(length) or length < 0:
                raise ValueError(f"Road edge {source_id}->{target_id} has an invalid length.")
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
        if not self._positions: return None
        lat1=radians(lat); lon1=radians(lon)
        def metres(position):
            lat2=radians(position["lat"]); lon2=radians(position["lon"])
            dlat=lat2-lat1; dlon=lon2-lon1
            h=sin(dlat/2)**2+cos(lat1)*cos(lat2)*sin(dlon/2)**2
            return 6_371_000*2*asin(min(1.0,sqrt(h)))
        closest=min(self._positions,key=lambda node:metres(self._positions[node]))
        return closest if metres(self._positions[closest]) <= self.max_snap_distance_m else None

    def coordinates(self, node: str) -> dict[str, float]:
        return self._positions[str(node)]

    @property
    def positions(self) -> dict[str, dict[str, float]]:
        return self._positions
