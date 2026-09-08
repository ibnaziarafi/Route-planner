from fastapi import APIRouter, HTTPException

from backend.real_map.schemas import RealMapRouteRequest, RealMapRouteResponse
from backend.real_map.service import calculate_real_map_route

router = APIRouter(prefix="/api/real-map", tags=["real-map"])


@router.post("/route", response_model=RealMapRouteResponse)
def route_real_map(request: RealMapRouteRequest):
    try:
        return calculate_real_map_route(request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
