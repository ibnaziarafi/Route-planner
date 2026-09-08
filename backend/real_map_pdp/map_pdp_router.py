from fastapi import APIRouter, HTTPException

from backend.real_map_pdp.real_map_pdp_service import solve_real_map_pdp
from backend.real_map_pdp.schemas import RealMapPDPRequest, RealMapPDPResponse

router = APIRouter(prefix="/api/real-map-pdp", tags=["real-map-pdp"])


@router.post("/solve", response_model=RealMapPDPResponse)
def solve_real_map_pdp_route(request: RealMapPDPRequest):
    try:
        return solve_real_map_pdp(request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
