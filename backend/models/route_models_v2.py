from pydantic import BaseModel, Field


class RouteV2Request(BaseModel):
    start: str = Field(..., json_schema_extra={"example": "A"})
    destination: str = Field(..., json_schema_extra={"example": "F"})


class RouteAStarRequest(BaseModel):
    start: str = Field(..., json_schema_extra={"example": "A"})
    destination: str = Field(..., json_schema_extra={"example": "F"})
