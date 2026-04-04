from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.news import NewsListResponse
from app.services.news_service import NewsService

router = APIRouter()


@router.get("/news/hot", response_model=NewsListResponse)
def get_hot_news(
    limit: int = Query(default=10, ge=1, le=20), db: Session = Depends(get_db)
) -> NewsListResponse:
    return NewsListResponse(**NewsService(db).get_hot_news(limit=limit))


@router.get("/news/search", response_model=NewsListResponse)
def search_news(
    q: str = Query(min_length=2),
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
) -> NewsListResponse:
    return NewsListResponse(**NewsService(db).search_news(query=q, limit=limit))
