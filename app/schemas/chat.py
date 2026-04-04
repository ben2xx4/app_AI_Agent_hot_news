from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel


class ChatQueryRequest(APIModel):
    question: str = Field(min_length=3)


class ChatQueryResponse(APIModel):
    question: str
    intent: str
    tool_called: str
    answer: str
    sources: list[str]
    updated_at: datetime | None = None
    data: dict | None = None
