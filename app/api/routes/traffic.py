from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.traffic import TrafficListResponse
from app.services.traffic_service import TrafficService

router = APIRouter()


@router.get("/traffic/latest", response_model=TrafficListResponse)
def get_latest_traffic(
    location: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
) -> TrafficListResponse:
    return TrafficListResponse(
        **TrafficService(db).get_traffic_updates(location=location, limit=limit)
    )
