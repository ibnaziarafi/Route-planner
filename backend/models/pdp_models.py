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
    drivers: list[PDPDriverRequest] = Field(..., min_length=1)
    orders: list[PDPOrderRequest] = Field(default_factory=list)