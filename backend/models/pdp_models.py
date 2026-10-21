from pydantic import BaseModel, Field


class PDPDriverRequest(BaseModel):
    driver_id: int = Field(..., ge=1)
    start_node: str = Field(..., min_length=1)
    capacity: int = Field(5, ge=1)


class PDPOrderRequest(BaseModel):
    order_id: int = Field(..., ge=1)
    pickup_node: str = Field(..., min_length=1)
    dropoff_node: str = Field(..., min_length=1)
    demand: int = Field(1, ge=1)


class PDPRequest(BaseModel):
    graph_type: str = Field("medium", pattern="^(small|medium)$")
    algorithm: str = Field("scratch", pattern="^(scratch|ortools|pyvrp|learned)$")
    time_limit_seconds: float = Field(5, ge=1, le=10, allow_inf_nan=False)
    mode: str = Field("save", pattern="^(save|time)$")
    activation_cost: float = Field(20, ge=0, allow_inf_nan=False)
    cost_per_km: float = Field(.5, ge=0, allow_inf_nan=False)
    speed_kph: float = Field(30, gt=0, allow_inf_nan=False)
    service_minutes_per_stop: float = Field(1, ge=0, allow_inf_nan=False)
    drivers: list[PDPDriverRequest] = Field(..., min_length=1)
    orders: list[PDPOrderRequest] = Field(default_factory=list)
