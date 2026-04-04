from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.policies import PolicyListResponse
from app.services.policy_service import PolicyService

router = APIRouter()


@router.get("/policies/search", response_model=PolicyListResponse)
def search_policies(
    query: str | None = Query(default=None),
    field: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
) -> PolicyListResponse:
    return PolicyListResponse(
        **PolicyService(db).search_policy(query=query, field=field, limit=limit)
    )
