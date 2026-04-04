from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.weather import WeatherResponse
from app.services.weather_service import WeatherService

router = APIRouter()


@router.get("/weather/latest", response_model=WeatherResponse)
def get_latest_weather(
    location: str = Query(min_length=2), db: Session = Depends(get_db)
) -> WeatherResponse:
    payload = WeatherService(db).get_weather(location=location)
    if not payload:
        raise HTTPException(status_code=404, detail="Khong tim thay du lieu thoi tiet")
    return WeatherResponse(**payload)
