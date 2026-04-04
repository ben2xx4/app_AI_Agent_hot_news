from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/chat/query", response_model=ChatQueryResponse)
def chat_query(payload: ChatQueryRequest, db: Session = Depends(get_db)) -> ChatQueryResponse:
    return ChatQueryResponse(**ChatService(db).answer_question(payload.question))
