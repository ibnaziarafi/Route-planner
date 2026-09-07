from pydantic import BaseModel, Field
from typing import Optional


class RouteRequest(BaseModel):
    start: str = Field(..., json_schema_extra={"example": "A"})
    destination: str = Field(..., json_schema_extra={"example": "F"})
    graph_type: Optional[str] = Field("small", json_schema_extra={"example": "small"})


class MultiStopRouteRequest(BaseModel):
    start: str = Field(..., json_schema_extra={"example": "A"})
    stops: list[str] = Field(default_factory=list, json_schema_extra={"example": ["D", "C"]})
    destination: str = Field(..., json_schema_extra={"example": "F"})
    graph_type: Optional[str] = Field("small", json_schema_extra={"example": "small"})


class RouteResponse(BaseModel):
    path: Optional[list[str]] = None
    route: Optional[list[str]] = None
    distance: float
    error: Optional[str] = None


class EdgeModel(BaseModel):
    u: str
    v: str
    weight: float


class PositionModel(BaseModel):
    x: int
    y: int


class GraphResponse(BaseModel):
    nodes: list[str]
    edges: list[EdgeModel]
    positions: dict[str, PositionModel]
