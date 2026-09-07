from pydantic import BaseModel, Field
from typing import Optional


class RouteV2Request(BaseModel):
    start: str = Field(..., json_schema_extra={"example": "A"})
    destination: str = Field(..., json_schema_extra={"example": "F"})
    graph_type: Optional[str] = Field("small", json_schema_extra={"example": "small"})


class RouteAStarRequest(BaseModel):
    start: str = Field(..., json_schema_extra={"example": "A"})
    destination: str = Field(..., json_schema_extra={"example": "F"})
    graph_type: Optional[str] = Field("small", json_schema_extra={"example": "small"})
