from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.prices import PriceComparison, PriceLatestResponse
from app.services.price_service import PriceService

router = APIRouter()


@router.get("/prices/latest", response_model=PriceLatestResponse)
def get_latest_prices(
    item_name: str | None = Query(default=None), db: Session = Depends(get_db)
) -> PriceLatestResponse:
    return PriceLatestResponse(**PriceService(db).get_latest_price(item_name=item_name))


@router.get("/prices/compare", response_model=PriceComparison)
def compare_price(
    item_name: str = Query(min_length=2), db: Session = Depends(get_db)
) -> PriceComparison:
    return PriceComparison(**PriceService(db).compare_price(item_name=item_name))
