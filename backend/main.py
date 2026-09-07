from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.models.route_models import (
    RouteRequest,
    MultiStopRouteRequest,
    RouteResponse,
    GraphResponse,
)
from backend.models.route_models_v2 import (
    RouteV2Request,
    RouteAStarRequest,
)
from backend.models.pdp_models import PDPRequest
from backend.pdp.models import Driver, Order
from backend.pdp.pdp_service import PDPService
from backend.graph.graph_data import get_graph_and_positions
from backend.services.route_service import RouteService
from backend.services.route_service_v2 import RouteServiceV2

app = FastAPI(
    title="Route Planner API - Phase 2",
    description="Custom DSA Route Planner using Graph, Dijkstra V1/V2, MinHeap, and A*",
    version="2.0.0",
)

# CORS configuration for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

route_service = RouteService()
route_service_v2 = RouteServiceV2()

@app.get("/graph", response_model=GraphResponse)
def get_graph(graph_type: str = Query("small", description="Size of graph: 'small' (6 nodes) or 'medium' (20 nodes)")):
    """Returns all graph nodes, weighted edges, and layout coordinates for specified graph size."""
    return route_service.get_graph_data(graph_type=graph_type)

@app.post("/route", response_model=RouteResponse)
def find_route(request: RouteRequest):
    """Calculates the shortest single route between start and destination using Phase 1 Dijkstra V1."""
    if not request.start or not request.destination:
        raise HTTPException(status_code=400, detail="Start and destination are required.")
    
    graph_type = request.graph_type or "small"
    result = route_service.calculate_single_route(request.start, request.destination, graph_type=graph_type)
    if result["distance"] == float('inf'):
        raise HTTPException(status_code=404, detail="No route found between the specified points.")
    
    return result

@app.post("/route/multi-stop", response_model=RouteResponse)
def find_multi_stop_route(request: MultiStopRouteRequest):
    """Calculates a multi-stop route combining Dijkstra segments into a Linked List."""
    if not request.start or not request.destination:
        raise HTTPException(status_code=400, detail="Start and destination are required.")
    
    graph_type = request.graph_type or "small"
    result = route_service.calculate_multi_stop_route(
        request.start, request.stops, request.destination, graph_type=graph_type
    )
    if result["distance"] == float('inf'):
        raise HTTPException(
            status_code=404, detail=result.get("error", "No route found covering all specified stops.")
        )
    
    return result

@app.post("/route/v2", response_model=RouteResponse)
def find_route_v2(request: RouteV2Request):
    """Calculates the shortest route using Phase 2 Dijkstra V2 (MinHeap)."""
    if not request.start or not request.destination:
        raise HTTPException(status_code=400, detail="Start and destination are required.")

    graph_type = request.graph_type or "small"
    result = route_service_v2.calculate_single_route_v2(request.start, request.destination, graph_type=graph_type)
    if result["distance"] == float('inf'):
        raise HTTPException(status_code=404, detail="No route found between the specified points.")

    return result

@app.post("/route/astar", response_model=RouteResponse)
def find_route_astar(request: RouteAStarRequest):
    """Calculates the shortest route using Phase 2 A* Pathfinding."""
    if not request.start or not request.destination:
        raise HTTPException(status_code=400, detail="Start and destination are required.")

    graph_type = request.graph_type or "small"
    result = route_service_v2.calculate_single_route_astar(request.start, request.destination, graph_type=graph_type)
    if result["distance"] == float('inf'):
        raise HTTPException(status_code=404, detail="No route found between the specified points.")

    return result


@app.post("/pdp/solve")
def solve_pdp(request: PDPRequest):
    """Assigns parcel pickups and drop-offs to drivers and expands their routes."""
    graph, _ = get_graph_and_positions(request.graph_type)
    graph_nodes = set(graph.adj.keys())
    requested_nodes = {
        driver.start_node for driver in request.drivers
    } | {
        node
        for order in request.orders
        for node in (order.pickup_node, order.dropoff_node)
    }
    unknown_nodes = sorted(requested_nodes - graph_nodes)
    if unknown_nodes:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown graph nodes: {', '.join(unknown_nodes)}",
        )

    driver_ids = [driver.driver_id for driver in request.drivers]
    order_ids = [order.order_id for order in request.orders]
    if len(driver_ids) != len(set(driver_ids)):
        raise HTTPException(status_code=400, detail="Driver IDs must be unique.")
    if len(order_ids) != len(set(order_ids)):
        raise HTTPException(status_code=400, detail="Order IDs must be unique.")

    service = PDPService(request.graph_type)
    drivers = [Driver(**driver.model_dump()) for driver in request.drivers]
    orders = [Order(**order.model_dump()) for order in request.orders]
    return service.solve_pdp(drivers, orders)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
