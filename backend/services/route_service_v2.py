from backend.graph.graph_data import get_graph_and_positions
from backend.algorithms.dijkstra_v2 import dijkstra_v2
from backend.algorithms.astar import astar
from backend.structures.linked_list import RouteLinkedList


class RouteServiceV2:
    def calculate_single_route_v2(self, start: str, destination: str, graph_type: str = "small") -> dict:
        """
        Calculates shortest path using Dijkstra V2 (MinHeap).
        Stores path nodes in RouteLinkedList.
        """
        graph, _ = get_graph_and_positions(graph_type)
        path_list, distance = dijkstra_v2(graph, start, destination)

        linked_list = RouteLinkedList()
        for node in path_list:
            linked_list.append(node)

        return {
            "path": linked_list.get_all(),
            "distance": round(distance, 2) if distance != float('inf') else float('inf'),
            "algorithm": "Dijkstra V2 (MinHeap)",
        }

    def calculate_single_route_astar(self, start: str, destination: str, graph_type: str = "small") -> dict:
        """
        Calculates shortest path using A* pathfinding (Geographic Heuristic).
        Stores path nodes in RouteLinkedList.
        """
        graph, positions = get_graph_and_positions(graph_type)
        path_list, distance = astar(graph, start, destination, positions)

        linked_list = RouteLinkedList()
        for node in path_list:
            linked_list.append(node)

        return {
            "path": linked_list.get_all(),
            "distance": round(distance, 2) if distance != float('inf') else float('inf'),
            "algorithm": "A* (Geographic Heuristic)",
        }
