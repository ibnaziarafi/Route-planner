from pydantic import BaseModel, Field


class RealMapEconomics(BaseModel):
    activation_cost: float = Field(default=20, ge=0, allow_inf_nan=False)
    cost_per_km: float = Field(default=.5, ge=0, allow_inf_nan=False)


class RealMapTiming(BaseModel):
    speed_kph: float = Field(default=30, gt=0, allow_inf_nan=False)
    service_minutes_per_stop: float = Field(default=1, ge=0, allow_inf_nan=False)


class RealMapPDPDriver(BaseModel):
    driver_id: int = Field(..., ge=1)
    start_lat: float = Field(..., ge=-90, le=90, allow_inf_nan=False)
    start_lon: float = Field(..., ge=-180, le=180, allow_inf_nan=False)
    capacity: int = Field(..., ge=1)


class RealMapPDPOrder(BaseModel):
    order_id: int = Field(..., ge=1)
    pickup_lat: float = Field(..., ge=-90, le=90, allow_inf_nan=False)
    pickup_lon: float = Field(..., ge=-180, le=180, allow_inf_nan=False)
    dropoff_lat: float = Field(..., ge=-90, le=90, allow_inf_nan=False)
    dropoff_lon: float = Field(..., ge=-180, le=180, allow_inf_nan=False)
    demand: int = Field(1, ge=1)


class RealMapPDPRequest(BaseModel):
    drivers: list[RealMapPDPDriver] = Field(..., min_length=1, max_length=8)
    orders: list[RealMapPDPOrder] = Field(default_factory=list, max_length=20)
    algorithm: str = Field("dijkstra_v2", pattern="^(dijkstra|dijkstra_v2|a_star)$")
    solver: str = Field("scratch", pattern="^(scratch|ortools|pyvrp|learned)$")
    time_limit_seconds: float = Field(5, ge=1, le=10, allow_inf_nan=False)
    mode: str = Field("save", pattern="^(save|time)$")
    economics: RealMapEconomics = Field(default_factory=RealMapEconomics)
    timing: RealMapTiming = Field(default_factory=RealMapTiming)


class RealMapPDPStop(BaseModel):
    order_id: int
    node: str
    type: str
    lat: float
    lon: float
    distance_km: float


class RealMapPDPRoute(BaseModel):
    driver_id: int
    capacity: int
    total_distance_km: float
    stops: list[RealMapPDPStop]
    full_path: list[dict]


class RealMapPDPResponse(BaseModel):
    algorithm: str
    solver: str
    mode: str = "save"
    status: str = "feasible"
    objective_value: float | None = None
    metrics: dict = Field(default_factory=dict)
    validation: dict = Field(default_factory=dict)
    assumptions: dict = Field(default_factory=dict)
    total_distance_km: float
    routes: list[RealMapPDPRoute]
    unassigned_orders: list[int]
    positions: dict[str, dict[str, float]]
