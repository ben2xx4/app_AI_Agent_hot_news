from fastapi import APIRouter

from app.db.session import get_engine
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    engine = get_engine()
    return HealthResponse(
        status="ok",
        database_url=engine.url.render_as_string(hide_password=False),
        database_driver=engine.url.drivername,
    )
