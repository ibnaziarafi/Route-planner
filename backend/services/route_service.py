from backend.graph.graph_data import get_graph_and_positions
from backend.algorithms.dijkstra import dijkstra
from backend.structures.linked_list import RouteLinkedList


class RouteService:
    def get_graph_data(self, graph_type: str = "small") -> dict:
        """Returns nodes, edges with weights, and visual positions for specified graph type."""
        graph, positions = get_graph_and_positions(graph_type)
        return {
            "nodes": graph.get_nodes(),
            "edges": graph.get_edges(),
            "positions": positions,
        }

    def calculate_single_route(self, start: str, destination: str, graph_type: str = "small") -> dict:
        """
        Calculates shortest path from start to destination using Phase 1 Dijkstra V1.
        Stores the resulting path in a RouteLinkedList.
        """
        graph, _ = get_graph_and_positions(graph_type)
        path_list, distance = dijkstra(graph, start, destination)

        linked_list = RouteLinkedList()
        for node in path_list:
            linked_list.append(node)

        return {
            "path": linked_list.get_all(),
            "distance": round(distance, 2) if distance != float('inf') else float('inf')
        }

    def calculate_multi_stop_route(self, start: str, stops: list[str], destination: str, graph_type: str = "small") -> dict:
        """
        Calculates the route connecting start -> stop_1 -> ... -> stop_N -> destination.
        Each segment is calculated independently using Dijkstra, and merged into a RouteLinkedList.
        """
        graph, _ = get_graph_and_positions(graph_type)
        points = [start] + [s for s in stops if s.strip()] + [destination]

        linked_list = RouteLinkedList()
        total_distance = 0.0

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            segment_path, segment_dist = dijkstra(graph, p1, p2)

            if segment_dist == float('inf'):
                return {
                    "route": [],
                    "distance": float('inf'),
                    "error": f"No path found between {p1} and {p2}"
                }

            linked_list.extend_segment(segment_path)
            total_distance += segment_dist

        return {
            "route": linked_list.get_all(),
            "distance": round(total_distance, 2)
        }
