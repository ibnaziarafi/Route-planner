from pydantic import BaseModel, Field


class RealMapPDPDriver(BaseModel):
    driver_id: int = Field(..., ge=1)
    start_lat: float = Field(..., ge=-90, le=90)
    start_lon: float = Field(..., ge=-180, le=180)
    capacity: int = Field(..., ge=1)


class RealMapPDPOrder(BaseModel):
    order_id: int = Field(..., ge=1)
    pickup_lat: float = Field(..., ge=-90, le=90)
    pickup_lon: float = Field(..., ge=-180, le=180)
    dropoff_lat: float = Field(..., ge=-90, le=90)
    dropoff_lon: float = Field(..., ge=-180, le=180)
    demand: int = Field(1, ge=1)


class RealMapPDPRequest(BaseModel):
    drivers: list[RealMapPDPDriver] = Field(..., min_length=1)
    orders: list[RealMapPDPOrder] = Field(default_factory=list)
    algorithm: str = Field("dijkstra_v2", pattern="^(dijkstra|dijkstra_v2|a_star)$")
    solver: str = Field("scratch", pattern="^(scratch|ortools|pyvrp)$")
    time_limit_seconds: int = Field(5, ge=1, le=60)


class RealMapPDPStop(BaseModel):
    order_id: int
    node: str
    type: str
    lat: float
    lon: float


class RealMapPDPRoute(BaseModel):
    driver_id: int
    capacity: int
    total_distance_km: float
    stops: list[RealMapPDPStop]
    full_path: list[dict]


class RealMapPDPResponse(BaseModel):
    algorithm: str
    solver: str
    total_distance_km: float
    routes: list[RealMapPDPRoute]
    unassigned_orders: list[int]
    positions: dict[str, dict[str, float]]
