from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models.route_models import (
    RouteRequest,
    MultiStopRouteRequest,
    RouteResponse,
    GraphResponse,
)
from backend.services.route_service import RouteService

app = FastAPI(
    title="Route Planner API - Phase 1",
    description="Custom DSA Route Planner using Graph, Dijkstra, and Doubly Linked List",
    version="1.0.0",
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

@app.get("/graph", response_model=GraphResponse)
def get_graph():
    """Returns all graph nodes, weighted edges, and layout coordinates."""
    return route_service.get_graph_data()

@app.post("/route", response_model=RouteResponse)
def find_route(request: RouteRequest):
    """Calculates the shortest single route between start and destination."""
    if not request.start or not request.destination:
        raise HTTPException(status_code=400, detail="Start and destination are required.")
    
    result = route_service.calculate_single_route(request.start, request.destination)
    if result["distance"] == float('inf'):
        raise HTTPException(status_code=404, detail="No route found between the specified points.")
    
    return result

@app.post("/route/multi-stop", response_model=RouteResponse)
def find_multi_stop_route(request: MultiStopRouteRequest):
    """Calculates a multi-stop route combining Dijkstra segments into a Linked List."""
    if not request.start or not request.destination:
        raise HTTPException(status_code=400, detail="Start and destination are required.")
    
    result = route_service.calculate_multi_stop_route(
        request.start, request.stops, request.destination
    )
    if result["distance"] == float('inf'):
        raise HTTPException(
            status_code=404, detail=result.get("error", "No route found covering all specified stops.")
        )
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
