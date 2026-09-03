from backend.graph.graph_data import create_default_graph, NODE_POSITIONS
from backend.algorithms.dijkstra import dijkstra
from backend.structures.linked_list import RouteLinkedList

class RouteService:
    def __init__(self):
        self.graph = create_default_graph()
        self.positions = NODE_POSITIONS

    def get_graph_data(self) -> dict:
        """Returns nodes, edges with weights, and visual positions of the default graph."""
        return {
            "nodes": self.graph.get_nodes(),
            "edges": self.graph.get_edges(),
            "positions": self.positions,
        }

    def calculate_single_route(self, start: str, destination: str) -> dict:
        """
        Calculates shortest path from start to destination.
        Stores the resulting path in a RouteLinkedList.
        """
        path_list, distance = dijkstra(self.graph, start, destination)
        
        linked_list = RouteLinkedList()
        for node in path_list:
            linked_list.append(node)

        return {
            "path": linked_list.get_all(),
            "distance": round(distance, 2) if distance != float('inf') else float('inf')
        }

    def calculate_multi_stop_route(self, start: str, stops: list[str], destination: str) -> dict:
        """
        Calculates the route connecting start -> stop_1 -> ... -> stop_N -> destination.
        Each segment is calculated independently using Dijkstra, and merged into a RouteLinkedList.
        """
        points = [start] + [s for s in stops if s.strip()] + [destination]
        
        linked_list = RouteLinkedList()
        total_distance = 0.0

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            segment_path, segment_dist = dijkstra(self.graph, p1, p2)
            
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
