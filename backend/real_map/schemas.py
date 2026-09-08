from pydantic import BaseModel, Field


class RealMapRouteRequest(BaseModel):
    start_lat: float = Field(..., ge=-90, le=90)
    start_lon: float = Field(..., ge=-180, le=180)
    end_lat: float = Field(..., ge=-90, le=90)
    end_lon: float = Field(..., ge=-180, le=180)
    algorithm: str = Field("dijkstra_v2", pattern="^(dijkstra|dijkstra_v2|a_star)$")


class RouteCoordinate(BaseModel):
    node: str
    lat: float
    lon: float


class RealMapRouteResponse(BaseModel):
    algorithm: str
    distance: float
    start_node: str
    end_node: str
    path: list[RouteCoordinate]
