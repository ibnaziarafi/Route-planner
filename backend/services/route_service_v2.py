from backend.graph.graph_data import create_default_graph, NODE_POSITIONS
from backend.algorithms.dijkstra_v2 import dijkstra_v2
from backend.algorithms.astar import astar
from backend.structures.linked_list import RouteLinkedList


class RouteServiceV2:
    def __init__(self):
        self.graph = create_default_graph()
        self.positions = NODE_POSITIONS

    def calculate_single_route_v2(self, start: str, destination: str) -> dict:
        """
        Calculates shortest path using Dijkstra V2 (MinHeap).
        Stores path nodes in RouteLinkedList.
        """
        path_list, distance = dijkstra_v2(self.graph, start, destination)

        linked_list = RouteLinkedList()
        for node in path_list:
            linked_list.append(node)

        return {
            "path": linked_list.get_all(),
            "distance": round(distance, 2) if distance != float('inf') else float('inf'),
            "algorithm": "Dijkstra V2 (MinHeap)",
        }

    def calculate_single_route_astar(self, start: str, destination: str) -> dict:
        """
        Calculates shortest path using A* pathfinding (Geographic Heuristic).
        Stores path nodes in RouteLinkedList.
        """
        path_list, distance = astar(self.graph, start, destination, self.positions)

        linked_list = RouteLinkedList()
        for node in path_list:
            linked_list.append(node)

        return {
            "path": linked_list.get_all(),
            "distance": round(distance, 2) if distance != float('inf') else float('inf'),
            "algorithm": "A* (Geographic Heuristic)",
        }
