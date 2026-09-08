"""Real-map routing service using the existing project algorithms."""

from math import isfinite

from backend.algorithms.astar import astar
from backend.algorithms.dijkstra import dijkstra
from backend.algorithms.dijkstra_v2 import dijkstra_v2
from backend.real_map.osm_graph import get_hobart_adapter


def calculate_real_map_route(request, graph=None) -> dict:
    coordinates = (request.start_lat, request.start_lon, request.end_lat, request.end_lon)
    if not all(isfinite(value) for value in coordinates):
        raise ValueError("Coordinates must be finite numbers.")

    adapter = graph or get_hobart_adapter()
    start_node = adapter.nearest_node(request.start_lat, request.start_lon)
    end_node = adapter.nearest_node(request.end_lat, request.end_lon)
    if start_node is None or end_node is None:
        raise ValueError("No road nodes are available for the requested locations.")

    if request.algorithm == "dijkstra":
        path, distance = dijkstra(adapter, start_node, end_node)
    elif request.algorithm == "dijkstra_v2":
        path, distance = dijkstra_v2(adapter, start_node, end_node)
    elif request.algorithm == "a_star":
        path, distance = astar(adapter, start_node, end_node, adapter.positions)
    else:
        raise ValueError("Unsupported algorithm. Use dijkstra, dijkstra_v2, or a_star.")

    if not path or distance == float("inf"):
        raise ValueError("No route found between the selected locations.")

    return {
        "algorithm": request.algorithm,
        "distance": round(distance, 2),
        "start_node": start_node,
        "end_node": end_node,
        "path": [
            {
                "node": node,
                "lat": round(adapter.coordinates(node)["lat"], 7),
                "lon": round(adapter.coordinates(node)["lon"], 7),
            }
            for node in path
        ],
    }
