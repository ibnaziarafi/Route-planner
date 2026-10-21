"""
Service wrapper bridging PDP solver with graph data and road navigation paths.
"""

from backend.graph.graph_data import get_graph_and_positions
from backend.algorithms.dijkstra_v2 import dijkstra_v2
from backend.pdp.models import Driver, Order, Solution, StopType
from backend.pdp.distance_matrix import DistanceMatrix
from backend.pdp.scratch_solver import solve as scratch_solve
from backend.pdp.ortools_solver import solve as ortools_solve
from backend.pdp.pyvrp_solver import solve as pyvrp_solve


class PDPService:
    def __init__(self, graph_type: str = "medium"):
        self.graph_type = graph_type
        self.graph, self.positions = get_graph_and_positions(graph_type)

    def solve_pdp(
        self,
        drivers: list[Driver],
        orders: list[Order],
        algorithm: str = "scratch",
        time_limit_seconds: int = 5,
        mode: str = "save", economics=None, timing=None,
    ) -> dict:
        """
        Solves the PDP routing problem for given drivers and orders.
        Returns solution routes, unassigned orders, total distance, and detailed paths for visual rendering.
        """
        # Collect all relevant nodes
        relevant_nodes = sorted(
            {d.start_node for d in drivers}
            | {o.pickup_node for o in orders}
            | {o.dropoff_node for o in orders}
        )

        # Build distance matrix using Dijkstra
        dm = DistanceMatrix(relevant_nodes, self.graph)

        # Solve PDP using the same canonical mode contract as benchmark API.
        from backend.pdp.mode_solver import solve_mode
        if algorithm == "scratch":
            solution, _ = solve_mode(orders, drivers, dm, mode=mode, economics=economics,
                                     timing=timing, time_limit_seconds=time_limit_seconds)
        # Solve PDP
        elif algorithm == "ortools":
            solution = ortools_solve(orders, drivers, dm, time_limit_seconds, mode=mode,
                                     economics=economics, timing=timing)
        elif algorithm == "pyvrp":
            solution = pyvrp_solve(orders, drivers, dm, time_limit_seconds, mode=mode,
                                   economics=economics, timing=timing)
        elif algorithm == "learned":
            from backend.ml.policy import solve as learned_solve
            solution = learned_solve(orders, drivers, dm, mode=mode, economics=economics,
                                     timing=timing, time_limit_seconds=time_limit_seconds)
        from backend.pdp.validation import validate
        audit = validate(solution, orders, drivers, dm, mode=mode, economics=economics,
            timing=timing, metres_per_unit=1000.0)

        # Expand stop sequences into turn-by-turn road paths
        detailed_routes = []
        driver_by_id = {d.driver_id: d for d in drivers}

        for driver_id, route in solution.routes.items():
            driver = driver_by_id[driver_id]
            full_path = []
            segment_details = []

            current_node = driver.start_node
            full_path.append(current_node)

            for stop in route.stops:
                target_node = stop.node
                if current_node != target_node:
                    seg_path, seg_dist = dijkstra_v2(self.graph, current_node, target_node)
                    if seg_path:
                        # Append path excluding duplicate current_node
                        full_path.extend(seg_path[1:])
                        segment_details.append({
                            "from": current_node,
                            "to": target_node,
                            "order_id": stop.order_id,
                            "stop_type": stop.stop_type.value,
                            "distance": round(seg_dist, 2),
                            "path": seg_path
                        })
                current_node = target_node

            detailed_routes.append({
                "driver_id": driver_id,
                "start_node": driver.start_node,
                "capacity": driver.capacity,
                "total_distance": round(route.total_distance, 2),
                "stops": [
                    {
                        "order_id": s.order_id,
                        "node": s.node,
                        "type": s.stop_type.value
                    }
                    for s in route.stops
                ],
                "full_path": full_path,
                "segment_details": segment_details
            })

        return {
            "algorithm": algorithm,
            "mode": mode,
            "status": "feasible" if audit["complete"] and audit["valid"] else ("infeasible" if mode == "time" and len(drivers) > len(orders) else "no_solution" if not audit["metrics"]["served_orders"] else "partial"),
            "objective_value": audit["objective_value"],
            "metrics": audit["metrics"],
            "validation": {"valid": audit["valid"], "complete": audit["complete"], "errors": audit["errors"]},
            "solver_metadata": solution.metadata,
            "total_distance": round(solution.total_distance, 2),
            "unassigned_orders": solution.unassigned_orders,
            "routes": detailed_routes,
            "positions": self.positions
        }
